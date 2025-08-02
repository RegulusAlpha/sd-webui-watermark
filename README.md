# 🔖 SD WebUI Watermark Extension

This extension automatically adds a customizable **text or image watermark** to images saved in **Stable Diffusion WebUI Forge**, and provides a powerful UI tab for **batch watermarking** existing images.

## ✨ Features

### ✅ Automatic Watermark on Save
- Enable/disable watermark globally or via Quicksettings
- **Text watermark mode**:
  - Custom string
  - Font (must be `.ttf` in `assets/fonts/`)
  - Adjustable font size and opacity
  - White or black text color
- **Image watermark mode**:
  - Upload transparent PNG
  - Auto-resizes to max dimension
  - Adjustable opacity
- **Watermark placement**:
  - Bottom-right (default), bottom-left, top-right, top-left
  - Or set custom X/Y coordinates
- Fully compatible with **WebUI Forge**
- Triggered only at image save, lightweight and stable

## 🧰 New Watermark Tab (Batch Processing)

A dedicated **"Watermark" tab** is now available in the UI with:

- Drag-and-drop upload for multiple images
- Optional input directory to include folder contents
- Optional output directory:
  - If blank: overwrites images in place
  - If set: saves new watermarked images there
- Independent settings (text/image, position, font, etc.)
- Live preview gallery of watermarked results

## 🖼️ Watermark Placement Options

Set position with:

- `"bottom_right"` (default)
- `"bottom_left"`
- `"top_right"`
- `"top_left"`
- `"custom"` (with `watermark_custom_x` and `watermark_custom_y`)

Can be controlled via **Quicksettings** or in the batch tab.

## 📆 Installation

1. **Download & extract** this extension into your `extensions/` folder:

   ```
   stable-diffusion-webui-forge/extensions/sd-webui-watermark/
   ```

2. Restart WebUI Forge.


## ⚙️ Configuration

### 🔧 Settings Tab (Under “Watermark”)

* **Enable watermark** (toggle)
* **Watermark type**: `text` or `image`
* **Text string**
* **Text color**: toggle black or white
* **Font name**: must match a `.ttf` file in `assets/fonts/`
* **Font size**: in pixels
* **Image watermark path**: relative to your WebUI folder
* **Opacity**: from 0 (invisible) to 255 (fully visible)
* **Max image watermark size**: in pixels

### ⚡ Quicksettings Toggle (Optional)

To toggle watermarking from the **top bar**, add this to your `config.json`:

```json
{
  "quicksettings": ["sd_model_checkpoint", "watermark_enabled"]
}
```

## 🚀 How to Use

### 🔁 Auto Watermark on Generation:
- Go to `Settings > Watermark`
- Enable `watermark_enabled`
- Customize your options

### 🖋️ Batch Watermarking:
- Go to the **Watermark** tab
- Upload images or specify input folder
- (Optional) set output folder | if output folder is not specified the input folder will be overwritten
- Customize settings
- Click **Apply Watermarks**
- Uploaded images will be modified in a TEMP directory, applying watermark will not overwrite the origional file. Save watermarked image from the output box
- All processed images will be viewable at the bottom in the watermarked images preview box


## 🌤️ Custom Fonts

To use your own fonts:

1. Place `.ttf` files into:

   ```
   extensions/sd-webui-watermark/assets/fonts/
   ```

2. In the settings, enter the font **filename without `.ttf`** in the "Font name" field.

For example:

| File in folder              | Set `watermark_font` to |
| --------------------------- | ----------------------- |
| `DejaVuSans.ttf`            | `DejaVuSans`            |
| `MyCustomSignatureFont.ttf` | `MyCustomSignatureFont` |


## 🧪 Usage Notes

* Only PNG and JPG images will be watermarked.
* Watermark will only appear if **enabled** in settings **and/or** checked in the Quicksettings bar.
* Settings changes apply immediately after clicking **Apply Settings**.


## 🧼 Uninstall

Just delete the folder:

```
extensions/sd-webui-watermark/
```

And restart WebUI Forge.


## 🛠️ Troubleshooting

* If text watermark doesn’t appear:

  * Ensure `watermark_enabled` is checked
  * Check that `watermark_type` is set to `text`
  * Make sure the font file exists and is valid
* If image watermark doesn’t show:

  * Ensure path is correct (relative to WebUI folder)
  * Image should be a transparent `.png`


## 📁 Folder Structure

```
sd-webui-watermark/
├── scripts/
│   └── watermark.py
├── assets/
│   ├── default_watermark.png
│   └── fonts/
│       └── DejaVuSans.ttf
└── README.md
```

## 💡 Planned Features

- Filename suffix instead of overwrite
- Folder recursion support
- Font auto-detection from assets
- ZIP export of batch results


Font Credits
Font Name: Ultimate Pixel Font
Author(s):

Linus Suter – https://codewelt.com

License: GNU General Public License (GPL)
This font is licensed under the GNU GPL, which allows for free use, modification, and distribution, provided the license terms are respected. For projects embedding this font in software, ensure compliance with GPL font linking exceptions if applicable.

Source: https://codewelt.com


## Licence & Contributing

Contributing:
  1 fork this repository
  2 make changes
  3 submit pull request

License: GNU General Public License (GPLv3) (https://www.gnu.org/licenses/gpl-3.0.en.html)

Made for [Stable Diffusion WebUI Forge](https://github.com/lllyasviel/stable-diffusion-webui-forge)

