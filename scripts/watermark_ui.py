# scripts/watermark_ui.py

import os
import glob
import gradio as gr
from PIL import Image, ImageDraw, ImageFont
from modules import script_callbacks

MARGIN = 10
IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")

# PIL 10+ compat for resampling
try:
    RESAMPLE = Image.Resampling.LANCZOS
except Exception:
    RESAMPLE = Image.LANCZOS

def parse_rgb(color_str: str):
    # Accept "#RRGGBB" or "R,G,B"
    try:
        s = str(color_str).strip()
        if s.startswith("#"):
            s = s.lstrip("#")
            if len(s) == 6:
                r = int(s[0:2], 16)
                g = int(s[2:4], 16)
                b = int(s[4:6], 16)
                return (r, g, b)
        else:
            parts = [int(p) for p in s.split(",")]
            if len(parts) == 3:
                return tuple(max(0, min(255, v)) for v in parts)
    except Exception:
        pass
    # Fallback to white
    return (255, 255, 255)

def _measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont):
    # Prefer textbbox for better accuracy; fallback if unavailable
    try:
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return right - left, bottom - top
    except Exception:
        return draw.textsize(text, font=font)

def _resolve_pos_by_box(img_w, img_h, box_w, box_h, position, custom_x, custom_y):
    if position == "top_left":
        return (MARGIN, MARGIN)
    elif position == "top_right":
        return (img_w - box_w - MARGIN, MARGIN)
    elif position == "center":
        return ((img_w - box_w) // 2, (img_h - box_h) // 2)
    elif position == "bottom_left":
        return (MARGIN, img_h - box_h - MARGIN)
    elif position == "custom":
        return (int(custom_x), int(custom_y))
    else:  # bottom_right default
        return (img_w - box_w - MARGIN, img_h - box_h - MARGIN)

def apply_watermark(
    img,
    text,
    use_image,
    image_path,
    position,
    custom_x,
    custom_y,
    opacity,
    font_name,
    font_size,
    text_color,
    max_size,
):
    """Return a new watermarked PIL Image (RGBA compositing, preserves PNG alpha)."""
    # Sanitize numeric inputs from Gradio (they may come as float/str)
    try:
        opacity = int(opacity)
    except Exception:
        opacity = 128
    opacity = max(0, min(255, opacity))

    try:
        font_size = int(font_size)
    except Exception:
        font_size = 16
    font_size = max(1, font_size)

    try:
        max_size = int(max_size)
    except Exception:
        max_size = 128
    max_size = max(1, max_size)

    img = img.convert("RGBA")

    if use_image:
        # IMAGE WATERMARK
        if not image_path or not os.path.exists(image_path):
            return img

        try:
            watermark = Image.open(image_path).convert("RGBA")
        except Exception:
            return img

        if watermark.width == 0 or watermark.height == 0:
            return img

        # Scale but do not upscale above original
        ratio = min(max_size / watermark.width, max_size / watermark.height, 1.0)
        new_size = (max(1, int(watermark.width * ratio)), max(1, int(watermark.height * ratio)))
        watermark = watermark.resize(new_size, RESAMPLE)

        # Adjust alpha by opacity
        r, g, b, a = watermark.split()
        a = a.point(lambda p: int(p * (opacity / 255.0)))
        watermark.putalpha(a)

        pos = _resolve_pos_by_box(img.width, img.height, watermark.width, watermark.height, position, custom_x, custom_y)

        # Paste with its alpha as mask
        out = img.copy()
        out.paste(watermark, pos, watermark)
        return out
    else:
        # TEXT WATERMARK on a transparent overlay -> alpha_composite
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Load font from your extension fonts folder
        try:
            font_path = os.path.join("extensions", "sd-webui-watermark", "assets", "fonts", f"{font_name}.ttf")
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()

        text_w, text_h = _measure_text(draw, text, font)

        pos = _resolve_pos_by_box(img.width, img.height, text_w, text_h, position, custom_x, custom_y)

        r, g, b = parse_rgb(text_color)
        draw.text(pos, text, font=font, fill=(r, g, b, int(opacity)))

        return Image.alpha_composite(img, overlay)

def _collect_paths_from_uploads(files):
    """Gradio may pass None, list of file objs with .name, dicts, or str paths."""
    paths = []
    if not files:
        return paths
    for f in files:
        if isinstance(f, (str, os.PathLike)):
            paths.append(str(f))
            continue
        # common attributes across gradio versions
        p = getattr(f, "name", None) or getattr(f, "orig_name", None)
        if not p and isinstance(f, dict):
            p = f.get("name") or f.get("path")
        if p:
            paths.append(p)
    return paths

def _collect_paths_from_dir(input_dir):
    paths = []
    if input_dir and os.path.isdir(input_dir):
        for ext in IMG_EXTS:
            paths.extend(glob.glob(os.path.join(input_dir, f"*{ext}")))
    return paths

def batch_process(
    files,
    input_dir,
    output_dir,
    text,
    use_image,
    image_path,
    position,
    custom_x,
    custom_y,
    opacity,
    font_name,
    font_size,
    text_color,
    max_size,
):
    """
    Supports:
      - only uploaded files
      - only input_dir
      - both (deduped)
    Returns a list of PIL Images for the Gallery.
    """
    uploaded_paths = _collect_paths_from_uploads(files)
    dir_paths = _collect_paths_from_dir(input_dir)

    # Merge & dedupe
    seen = set()
    image_paths = []
    for p in uploaded_paths + dir_paths:
        if p and p.lower().endswith(IMG_EXTS) and p not in seen:
            seen.add(p)
            image_paths.append(p)

    if not image_paths:
        # Return a blank list -> Gallery shows nothing; better to raise a user msg
        # but Gallery output expects images; so we just return [] and rely on console/info elsewhere.
        print("[Watermark UI] No images found. Upload files or set a valid input directory.")
        return []

    results = []
    for img_path in image_paths:
        try:
            with Image.open(img_path) as im:
                orig_format = (im.format or "").upper()
                base = im.convert("RGBA")

            wm = apply_watermark(
                base,
                text,
                use_image,
                image_path,
                position,
                custom_x,
                custom_y,
                opacity,
                font_name,
                font_size,
                text_color,
                max_size,
            )

            # Decide save path
            save_path = img_path
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                save_path = os.path.join(output_dir, os.path.basename(img_path))

            if orig_format == "PNG":
                wm.save(save_path, format="PNG")
            else:
                wm.convert("RGB").save(save_path, format=(orig_format or "JPEG"))

            results.append(wm)
        except Exception as e:
            print(f"[Watermark UI] Failed to process {img_path}: {e}")

    return results

def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as watermark_ui:
        with gr.Row():
            gr.Markdown("## 🖋️ Batch Watermark Tool")

        with gr.Row():
            uploaded_files = gr.File(
                file_types=[".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"],
                label="Upload Images",
                file_count="multiple"
            )

        with gr.Row():
            input_dir = gr.Textbox(label="Optional Input Directory", placeholder="/path/to/input/images")
            output_dir = gr.Textbox(label="Optional Output Directory (leave blank to overwrite originals)")

        with gr.Accordion("Watermark Settings", open=True):
            use_image = gr.Checkbox(label="Use Image Watermark", value=False)
            watermark_text = gr.Textbox(label="Text Watermark", value="My Watermark")
            watermark_image_path = gr.Textbox(
                label="Image Path",
                value="extensions/sd-webui-watermark/assets/default_watermark.png"
            )
            watermark_position = gr.Dropdown(
                ["bottom_right", "bottom_left", "top_right", "top_left", "center", "custom"],
                value="bottom_right",
                label="Position"
            )
            custom_x = gr.Number(label="Custom X", value=0)
            custom_y = gr.Number(label="Custom Y", value=0)
            opacity = gr.Slider(0, 255, value=128, step=1, label="Opacity")
            font_name = gr.Textbox(label="Font Name", value="UltimatePixelFont")
            font_size = gr.Slider(8, 128, value=16, step=1, label="Font Size")
            text_color = gr.ColorPicker(label="Text color", value="#FFFFFF")
            max_size = gr.Slider(32, 2048, value=128, step=1, label="Max Image Size (for image watermark)")

        run_button = gr.Button("Apply Watermarks")
        output_gallery = gr.Gallery(label="Watermarked Images", columns=4)

        run_button.click(
            fn=batch_process,
            inputs=[
                uploaded_files, input_dir, output_dir,
                watermark_text, use_image, watermark_image_path,
                watermark_position, custom_x, custom_y,
                opacity, font_name, font_size, text_color, max_size
            ],
            outputs=output_gallery
        )

    return [(watermark_ui, "Watermark", "watermark_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
