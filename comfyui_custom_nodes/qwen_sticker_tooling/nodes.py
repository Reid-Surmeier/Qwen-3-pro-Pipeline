"""ComfyUI nodes for mask-owned sticker Assembly and Fidelity Checks.

This pack is deliberately independent of the provider and router packages.  It
operates only on image and mask tensors after a Render Pass has completed.
"""

from __future__ import annotations

import json
from typing import Any


def _mask_batch(masks: Any):
    if masks.ndim == 2:
        masks = masks.unsqueeze(0)
    if masks.ndim != 3:
        raise ValueError("Masks must have shape [batch,height,width]")
    return masks.to(dtype=masks.dtype).clamp(0.0, 1.0)


def _expand_batch(tensor: Any, batch_size: int):
    if tensor.shape[0] == batch_size:
        return tensor
    if tensor.shape[0] == 1:
        return tensor.expand(batch_size, *tensor.shape[1:])
    raise ValueError(
        f"Batch size {tensor.shape[0]} cannot be matched to batch size {batch_size}"
    )


def _dilate(mask: Any, pixels: int):
    import torch.nn.functional as functional

    if pixels <= 0:
        return mask
    kernel = (pixels * 2) + 1
    return functional.max_pool2d(
        mask.unsqueeze(1), kernel_size=kernel, stride=1, padding=pixels
    ).squeeze(1)


def _erode(mask: Any, pixels: int):
    if pixels <= 0:
        return mask
    return 1.0 - _dilate(1.0 - mask, pixels)


def _parse_quad(value: str, width: int, height: int):
    import torch

    try:
        numbers = [float(item.strip()) for item in value.split(",")]
    except (TypeError, ValueError) as error:
        raise ValueError("Target quad must be x1,y1,x2,y2,x3,y3,x4,y4") from error
    if len(numbers) != 8:
        raise ValueError("Target quad must contain exactly eight coordinates")
    points = torch.tensor(numbers, dtype=torch.float64).reshape(4, 2)
    if (
        (points[:, 0] < 0).any()
        or (points[:, 0] > width - 1).any()
        or (points[:, 1] < 0).any()
        or (points[:, 1] > height - 1).any()
    ):
        raise ValueError("Target quad must stay inside the output canvas")
    x = points[:, 0]
    y = points[:, 1]
    area = 0.5 * abs(
        float(
            (x * torch.roll(y, shifts=-1) - y * torch.roll(x, shifts=-1))
            .sum()
            .item()
        )
    )
    if area < 1.0:
        raise ValueError("Target quad must have a non-zero area")
    return points


def _projective_grid(
    *,
    source_width: int,
    source_height: int,
    canvas_width: int,
    canvas_height: int,
    target_quad: str,
    device: Any,
    dtype: Any,
):
    """Return a grid mapping destination pixels back to source pixels."""

    import torch

    destination = _parse_quad(target_quad, canvas_width, canvas_height)
    source = torch.tensor(
        [
            [0.0, 0.0],
            [source_width - 1.0, 0.0],
            [source_width - 1.0, source_height - 1.0],
            [0.0, source_height - 1.0],
        ],
        dtype=torch.float64,
    )
    rows = []
    values = []
    for (x, y), (u, v) in zip(destination.tolist(), source.tolist(), strict=True):
        rows.append([x, y, 1.0, 0.0, 0.0, 0.0, -u * x, -u * y])
        values.append(u)
        rows.append([0.0, 0.0, 0.0, x, y, 1.0, -v * x, -v * y])
        values.append(v)
    matrix = torch.tensor(rows, dtype=torch.float64)
    vector = torch.tensor(values, dtype=torch.float64)
    try:
        solution = torch.linalg.solve(matrix, vector)
    except RuntimeError as error:
        raise ValueError("Target quad does not define a stable perspective warp") from error
    homography = torch.cat([solution, torch.ones(1, dtype=torch.float64)]).reshape(3, 3)

    yy, xx = torch.meshgrid(
        torch.arange(canvas_height, dtype=torch.float64),
        torch.arange(canvas_width, dtype=torch.float64),
        indexing="ij",
    )
    ones = torch.ones_like(xx)
    destination_pixels = torch.stack([xx, yy, ones], dim=-1)
    mapped = destination_pixels @ homography.T
    denominator = mapped[..., 2]
    epsilon = torch.full_like(denominator, 1e-9)
    denominator = torch.where(
        denominator.abs() < epsilon,
        torch.where(denominator < 0, -epsilon, epsilon),
        denominator,
    )
    source_x = mapped[..., 0] / denominator
    source_y = mapped[..., 1] / denominator
    if source_width == 1:
        normalized_x = torch.zeros_like(source_x)
    else:
        normalized_x = (source_x * 2.0 / (source_width - 1.0)) - 1.0
    if source_height == 1:
        normalized_y = torch.zeros_like(source_y)
    else:
        normalized_y = (source_y * 2.0 / (source_height - 1.0)) - 1.0
    return torch.stack([normalized_x, normalized_y], dim=-1).to(
        device=device, dtype=dtype
    )


