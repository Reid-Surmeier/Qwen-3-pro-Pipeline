from pathlib import Path

from PIL import Image

from seedance_icons.verify import image_rmse


def test_image_rmse_is_zero_for_identical_images(tmp_path: Path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    Image.new("RGB", (16, 16), "blue").save(first)
    Image.new("RGB", (16, 16), "blue").save(second)
    assert image_rmse(first, second) == 0


def test_image_rmse_detects_difference(tmp_path: Path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    Image.new("RGB", (16, 16), "blue").save(first)
    Image.new("RGB", (16, 16), "red").save(second)
    assert image_rmse(first, second) > 0
