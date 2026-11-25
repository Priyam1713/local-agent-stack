"""Local patch for city96/ComfyUI-GGUF @ 6ea2651 (2026-01-12), applied 2026-11-25.

Upstream predates three architectures that ComfyUI core 0.44 already implements:
  - moss_image    kromoss-Q8_0.gguf declares general.architecture = moss_image, which is not
                  in IMG_ARCH_LIST.
  - minimax_h3    minimax_h3_fl2va_pruned-Q4_K.gguf has NO metadata, so upstream falls into
                  sd.cpp compat detection, which does not know MiniMax H3 and raises.
  - qwen_image21  qwen-image-2.1-Q8_0.gguf: no metadata either; the same failure.
The loader uses the arch string only as a gate (and for text-encoder remapping, which these
diffusion models never reach); ComfyUI core detects the model itself from tensor names, and the
key tests below are the ones core's model_detection.py uses.
Each change is applied independently and is idempotent: re-run after any `git pull` of the node.
Usage: python3 patch-comfyui-gguf.py ~/ComfyUI/custom_nodes/ComfyUI-GGUF/loader.py
"""
import sys

path = sys.argv[1]
raw = open(path, encoding="utf-8", newline="").read()  # upstream file is CRLF: keep it that way
eol = "\r\n" if "\r\n" in raw else "\n"
src = raw.replace("\r\n", "\n")
MARK = "# LOCAL-PATCH"
changed = []

# 1. Allow the three architectures through the gate.
ARCHES = ("moss_image", "minimax_h3", "qwen_image21")
head = 'IMG_ARCH_LIST = {"flux", "sd1", "sdxl", "sd3", "aura", "hidream", "cosmos", "ltxv", "hyvid", "wan", "lumina2", "qwen_image"'
line_start = src.index("IMG_ARCH_LIST = {")
line_end = src.index("\n", line_start)
line = src[line_start:line_end]
assert line.startswith(head), "IMG_ARCH_LIST line changed upstream; re-check the patch"
missing = [a for a in ARCHES if f'"{a}"' not in line]
if missing:
    body = line[: line.index("}")]
    new_line = body + "".join(f', "{a}"' for a in missing) + "}  " + MARK + " extra arches"
    src = src[:line_start] + new_line + src[line_end:]
    changed.append("arch list +" + ",".join(missing))

# 2. Recognise metadata-less MiniMax H3 / Qwen Image 2.1 files before sd.cpp detection.
upstream = """        try:
            arch_str = detect_arch(set(val[0] for val in tensors)).arch
        except Exception as e:
            raise ValueError(f"This model is not currently supported - ({e})")"""
v1 = """        keys = set(val[0] for val in tensors)
        if "video_patch_proj.weight" in keys and "audio_patch_proj.weight" in keys:  # LOCAL-PATCH moss_image/minimax_h3
            arch_str = "minimax_h3"
        else:"""
v2 = """        keys = set(val[0] for val in tensors)
        if "video_patch_proj.weight" in keys and "audio_patch_proj.weight" in keys:  # LOCAL-PATCH minimax_h3
            arch_str = "minimax_h3"
        elif {"txt_in.text_norm.weight", "modulation.1.weight", "img_in.weight", "proj_out.weight"} <= keys:  # LOCAL-PATCH qwen_image21
            arch_str = "qwen_image21"
        else:"""
fallback = """
            try:
                arch_str = detect_arch(keys).arch
            except Exception as e:
                raise ValueError(f"This model is not currently supported - ({e})")"""
if v2 in src:
    pass
elif v1 in src:
    src = src.replace(v1, v2); changed.append("detect +qwen_image21")
elif upstream in src:
    src = src.replace(upstream, v2 + fallback); changed.append("detect minimax_h3,qwen_image21")
else:
    raise SystemExit("detect_arch block changed upstream; re-check the patch")

if changed:
    open(path, "w", encoding="utf-8", newline="").write(src.replace("\n", eol))
    print("patched", path, "|", "; ".join(changed))
else:
    print("already patched")