def _byte_images(images: Any):
    import torch

    return (images * 255.0).round().clamp(0, 255).to(torch.uint8)


def _centroid_and_scale(mask: Any):
    import torch

    points = torch.nonzero(mask, as_tuple=False)
    if points.numel() == 0:
        return None, 0.0
    centroid = points.to(torch.float32).mean(dim=0)
    return centroid, float(points.shape[0])


def _masked_ssim(reference: Any, candidate: Any, mask: Any) -> float:
    import torch

    pixels = mask.unsqueeze(-1).expand_as(reference)
    if not bool(pixels.any()):
        return 1.0
    left = reference[pixels].to(torch.float32) / 255.0
    right = candidate[pixels].to(torch.float32) / 255.0
    mean_left = left.mean()
    mean_right = right.mean()
    variance_left = left.var(unbiased=False)
    variance_right = right.var(unbiased=False)
    covariance = ((left - mean_left) * (right - mean_right)).mean()
    c1 = 0.01**2
    c2 = 0.03**2
    score = ((2 * mean_left * mean_right + c1) * (2 * covariance + c2)) / (
        (mean_left.square() + mean_right.square() + c1)
        * (variance_left + variance_right + c2)
    )
    return float(torch.clamp(score, -1.0, 1.0).item())


def _edge_map(image: Any, mask: Any):
    import torch
    import torch.nn.functional as functional

    grayscale = image.to(torch.float32).mean(dim=-1, keepdim=True).permute(2, 0, 1)
    kernel_x = torch.tensor(
        [[-1.0, 0.0, 1.0], [-2.0, 0.0, 2.0], [-1.0, 0.0, 1.0]],
        device=image.device,
    ).reshape(1, 1, 3, 3)
    kernel_y = kernel_x.transpose(-1, -2)
    gx = functional.conv2d(grayscale.unsqueeze(0), kernel_x, padding=1)
    gy = functional.conv2d(grayscale.unsqueeze(0), kernel_y, padding=1)
    magnitude = torch.sqrt(gx.square() + gy.square()).squeeze(0).squeeze(0)
    return magnitude.gt(48.0) & mask


class StickerMaskBands:
    """Split one approved silhouette into explicit pixel-ownership bands."""

    CATEGORY = "Qwen UI Pipeline/Sticker Tooling"
    FUNCTION = "build"
    RETURN_TYPES = ("MASK", "MASK", "MASK", "MASK", "MASK")
    RETURN_NAMES = (
        "artwork_interior",
        "white_cutline",
        "contact_band",
        "editable_union",
        "immutable_outside",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "sticker_masks": ("MASK",),
                "threshold": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "artwork_inset": (
                    "INT",
                    {"default": 0, "min": 0, "max": 64, "step": 1},
                ),
                "cutline_width": (
                    "INT",
                    {"default": 3, "min": 0, "max": 256, "step": 1},
                ),
                "contact_width": (
                    "INT",
                    {"default": 2, "min": 0, "max": 256, "step": 1},
                ),
            }
        }

    def build(
        self,
        sticker_masks,
        threshold: float,
        artwork_inset: int,
        cutline_width: int,
        contact_width: int,
    ):
        base = (_mask_batch(sticker_masks) >= threshold).to(sticker_masks.dtype)
        artwork = _erode(base, artwork_inset)
        silhouette = _dilate(base, cutline_width)
        contact_limit = _dilate(silhouette, contact_width)
        cutline = (silhouette - artwork).clamp(0.0, 1.0)
        contact = (contact_limit - silhouette).clamp(0.0, 1.0)
        editable = (artwork + cutline + contact).clamp(0.0, 1.0)
        immutable = 1.0 - editable
        return artwork, cutline, contact, editable, immutable


