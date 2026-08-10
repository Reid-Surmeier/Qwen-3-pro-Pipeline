# Source register

Checked 2026-08-10.

| Source | Authority | Pipeline fact used |
| --- | --- | --- |
| [Qwen Image 3.0 announcement](https://qwen.ai/blog?id=qwen-image-3.0) | Qwen official | About 4.5K accepted instruction tokens; 3.7K-token 3×3 example; 10 px detail claim; editing and rich spatial content |
| [Alibaba Qwen image API reference](https://help.aliyun.com/en/model-studio/qwen-image-generation-and-editing-api-reference) | Provider official | Pro/standard model IDs, image-edit request shape, one to three direct references, pixel limits, prompt enhancement modes, seed/count, 24-hour URL retention |
| [OpenRouter image generation](https://openrouter.ai/docs/guides/overview/multimodal/image-generation) | Provider official | Dedicated `/api/v1/images` API, base64 response, reference image shape, discovery and endpoint capability records |
| [OpenRouter live image-model API](https://openrouter.ai/api/v1/images/models) | Provider official | Current Qwen Image 3 availability and model slugs |
| [OpenRouter guardrails](https://openrouter.ai/docs/guides/features/guardrails/overview) | Provider official | Account-level privacy and data-policy restrictions can exclude an otherwise available provider endpoint |
| [ComfyUI Qwen-Image workflow](https://docs.comfy.org/tutorials/image/qwen/qwen-image) | ComfyUI official | Native open-weight Qwen-Image workflow and 24 GB reference measurements; distinct from Image 3 API service |
| [ComfyUI manual installation](https://docs.comfy.org/installation/manual_install) | ComfyUI official | Isolated Python environment and Linux installation sequence |
| [PlantStudio main window](https://www.kurtz-fernhout.com/PlantStudio/screenMainWindow.gif) | Original software publisher | Stable source reference recovered after the prior FigJam node disappeared |
| [comfyui-mcp](https://github.com/artokun/comfyui-mcp) | Community integration | Local MCP control plane used to expose ComfyUI workflows to Codex |
