# Voice-box theme customization

## Overview

This directory contains static files built from [xiaozhi-assets-generator](https://github.com/xinnan-tech/xiaozhi-assets-generator). The tool lets users customize wake words, fonts, emoji, and chat backgrounds, then export an `assets.bin` file for voice-box hardware.

## Directory layout

```text
generator/
├── assets/              # Generated JavaScript, CSS, and supporting build assets
├── static/              # Static resources
│   ├── charsets/        # Character sets: deepseek, gb2312, latin1, qwen18409
│   ├── fonts/           # Prebuilt font binaries and source TTF fonts
│   ├── multinet_model/  # Custom wake-word models
│   │   ├── fst/
│   │   ├── mn6_cn/
│   │   ├── mn6_en/
│   │   ├── mn7_cn/
│   │   └── mn7_en/
│   ├── twemoji32/       # 32x32 emoji images
│   ├── twemoji64/       # 64x64 emoji images
│   └── wakenet_model/   # Preset wake-word models
├── index.html           # Entry page
└── README.md            # This guide
```

Build-generated filenames contain hashes and may differ between generator releases.

## Features

### Chip and display settings

Choose ESP32-S3, ESP32-C3, ESP32-P4, or ESP32-C6, set the display resolution, and use the RGB565 color format.

### Wake words

Choose a preset WakeNet model compatible with the chip, or configure Chinese or English custom command words with thresholds and timeouts.

### Fonts

Choose a preset font, such as Alibaba PuHui or Noto Qwen, or upload a TTF/WOFF font. Set the font size and bit depth (bpp).

### Emoji

Choose from 21 basic expressions in 32x32 or 64x64 presets, or upload custom images.

### Chat backgrounds

Choose light or dark mode and a solid-color or image background. The tool adapts the background to the display resolution.

## Usage

1. Serve `index.html` through an HTTP server.
2. Choose the chip and display settings.
3. Configure theme elements in the tabs.
4. Click the generate button to review the resource list.
5. Confirm, then generate and download `assets.bin`.

## Technical notes

The `assets/` directory holds compiled output; `static/` holds the original models and resources. The bundled tool supports offline use without additional dependencies.

Use the generated `assets.bin` with compatible voice-box hardware. Check custom resources against the tool's format and size limits.

## Preserved language and model data

On 2026-10-20 the user explicitly approved keeping the source-unavailable
compiled JavaScript bundle unchanged as a translation exception. Its exact hash
is checked by the repository's English coverage guard. The English workflow
above explains how to use the tool; this change does not rebuild its UI.

The bundled JavaScript is generated output from the separate generator project, not this Vue application's maintained source. Do not hand-edit its minified UI dictionaries or third-party code to translate this guide. Source changes and a reproducible generator rebuild require a separate upstream slice.

`static/charsets/gb2312.txt` contains Chinese characters needed for font generation. The `_MODEL_INFO_` files under `static/wakenet_model/` contain model identifiers, supported Chinese wake phrases, version tags, and numeric thresholds. Keep these exact values and filenames so generated firmware assets remain compatible. The binary fonts, speech models, and emoji images also remain unchanged.
