import os
import gradio as gr
from PIL import Image, ImageDraw, ImageFont
from modules import script_callbacks

MARGIN = 10

def apply_watermark(img, text, use_image, image_path, position, custom_x, custom_y, opacity, font_name, font_size, use_black, max_size):
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

        color = (0, 0, 0, opacity) if use_black else (255, 255, 255, opacity)
        draw.text(pos, text, fill=color, font=font)

    return img.convert("RGB")

def batch_process(images, *args):
    watermarked = []
    for img in images:
        watermarked.append(apply_watermark(img, *args))
    return watermarked

def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as watermark_ui:
        with gr.Row():
            gr.Markdown("## 🖋️ Batch Watermark Tool")

        with gr.Row():
            input_images = gr.Image(type="pil", label="Images", tool="editor", image_mode="RGB", multiple=True)

        with gr.Accordion("Watermark Settings", open=True):
            use_image = gr.Checkbox(label="Use Image Watermark", value=False)
            watermark_text = gr.Textbox(label="Text Watermark", value="My Watermark")
            watermark_image_path = gr.Textbox(label="Image Path", value="extensions/sd-webui-watermark/assets/default_watermark.png")
            watermark_position = gr.Dropdown(["bottom_right", "bottom_left", "top_right", "top_left", "custom"], value="bottom_right", label="Position")
            custom_x = gr.Number(label="Custom X", value=0)
            custom_y = gr.Number(label="Custom Y", value=0)
            opacity = gr.Slider(0, 255, value=128, label="Opacity")
            font_name = gr.Textbox(label="Font Name", value="UltimatePixelFont")
            font_size = gr.Slider(8, 128, value=16, label="Font Size")
            use_black = gr.Checkbox(label="Use Black Text", value=False)
            max_size = gr.Slider(32, 1024, value=128, label="Max Image Size")

        run_button = gr.Button("Apply Watermarks")
        output_gallery = gr.Gallery(label="Watermarked Images", columns=4)

        run_button.click(
            fn=batch_process,
            inputs=[
                input_images,
                watermark_text, use_image, watermark_image_path,
                watermark_position, custom_x, custom_y,
                opacity, font_name, font_size, use_black, max_size
            ],
            outputs=output_gallery
        )

    return [(watermark_ui, "Watermark", "watermark_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