class StickerPerspectiveWarp:
    """Project an artwork image and its mask onto the same four-corner surface."""

    CATEGORY = "Qwen UI Pipeline/Sticker Tooling"
    FUNCTION = "warp"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("warped_artwork", "warped_mask")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "artwork_images": ("IMAGE",),
                "sticker_masks": ("MASK",),
                "canvas_width": (
                    "INT",
                    {"default": 1024, "min": 1, "max": 16384, "step": 1},
                ),
                "canvas_height": (
                    "INT",
                    {"default": 1024, "min": 1, "max": 16384, "step": 1},
                ),
                "target_quad": (
                    "STRING",
                    {
                        "default": "0,0,1023,0,1023,1023,0,1023",
                        "multiline": False,
                    },
                ),
            }
        }

    def warp(
        self,
        artwork_images,
        sticker_masks,
        canvas_width: int,
        canvas_height: int,
        target_quad: str,
    ):
        import torch.nn.functional as functional

        if artwork_images.ndim != 4 or artwork_images.shape[-1] not in (3, 4):
            raise ValueError(
                "Artwork images must have shape [batch,height,width,channels]"
            )
        masks = _mask_batch(sticker_masks)
        batch_size = max(artwork_images.shape[0], masks.shape[0])
        images = _expand_batch(artwork_images, batch_size)
        masks = _expand_batch(masks, batch_size)
        source_height, source_width = images.shape[1:3]
        if masks.shape[1:3] != (source_height, source_width):
            raise ValueError("Artwork image and sticker mask dimensions must match")
        grid = _projective_grid(
            source_width=source_width,
            source_height=source_height,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            target_quad=target_quad,
            device=images.device,
            dtype=images.dtype,
        ).unsqueeze(0).expand(batch_size, -1, -1, -1)
        warped_images = functional.grid_sample(
            images.movedim(-1, 1),
            grid,
            mode="bilinear",
            padding_mode="zeros",
            align_corners=True,
        ).movedim(1, -1)
        warped_masks = functional.grid_sample(
            masks.unsqueeze(1),
            grid,
            mode="bilinear",
            padding_mode="zeros",
            align_corners=True,
        ).squeeze(1).clamp(0.0, 1.0)
        warped_images = warped_images * warped_masks.unsqueeze(-1)
        return warped_images, warped_masks


