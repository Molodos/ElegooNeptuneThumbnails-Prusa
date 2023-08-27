# Elegoo Neptune Thumbnails Post Processing Script For PrusaSlicer

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

## Support This Project

If you like this plugin, consider supporting me :)

[![Buy Me A Coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=&slug=molodos&button_colour=5F7FFF&font_colour=ffffff&font_family=Comic&outline_colour=000000&coffee_colour=FFDD00&id=2)](https://www.buymeacoffee.com/molodos)

## General Info

> **Note:** This is a lite version of
> the [ElegooNeptuneThumbnails plugin for Cura 5.X](https://github.com/Molodos/ElegooNeptuneThumbnails). For all
> features,
> use Cura :)

PrusaSlicer post processing script for adding gcode thumbnail images for Elegoo Neptune printers. The following models
are supported (for other models, see [FAQ](#faq)):

- Elegoo Neptune 4
- Elegoo Neptune 4 Pro
- Elegoo Neptune 3 Pro
- Elegoo Neptune 3 Plus
- Elegoo Neptune 3 Max
- Elegoo Neptune 2
- Elegoo Neptune 2S
- Elegoo Neptune 2D
- Elegoo Neptune X

> **Note:** If you have some idea on how to improve the post processing script or found a bug, feel free to create
> a [GitHub issue](https://github.com/Molodos/ElegooNeptuneThumbnails-Prusa/issues/new/choose) for that

<img src="readme_images/neptune_4_preview.jpg" width="300">
<img src="readme_images/neptune_4_view.jpg" width="300">

## Installation

1) Download the post processing script binary for your operating system
   from [GitHub](https://github.com/Molodos/ElegooNeptuneThumbnails-Prusa/releases/latest)
2) Place the binary somewhere on your system and remember the path (
   e.g. `C:\Users\Michael\ElegooNeptuneThumbnails-Prusa.exe`)
3) Set the thumbnail generation in PrusaSlicer to 600x600
   PNG <img src="readme_images/prusaslicer_set_thumbnail.png" width="600">
4) Configure the path to the post processing script binary in
   PrusaSlicer <img src="readme_images/prusaslicer_add_script.png" width="600">
5) If it isn't working, check the [FAQ](#faq)

## FAQ

### Is there a Cura version of this plugin?

Yes, check out the [ElegooNeptuneThumbnails plugin for Cura 5.X](https://github.com/Molodos/ElegooNeptuneThumbnails),
which is the extended version of this pos processing script.

### Does the "normal" Neptune 3 support this plugin?

The "normal" Neptune 3 doesn't support displaying thumbnails, I have talked with Elegoo as there were many people asking
for it.

### Thumbnails are not generated. What to do?

Make sure, that you have followed the installation steps correctly.

### Why do thumbnails not change when printing another gcode file?

There seems to be a bug in older printer firmware versions which causes the thumbnail to not update if you start a print
right after the last one ended. Restarting the printer in between prints seems to fix that. If this is the case for you,
check your printer for firmware updates, which might fix the bug.

## Development Guide

1) Install requirements `pip install -r requirements.txt`
2) Develop
3) TODO: Packaging guide

## License

This repository uses code snippets and image encoding binaries from Elegoo Cura MKS Plugin and is therefore released
under the **AGPL v3** license.