# scripts/watermark.py

import os
import gradio as gr
from PIL import Image, ImageDraw, ImageFont
from modules import script_callbacks, shared

MARGIN = 10

# PIL 10+ renamed resampling constants
try:
    RESAMPLE = Image.Resampling.LANCZOS
except Exception:
    RESAMPLE = Image.LANCZOS

def get_font_path(font_name: str) -> str:
    font_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
    font_file = f"{font_name}.ttf"
    return os.path.join(font_dir, font_file)

def parse_rgb(color_str: str):
    """Accept '#RRGGBB' or 'R,G,B' and return (r,g,b)."""
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
    return (255, 255, 255)

def _measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont):
    """Use textbbox when available for accurate sizing; fallback to textsize."""
    try:
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return right - left, bottom - top
    except Exception:
        return draw.textsize(text, font=font)

def _resolve_text_position(img_w: int, img_h: int, text_w: int, text_h: int):
    position_setting = shared.opts.data.get("watermark_position", "bottom_right")
    custom_x = int(shared.opts.data.get("watermark_custom_x", 0))
    custom_y = int(shared.opts.data.get("watermark_custom_y", 0))

    if position_setting == "top_left":
        return (MARGIN, MARGIN)
    elif position_setting == "top_right":
        return (img_w - text_w - MARGIN, MARGIN)
    elif position_setting == "center":
        return ((img_w - text_w) // 2, (img_h - text_h) // 2)
    elif position_setting == "bottom_left":
        return (MARGIN, img_h - text_h - MARGIN)
    elif position_setting == "custom":
        return (custom_x, custom_y)
    else:
        # bottom_right default
        return (img_w - text_w - MARGIN, img_h - text_h - MARGIN)

def _resolve_image_position(img_w: int, img_h: int, wm_w: int, wm_h: int):
    position_setting = shared.opts.data.get("watermark_position", "bottom_right")
    custom_x = int(shared.opts.data.get("watermark_custom_x", 0))
    custom_y = int(shared.opts.data.get("watermark_custom_y", 0))

    if position_setting == "top_left":
        return (MARGIN, MARGIN)
    elif position_setting == "top_right":
        return (img_w - wm_w - MARGIN, MARGIN)
    elif position_setting == "center":
        return ((img_w - wm_w) // 2, (img_h - wm_h) // 2)
    elif position_setting == "bottom_left":
        return (MARGIN, img_h - wm_h - MARGIN)
    elif position_setting == "custom":
        return (custom_x, custom_y)
    else:
        # bottom_right default
        return (img_w - wm_w - MARGIN, img_h - wm_h - MARGIN)

def apply_text_watermark(image: Image.Image, text: str, opacity: int, text_color: str, font_name: str, font_size: int):
    """Draw semi-transparent text onto a separate RGBA overlay, then composite."""
    if not text:
        return image

    # Overlay for clean alpha compositing
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Load font
    try:
        font_path = get_font_path(font_name)
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()

    # Measure text and compute position
    text_w, text_h = _measure_text(draw, text, font)
    pos = _resolve_text_position(image.width, image.height, text_w, text_h)

    # Color + opacity
    r, g, b = parse_rgb(text_color)
    draw.text(pos, text, fill=(r, g, b, int(opacity)), font=font)

    # Composite overlay onto base
    return Image.alpha_composite(image, overlay)

def apply_image_watermark(image: Image.Image, watermark_path: str, max_size: int, opacity: int):
    """Paste an RGBA watermark image with scaled size and adjusted alpha."""
    if not watermark_path or not os.path.exists(watermark_path):
        return image

    try:
        watermark = Image.open(watermark_path).convert("RGBA")
    except Exception:
        return image

    if watermark.width == 0 or watermark.height == 0:
        return image

    # Scale to fit within max_size
    scale = min(max_size / watermark.width, max_size / watermark.height)
    scale = max(scale, 1e-6)  # avoid zero scale
    new_size = (int(watermark.width * scale), int(watermark.height * scale))
    watermark = watermark.resize(new_size, RESAMPLE)

    # Adjust alpha
    r, g, b, a = watermark.split()
    a = a.point(lambda p: int(p * (int(opacity) / 255.0)))
    watermark.putalpha(a)

    # Position
    pos = _resolve_image_position(image.width, image.height, watermark.width, watermark.height)

    # Paste with mask
    image.paste(watermark, pos, watermark)
    return image

def on_image_saved(params):
    try:
        if not getattr(shared.opts, "watermark_enabled", False):
            return

        path = params.filename
        if not isinstance(path, str) or not path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            return

        # Read and sanitize options
        opacity = int(getattr(shared.opts, "watermark_opacity", 128))
        opacity = max(0, min(255, opacity))

        max_size = int(getattr(shared.opts, "watermark_max_size", 64))
        max_size = max(1, max_size)

        use_image = bool(getattr(shared.opts, "watermark_use_image", False))
        text = getattr(shared.opts, "watermark_text", "My Watermark") or "My Watermark"
        color = getattr(shared.opts, "watermark_text_color", "") or ""
        if not color.strip():
            # Back-compat with old boolean switch
            color = "#000000" if getattr(shared.opts, "watermark_text_black", False) else "#FFFFFF"

        font_name = getattr(shared.opts, "watermark_font", "UltimatePixelFont") or "UltimatePixelFont"
        font_size = int(getattr(shared.opts, "watermark_font_size", 16))
        font_size = max(1, font_size)

        # Open image and remember original format
        with Image.open(path) as im:
            orig_format = im.format  # 'PNG', 'JPEG', etc.
            img = im.convert("RGBA")

        # Apply watermark
        if use_image:
            image_path = getattr(shared.opts, "watermark_image_path", "") or ""
            img = apply_image_watermark(img, image_path, max_size, opacity)
        else:
            img = apply_text_watermark(img, text, opacity, color, font_name, font_size)

        # Save back, preserving PNG alpha when possible
        if (orig_format or "").upper() == "PNG":
            img.save(path, format="PNG")
        else:
            # Non-PNGs standardized to RGB
            img.convert("RGB").save(path, format=(orig_format or "JPEG"))

    except Exception as e:
        print(f"[Watermark Extension] Failed to apply watermark: {e}")

def on_ui_settings():
    section = ("watermark", "Watermark")

    shared.opts.add_option("watermark_enabled", shared.OptionInfo(True, "Enable watermark", section=section))
    shared.opts.add_option("watermark_use_image", shared.OptionInfo(False, "Use image watermark (unchecked = use text)", section=section))

    # Text mode settings
    shared.opts.add_option("watermark_text", shared.OptionInfo("My Watermark", "Watermark text", section=section))
    shared.opts.add_option(
        "watermark_text_color",
        shared.OptionInfo(
            "#FFFFFF",                    # default value
            "Text color",                 # label
            component=gr.ColorPicker,     # Color picker component
            component_args={},            # don't pass 'label' or 'value' here
            section=section,
        )
    )
    shared.opts.add_option("watermark_font", shared.OptionInfo("UltimatePixelFont", "Font name (place .ttf in assets/fonts)", section=section))
    shared.opts.add_option("watermark_font_size", shared.OptionInfo(16, "Font size (px)", section=section))

    # Image mode settings
    shared.opts.add_option("watermark_image_path", shared.OptionInfo(
        "extensions/sd-webui-watermark/assets/default_watermark.png",
        "Path to PNG watermark",
        section=section
    ))
    shared.opts.add_option("watermark_max_size", shared.OptionInfo(64, "Max watermark size (px)", section=section))

    # Placement
    shared.opts.add_option("watermark_position", shared.OptionInfo(
        "bottom_right",
        "Watermark position (bottom_right, bottom_left, top_right, top_left, center, custom)",
        section=section
    ))
    shared.opts.add_option("watermark_custom_x", shared.OptionInfo(0, "Custom X position (if using custom)", section=section))
    shared.opts.add_option("watermark_custom_y", shared.OptionInfo(0, "Custom Y position (if using custom)", section=section))

# Register callbacks
script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_image_saved(on_image_saved)