class MaskedReferenceFidelityGate:
    """Fail closed when any source pixel outside an approved mask drifts."""

    CATEGORY = "Qwen UI Pipeline/Sticker Tooling"
    FUNCTION = "check"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "fidelity_report")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "reference_images": ("IMAGE",),
                "candidate_images": ("IMAGE",),
                "allowed_masks": ("MASK",),
                "mask_threshold": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "exact_outside_mask": ("BOOLEAN", {"default": True}),
                "max_global_normalized_rmse": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.001},
                ),
                "min_inside_changed_pixels": (
                    "INT",
                    {"default": 1, "min": 0, "max": 2147483647},
                ),
            }
        }

    def check(
        self,
        reference_images,
        candidate_images,
        allowed_masks,
        mask_threshold: float,
        exact_outside_mask: bool,
        max_global_normalized_rmse: float,
        min_inside_changed_pixels: int,
    ):
        import torch

        reference = _byte_images(reference_images[:1])
        candidates = _byte_images(candidate_images)
        if reference.shape[1:] != candidates.shape[1:]:
            raise RuntimeError(
                "Masked Fidelity Check failed: exact_size; "
                f"reference={list(reference.shape[1:3])} "
                f"candidate={list(candidates.shape[1:3])}"
            )
        masks = _mask_batch(allowed_masks)
        if masks.shape[1:3] != candidates.shape[1:3]:
            raise RuntimeError("Masked Fidelity Check failed: mask_size")
        masks = _expand_batch(masks, candidates.shape[0]).ge(mask_threshold)
        expanded_reference = reference.expand(candidates.shape[0], -1, -1, -1)
        delta = (candidates.to(torch.int16) - expanded_reference.to(torch.int16)).abs()
        changed = delta.ne(0).any(dim=-1)
        outside = changed & ~masks
        inside = changed & masks
        rmse = torch.sqrt(delta.to(torch.float32).square().mean(dim=(1, 2, 3))) / 255

        reports = []
        failures: set[str] = set()
        for index in range(candidates.shape[0]):
            outside_changed = int(outside[index].sum().item())
            inside_changed = int(inside[index].sum().item())
            normalized_rmse = float(rmse[index].item())
            failed = []
            if exact_outside_mask and outside_changed:
                failed.append("exact_outside_mask")
            if normalized_rmse > max_global_normalized_rmse:
                failed.append("max_global_normalized_rmse")
            if inside_changed < min_inside_changed_pixels:
                failed.append("min_inside_changed_pixels")
            failures.update(failed)
            reports.append(
                {
                    "candidate_index": index,
                    "passed": not failed,
                    "failed_checks": failed,
                    "global_normalized_rmse": normalized_rmse,
                    "inside_mask_changed_pixels": inside_changed,
                    "outside_mask_changed_pixels": outside_changed,
                    "allowed_mask_pixels": int(masks[index].sum().item()),
                }
            )
        rendered = json.dumps(
            {"schema_version": 1, "ownership": "mask", "candidates": reports},
            sort_keys=True,
        )
        if failures:
            raise RuntimeError(
                "Masked Fidelity Check failed: "
                + ", ".join(sorted(failures))
                + "; "
                + rendered
            )
        return candidate_images, rendered


