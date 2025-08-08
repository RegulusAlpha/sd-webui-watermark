import os
import gradio as gr
from PIL import Image, ImageDraw, ImageFont
from modules import script_callbacks

MARGIN = 10

def apply_watermark(img, text, use_image, image_path, position, custom_x, custom_y, opacity, font_name, font_size, text_color, max_size):
    img = img.convert("RGBA")

    if use_image:
        if not os.path.exists(image_path):
            return img
        watermark = Image.open(image_path).convert("RGBA")
        ratio = min(max_size / watermark.width, max_size / watermark.height, 1)
        size = (int(watermark.width * ratio), int(watermark.height * ratio))
        watermark = watermark.resize(size, Image.ANTIALIAS)
        alpha = watermark.split()[3].point(lambda p: p * (opacity / 255))
        watermark.putalpha(alpha)

        if position == "top_left":
            pos = (MARGIN, MARGIN)
        elif position == "top_right":
            pos = (img.width - watermark.width - MARGIN, MARGIN)
        elif position == "bottom_left":
            pos = (MARGIN, img.height - watermark.height - MARGIN)
        elif position == "custom":
            pos = (custom_x, custom_y)
        else:
            pos = (img.width - watermark.width - MARGIN, img.height - watermark.height - MARGIN)

        img.paste(watermark, pos, watermark)

    else:
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(f"extensions/sd-webui-watermark/assets/fonts/{font_name}.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        text_size = draw.textsize(text, font=font)

        if position == "top_left":
            pos = (MARGIN, MARGIN)
        elif position == "top_right":
            pos = (img.width - text_size[0] - MARGIN, MARGIN)
        elif position == "bottom_left":
            pos = (MARGIN, img.height - text_size[1] - MARGIN)
        elif position == "custom":
            pos = (custom_x, custom_y)
        else:
            pos = (img.width - text_size[0] - MARGIN, img.height - text_size[1] - MARGIN)

        r, g, b = parse_rgb(text_color)
        fill = (r, g, b, opacity)
        draw.text(pos, text, font=font, fill=fill)

    return img.convert("RGB")

def batch_process(files, input_dir, output_dir, *args):
    image_paths = [file.name for file in files]

    if input_dir and os.path.isdir(input_dir):
        for fname in os.listdir(input_dir):
            if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                image_paths.append(os.path.join(input_dir, fname))

    results = []
    for img_path in image_paths:
        try:
            img = Image.open(img_path).convert("RGB")
            watermarked = apply_watermark(img, *args)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                out_path = os.path.join(output_dir, os.path.basename(img_path))
                watermarked.save(out_path)
            else:
                watermarked.save(img_path)
            results.append(watermarked)
        except Exception as e:
            print(f"[Watermark UI] Failed to process {img_path}: {e}")
    return results

def parse_rgb(color_str: str):
    # Accept "#RRGGBB" or "R,G,B"
    try:
        s = color_str.strip()
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

def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as watermark_ui:
        with gr.Row():
            gr.Markdown("## 🖋️ Batch Watermark Tool")

        with gr.Row():
            uploaded_files = gr.File(file_types=[".png", ".jpg", ".jpeg"], label="Upload Images", file_count="multiple")
        
        with gr.Row():
            input_dir = gr.Textbox(label="Optional Input Directory", placeholder="/path/to/input/images")
            output_dir = gr.Textbox(label="Optional Output Directory (leave blank to overwrite originals)")

        with gr.Accordion("Watermark Settings", open=True):
            use_image = gr.Checkbox(label="Use Image Watermark", value=False)
            watermark_text = gr.Textbox(label="Text Watermark", value="My Watermark")
            watermark_image_path = gr.Textbox(label="Image Path", value="extensions/sd-webui-watermark/assets/default_watermark.png")
            watermark_position = gr.Dropdown(["bottom_right", "bottom_left", "top_right", "top_left", "center", "custom"],value="bottom_right",label="Position")
            custom_x = gr.Number(label="Custom X", value=0)
            custom_y = gr.Number(label="Custom Y", value=0)
            opacity = gr.Slider(0, 255, value=128, label="Opacity")
            font_name = gr.Textbox(label="Font Name", value="UltimatePixelFont")
            font_size = gr.Slider(8, 128, value=16, label="Font Size")
            #use_black = gr.Checkbox(label="Use Black Text", value=False)
            text_color = gr.ColorPicker(label="Text color", value="#FFFFFF")
            max_size = gr.Slider(32, 1024, value=128, label="Max Image Size (for image watermark)")

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
