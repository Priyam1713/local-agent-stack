"""CPU-only check that ComfyUI core recognises a GGUF diffusion model loaded via ComfyUI-GGUF.
Reads tensor names/shapes only (mmap); does not materialise weights or touch the GPU.
Run with ~/ComfyUI/.venv/bin/python from ~/ComfyUI, CUDA_VISIBLE_DEVICES="" set.
"""
import sys, os, importlib
sys.argv = [sys.argv[0], "--cpu"] + sys.argv[1:]  # comfy.cli_args parses argv at import time
paths = sys.argv[2:]
sys.argv = sys.argv[:2]
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), "custom_nodes"))
import comfy.options
comfy.options.enable_args_parsing()  # otherwise cli_args ignores argv and --cpu is lost
import comfy.model_detection as md
loader = importlib.import_module("ComfyUI-GGUF.loader")

for p in paths:
    print("=" * 60, os.path.basename(p))
    sd, extra = loader.gguf_sd_loader(p)
    print("arch_str:", extra["arch_str"], "| tensors:", len(sd))
    # Diffusion-model-only files carry no prefix: UNETLoader / UnetLoaderGGUF detect with "".
    # (unet_prefix_from_state_dict is for full checkpoints and falls back to "model.", which fails.)
    cfg = md.model_config_from_unet(sd, "", metadata=extra.get("metadata"))
    if cfg is None:
        print("DETECTION FAILED"); continue
    print("model class:", type(cfg).__name__)
    print("unet_config:", {k: v for k, v in cfg.unet_config.items()})