class ArtworkFidelityGate:
    """Compare approved artwork and silhouette inside their owned pixels."""

    CATEGORY = "Qwen UI Pipeline/Sticker Tooling"
    FUNCTION = "check"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "artwork_report")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "approved_images": ("IMAGE",),
                "candidate_images": ("IMAGE",),
                "approved_masks": ("MASK",),
                "candidate_masks": ("MASK",),
                "mask_threshold": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "exact_artwork": ("BOOLEAN", {"default": True}),
                "max_masked_normalized_rmse": (
                    "FLOAT",
                    {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.001},
                ),
                "min_masked_ssim": (
                    "FLOAT",
                    {"default": 0.999, "min": -1.0, "max": 1.0, "step": 0.001},
                ),
                "min_edge_iou": (
                    "FLOAT",
                    {"default": 0.99, "min": 0.0, "max": 1.0, "step": 0.001},
                ),
                "min_silhouette_iou": (
                    "FLOAT",
                    {"default": 0.999, "min": 0.0, "max": 1.0, "step": 0.001},
                ),
                "max_centroid_drift_px": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 16384.0, "step": 0.1},
                ),
                "max_scale_drift": (
                    "FLOAT",
                    {"default": 0.001, "min": 0.0, "max": 1.0, "step": 0.001},
                ),
            }
        }

    def check(
        self,
        approved_images,
        candidate_images,
        approved_masks,
        candidate_masks,
        mask_threshold: float,
        exact_artwork: bool,
        max_masked_normalized_rmse: float,
        min_masked_ssim: float,
        min_edge_iou: float,
        min_silhouette_iou: float,
        max_centroid_drift_px: float,
        max_scale_drift: float,
    ):
        import torch

        approved = _byte_images(approved_images[:1])
        candidates = _byte_images(candidate_images)
        if approved.shape[1:] != candidates.shape[1:]:
            raise RuntimeError("Artwork Fidelity Check failed: exact_size")
        approved_mask = _mask_batch(approved_masks[:1]).ge(mask_threshold)
        candidate_mask = _mask_batch(candidate_masks).ge(mask_threshold)
        if (
            approved_mask.shape[1:3] != candidates.shape[1:3]
            or candidate_mask.shape[1:3] != candidates.shape[1:3]
        ):
            raise RuntimeError("Artwork Fidelity Check failed: mask_size")
        approved = approved.expand(candidates.shape[0], -1, -1, -1)
        approved_mask = approved_mask.expand(candidates.shape[0], -1, -1)
        candidate_mask = _expand_batch(candidate_mask, candidates.shape[0])

        reports = []
        failures: set[str] = set()
        for index in range(candidates.shape[0]):
            left_mask = approved_mask[index]
            right_mask = candidate_mask[index]
            intersection = left_mask & right_mask
            union = left_mask | right_mask
            union_count = int(union.sum().item())
            intersection_count = int(intersection.sum().item())
            silhouette_iou = intersection_count / union_count if union_count else 1.0

            delta = (
                candidates[index].to(torch.int16) - approved[index].to(torch.int16)
            ).abs()
            changed_pixels = delta.ne(0).any(dim=-1) & intersection
            if intersection_count:
                values = delta.to(torch.float32)[intersection]
                masked_rmse = float(torch.sqrt(values.square().mean()).item() / 255.0)
            else:
                masked_rmse = 0.0
            masked_ssim = _masked_ssim(
                approved[index], candidates[index], intersection
            )
            left_edges = _edge_map(approved[index], left_mask)
            right_edges = _edge_map(candidates[index], right_mask)
            edge_union = left_edges | right_edges
            edge_iou = (
                float((left_edges & right_edges).sum().item())
                / float(edge_union.sum().item())
                if bool(edge_union.any())
                else 1.0
            )
            left_centroid, left_scale = _centroid_and_scale(left_mask)
            right_centroid, right_scale = _centroid_and_scale(right_mask)
            if left_centroid is None or right_centroid is None:
                centroid_drift = (
                    1e30
                    if (left_centroid is None) != (right_centroid is None)
                    else 0.0
                )
            else:
                centroid_drift = float(
                    torch.linalg.vector_norm(left_centroid - right_centroid).item()
                )
            scale_drift = (
                abs(right_scale - left_scale) / left_scale
                if left_scale
                else (0.0 if right_scale == 0 else 1e30)
            )

            failed = []
            if exact_artwork and int(changed_pixels.sum().item()):
                failed.append("exact_artwork")
            if masked_rmse > max_masked_normalized_rmse:
                failed.append("max_masked_normalized_rmse")
            if masked_ssim < min_masked_ssim:
                failed.append("min_masked_ssim")
            if edge_iou < min_edge_iou:
                failed.append("min_edge_iou")
            if silhouette_iou < min_silhouette_iou:
                failed.append("min_silhouette_iou")
            if centroid_drift > max_centroid_drift_px:
                failed.append("max_centroid_drift_px")
            if scale_drift > max_scale_drift:
                failed.append("max_scale_drift")
            failures.update(failed)
            reports.append(
                {
                    "candidate_index": index,
                    "passed": not failed,
                    "failed_checks": failed,
                    "changed_artwork_pixels": int(changed_pixels.sum().item()),
                    "masked_normalized_rmse": masked_rmse,
                    "masked_ssim": masked_ssim,
                    "edge_iou": edge_iou,
                    "silhouette_iou": silhouette_iou,
                    "centroid_drift_px": centroid_drift,
                    "scale_drift": scale_drift,
                }
            )
        rendered = json.dumps(
            {"schema_version": 1, "ownership": "artwork", "candidates": reports},
            sort_keys=True,
        )
        if failures:
            raise RuntimeError(
                "Artwork Fidelity Check failed: "
                + ", ".join(sorted(failures))
                + "; "
                + rendered
            )
        return candidate_images, rendered


NODE_CLASS_MAPPINGS = {
    "StickerMaskBands": StickerMaskBands,
    "StickerPerspectiveWarp": StickerPerspectiveWarp,
    "MaskedReferenceFidelityGate": MaskedReferenceFidelityGate,
    "ArtworkFidelityGate": ArtworkFidelityGate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StickerMaskBands": "Sticker Mask Bands",
    "StickerPerspectiveWarp": "Sticker Perspective Warp",
    "MaskedReferenceFidelityGate": "Masked Reference Fidelity Gate",
    "ArtworkFidelityGate": "Artwork Fidelity Gate",
}
