# Copyright (c) 2023 - 2024 Molodos
# The ElegooNeptuneThumbnails plugin is released under the terms of the AGPLv3 or higher.

import argparse
import base64
import math
import sys
from argparse import Namespace
from array import array
from os import path

from PyQt6.QtCore import Qt, QByteArray, QBuffer, QIODeviceBase
from PyQt6.QtGui import QImage, QPainter, QFont, QColor
from PyQt6.QtWidgets import QApplication

import lib_col_pic


class SliceData:
    """
    Result data from slicing
    """

    def __init__(self, time_seconds: int, printer_model: str, model_height: float, filament_grams: float,
                 filament_cost: float, currency: str = "€"):
        self.printer_model: str = printer_model
        self.time_seconds: int = time_seconds
        self.model_height: float = model_height
        self.filament_grams: float = filament_grams
        self.filament_cost: float = filament_cost
        self.currency: str = currency


class ElegooNeptuneThumbnails:
    """
    ElegooNeptuneThumbnails post processing script
    """

    KLIPPER_THUMBNAIL_BLOCK_SIZE: int = 78
    COLORS: dict[str, QColor] = {
        "green": QColor(34, 236, 128),
        "red": QColor(209, 76, 81),
        "yellow": QColor(251, 226, 0),
        "white": QColor(255, 255, 255),
        "bg_dark": QColor(30, 36, 52),
        "bg_light": QColor(46, 54, 75),
        "bg_thumbnail": QColor(48, 57, 79),
        "own_gray": QColor(200, 200, 200),
        "darker_gray": QColor(63, 63, 63)
    }
    BG_PATH: str = path.abspath(path.join(path.dirname(path.realpath(__file__)), "img"))

    OLD_MODELS_ORCA: list[str] = ["Elegoo Neptune 2", "Elegoo Neptune 2D", "Elegoo Neptune 2S", "Elegoo Neptune X"]
    OLD_MODELS: list[str] = ["NEPTUNE2", "NEPTUNE2D", "NEPTUNE2S", "NEPTUNEX"] + OLD_MODELS_ORCA
    NEW_MODELS_ORCA: list[str] = ["Elegoo Neptune 4", "Elegoo Neptune 4 Pro", "Elegoo Neptune 4 Plus",
                                  "Elegoo Neptune 4 Max", "Elegoo Neptune 3 Pro", "Elegoo Neptune 3 Plus",
                                  "Elegoo Neptune 3 Max"]
    NEW_MODELS: list[str] = ["NEPTUNE4", "NEPTUNE4PRO", "NEPTUNE4PLUS", "NEPTUNE4MAX",
                             "NEPTUNE3PRO", "NEPTUNE3PLUS", "NEPTUNE3MAX"] + NEW_MODELS_ORCA
    B64JPG_MODELS: list[str] = ["ORANGESTORMGIGA"]

    def __init__(self):
        args: Namespace = self._parse_args()
        self._gcode: str = args.gcode
        self._printer_model: str = args.printer
        self._thumbnail: QImage = self._get_q_image_thumbnail()

        # Get slice data
        self._slice_data: SliceData = self._get_slice_data()

        # Find printer model from gcode if not set
        if not self._printer_model or self._printer_model not in (
                self.OLD_MODELS + self.NEW_MODELS + self.B64JPG_MODELS):
            if self._slice_data.printer_model is None:
                Exception("Printer model not found")
            self._printer_model = self._slice_data.printer_model

    @classmethod
    def _parse_args(cls) -> Namespace:
        """
        Parse arguments from prusa slicer
        """
        # Parse arguments
        parser = argparse.ArgumentParser(
            prog="ElegooNeptuneThumbnails-Prusa",
            description="A post processing script to add Elegoo Neptune thumbnails to gcode")
        parser.add_argument("-p", "--printer", help="Printer model to generate for", type=str, required=False,
                            default="")
        parser.add_argument("gcode", help="Gcode path provided by PrusaSlicer", type=str)
        return parser.parse_args()

    def _get_base64_thumbnail(self, min_size: int = 300) -> str:
        """
        Read the base64 encoded thumbnail from gcode file
        """
        # Try to find thumbnail
        found: bool = False
        base64_thumbnail: str = ""
        with open(self._gcode, "r", encoding="utf8") as file:
            for line in file.read().splitlines():
                if not found and line.startswith("; thumbnail begin "):
                    parts: list[str] = line.split(" ")
                    parts_two: list[str] = []
                    for part in [p.split("x") for p in parts]:
                        parts_two += part
                    width, height = map(int, parts_two[3:5])
                    if width >= min_size and height >= min_size:
                        found = True
                elif found and line == "; thumbnail end":
                    return base64_thumbnail
                elif found:
                    base64_thumbnail += line[2:]

        # If not found, raise exception
        raise Exception(
            f"Correct size thumbnail is not present: Make sure, that your slicer generates a thumbnail with a size of at least {min_size}x{min_size}")

    def _get_q_image_thumbnail(self) -> QImage:
        """
        Read the base64 encoded thumbnail from gcode file and parse it to a QImage object
        """
        # Read thumbnail
        base64_thumbnail: str = self._get_base64_thumbnail(min_size=300)

        # Parse thumbnail
        thumbnail = QImage()
        thumbnail.loadFromData(base64.decodebytes(bytes(base64_thumbnail, "UTF-8")), "PNG")
        thumbnail = thumbnail.scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio)
        return thumbnail

    def _get_slice_data(self) -> SliceData:
        """
        Read slice data from gcode file
        """
        # Mapping of data to extract
        attribute_mapping: dict[str, str] = {
            "max_z_height: ": "model_height",
            "filament used [g] = ": "filament_grams",
            "total filament cost = ": "filament_cost",
            "estimated printing time (normal mode) = ": "time",
            "printer_model = ": "printer_model"
        }

        # Example
        # "; max_z_height: 1.40"
        # "; filament used [g] = 12.94"
        # "; total filament cost = 0.26"
        # "; estimated printing time (normal mode) = 32m 11s"
        # "; printer_model = Elegoo Neptune 4 Pro"

        # Dict to store extracted data
        attributes: dict[str, str] = {}

        # Try to find all attributes
        with open(self._gcode, "r", encoding="utf8") as file:  # TODO: Optimize search
            for line in file.read().splitlines():
                if line.startswith("; "):
                    for attribute in list(attribute_mapping.keys()):
                        prefix = f"; {attribute}"
                        if line.startswith(prefix):
                            attributes[attribute_mapping[attribute]] = line[len(prefix):]
                            del attribute_mapping[attribute]

        # Parse extracted data
        time: str = attributes.get("time", None)
        time_seconds: int = -1
        if time is not None:
            time_seconds = 0
            for part in time.split(" "):
                if part.endswith("s"):
                    time_seconds += int(part[:-1])
                elif part.endswith("m"):
                    time_seconds += int(part[:-1]) * 60
                elif part.endswith("h"):
                    time_seconds += int(part[:-1]) * 60 * 60
                elif part.endswith("d"):
                    time_seconds += int(part[:-1]) * 60 * 60 * 24
                elif part.endswith("w"):
                    time_seconds += int(part[:-1]) * 60 * 60 * 24 * 7
        filament_grams: str = attributes.get("filament_grams", None)
        if filament_grams is not None:
            total: float = 0
            for entry in filament_grams.split(","):
                total += float(entry.strip())
            attributes["filament_grams"] = str(total)

        # Return data
        return SliceData(
            time_seconds=time_seconds,
            printer_model=attributes.get("printer_model", None),
            model_height=float(attributes.get("model_height", "-1")),
            filament_grams=float(attributes.get("filament_grams", "-1")),
            filament_cost=float(attributes.get("filament_cost", "-1"))
        )

    def is_supported_printer(self) -> bool:
        """
        Check if printer is supported
        """
        return self._is_old_thumbnail() or self._is_new_thumbnail() or self._is_b64jpg_thumbnail()

    def _is_old_thumbnail(self) -> bool:
        """
        Check if an old printer is present
        """
        return self._printer_model in self.OLD_MODELS

    def _is_new_thumbnail(self) -> bool:
        """
        Check if a new printer is present
        """
        return self._printer_model in self.NEW_MODELS

    def _is_b64jpg_thumbnail(self) -> bool:
        """
        Check if a base 64 JPG printer is present
        """
        return self._printer_model in self.B64JPG_MODELS

    def _add_thumbnail_metadata(self, is_light_background: bool = False, bg_image_path: str = None) -> QImage:
        """
        Add metadata and background to thumbnail and return
        """
        # Prepare background
        background: QImage = QImage(900, 900, QImage.Format.Format_RGBA8888)
        if bg_image_path is not None:
            painter = QPainter(background)
            painter.drawImage(0, 0, QImage(bg_image_path))
            painter.end()

        # Paint foreground on background
        painter = QPainter(background)
        painter.drawImage(150, 160, self._thumbnail)
        painter.end()

        # Generate option lines
        lines: list[str] = []

        # Add print time
        if self._slice_data.time_seconds < 0:
            lines.append(f"⧖ N/A")
        else:
            time_minutes: int = math.floor(self._slice_data.time_seconds / 60)
            lines.append(f"⧖ {time_minutes // 60}:{time_minutes % 60:02d}h")

        # Add model height
        if self._slice_data.model_height < 0:
            lines.append(f"⭱ N/A")
        else:
            lines.append(f"⭱ {round(self._slice_data.model_height, 2)}mm")

        # Add filament grams
        if self._slice_data.filament_grams < 0:
            lines.append(f"⭗ N/A")
        else:
            lines.append(f"⭗ {round(self._slice_data.filament_grams)}g")

        # Add filament cost
        if self._slice_data.filament_cost < 0:
            lines.append(f"⛁ N/A")
        else:
            lines.append(f"⛁ {round(self._slice_data.filament_cost, 2):.02f}{self._slice_data.currency}")

        # Add options
        app = QApplication(sys.argv)  # Trick to make QT not crash on painter.drawText (it needs a QApplication)
        painter = QPainter(background)
        font = QFont("Arial", 60)
        painter.setFont(font)
        if is_light_background:
            painter.setPen(self.COLORS["darker_gray"])
        else:
            painter.setPen(self.COLORS["own_gray"])
        for i, line in enumerate(lines):
            if line:
                left: bool = i % 2 == 0
                top: bool = i < 2
                painter.drawText(30 if left else 470,
                                 20 if top else 790, 400, 100,
                                 (Qt.AlignmentFlag.AlignLeft if left else Qt.AlignmentFlag.AlignRight) +
                                 Qt.AlignmentFlag.AlignVCenter, line)
        painter.end()

        # Return thumbnail
        return background

    def _generate_gcode_prefix(self) -> str:
        """
        Generate a g-code prefix string
        """
        # Generate metadata thumbnail
        metadata_thumbnail: QImage = self._add_thumbnail_metadata(bg_image_path=None)

        # Parse to g-code prefix
        gcode_prefix: str = ""
        if self._is_old_thumbnail():
            metadata_thumbnail_background: QImage = self._add_thumbnail_metadata(
                bg_image_path=path.join(self.BG_PATH, "bg_old.png"))
            gcode_prefix += self._parse_thumbnail_old(metadata_thumbnail_background, 100, 100, "simage")
            gcode_prefix += self._parse_thumbnail_old(metadata_thumbnail_background, 200, 200, ";gimage")
            gcode_prefix += self._parse_thumbnails_klipper(self._thumbnail, metadata_thumbnail)
        elif self._is_new_thumbnail():
            metadata_thumbnail_background: QImage = self._add_thumbnail_metadata(
                bg_image_path=path.join(self.BG_PATH, "bg_new.png"))
            gcode_prefix += self._parse_thumbnail_new(metadata_thumbnail_background, 200, 200, "gimage")
            gcode_prefix += self._parse_thumbnail_new(metadata_thumbnail_background, 160, 160, "simage")
            gcode_prefix += self._parse_thumbnails_klipper(self._thumbnail, metadata_thumbnail)
        elif self._is_b64jpg_thumbnail():
            metadata_thumbnail_background: QImage = self._add_thumbnail_metadata(is_light_background=True,
                                                                                 bg_image_path=path.join(self.BG_PATH,
                                                                                                         "bg_orangestorm.png"))
            gcode_prefix += self._parse_thumbnail_b64jpg(metadata_thumbnail_background, 400, 400, "gimage")
            gcode_prefix += self._parse_thumbnail_b64jpg(metadata_thumbnail_background, 114, 114, "simage")
            gcode_prefix += self._parse_thumbnails_klipper(self._thumbnail, metadata_thumbnail)
        if gcode_prefix:
            gcode_prefix += '\r; Thumbnail generated by the ElegooNeptuneThumbnails-Prusa post processing script (https://github.com/Molodos/ElegooNeptuneThumbnails-Prusa)' \
                            '\r; Just mentioning "Cura_SteamEngine X.X" to trick printer into thinking this is Cura gcode\r\r'

        # Return
        return gcode_prefix

    def add_thumbnail_prefix(self) -> None:
        """
        Adds thumbnail prefix to the gcode file if thumbnail doesn't already exist
        """
        # Get gcode
        g_code: str
        with open(self._gcode, "r", encoding="utf8") as file:
            g_code: str = file.read()

        # Censor original slicer
        g_code = g_code.replace("PrusaSlicer", "CensoredSlicer")
        g_code = g_code.replace("OrcaSlicer", "CensoredSlicer")

        # Disable original thumbnail
        g_code = g_code.replace("; thumbnail begin ", "; orig_thumbnail begin ")

        # Add prefix
        if ';gimage:' not in g_code and ';simage:' not in g_code:
            gcode_prefix: str = self._generate_gcode_prefix()
            with open(self._gcode, "w", encoding="utf8") as file:
                file.write(gcode_prefix + g_code)

    @classmethod
    def _parse_thumbnails_klipper(cls, small_icon: QImage, big_icon: QImage) -> str:
        """
        Generate klipper thumbnail gcode for thumbnails in sizes 32x32 and 300x300
        """
        g_code: str = "\r"
        for icon in [small_icon.scaled(32, 32), big_icon.scaled(300, 300)]:
            byte_array: QByteArray = QByteArray()
            byte_buffer: QBuffer = QBuffer(byte_array)
            byte_buffer.open(QIODeviceBase.OpenModeFlag.WriteOnly)
            icon.save(byte_buffer, "PNG")
            base64_string: str = str(byte_array.toBase64().data(), "UTF-8")
            g_code += f"; thumbnail begin {icon.width()} {icon.height()} {len(base64_string)}\r"
            while base64_string:
                g_code += f"; {base64_string[0:cls.KLIPPER_THUMBNAIL_BLOCK_SIZE]}\r"
                base64_string = base64_string[cls.KLIPPER_THUMBNAIL_BLOCK_SIZE:]
            g_code += "; thumbnail end\r\r"
        return g_code

    @classmethod
    def _parse_thumbnail_old(cls, img: QImage, width: int, height: int, img_type: str) -> str:
        """
        Parse thumbnail to string for old printers
        TODO: Maybe optimize at some time
        """
        img_type = f";{img_type}:"
        result = ""
        b_image = img.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio)
        img_size = b_image.size()
        result += img_type
        datasize = 0
        for i in range(img_size.height()):
            for j in range(img_size.width()):
                pixel_color = b_image.pixelColor(j, i)
                r = pixel_color.red() >> 3
                g = pixel_color.green() >> 2
                b = pixel_color.blue() >> 3
                rgb = (r << 11) | (g << 5) | b
                str_hex = "%x" % rgb
                if len(str_hex) == 3:
                    str_hex = '0' + str_hex[0:3]
                elif len(str_hex) == 2:
                    str_hex = '00' + str_hex[0:2]
                elif len(str_hex) == 1:
                    str_hex = '000' + str_hex[0:1]
                if str_hex[2:4] != '':
                    result += str_hex[2:4]
                    datasize += 2
                if str_hex[0:2] != '':
                    result += str_hex[0:2]
                    datasize += 2
                if datasize >= 50:
                    datasize = 0
            # if i != img_size.height() - 1:
            result += '\rM10086 ;'
            if i == img_size.height() - 1:
                result += "\r"
        return result

    @classmethod
    def _parse_thumbnail_new(cls, img: QImage, width: int, height: int, img_type: str) -> str:
        """
        Parse thumbnail to string for new printers
        TODO: Maybe optimize at some time
        """
        img_type = f";{img_type}:"

        result = ""
        b_image = img.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio)
        img_size = b_image.size()
        color16 = array('H')
        try:
            for i in range(img_size.height()):
                for j in range(img_size.width()):
                    pixel_color = b_image.pixelColor(j, i)
                    r = pixel_color.red() >> 3
                    g = pixel_color.green() >> 2
                    b = pixel_color.blue() >> 3
                    rgb = (r << 11) | (g << 5) | b
                    color16.append(rgb)
            output_data = bytearray(img_size.height() * img_size.width() * 10)
            result_int = lib_col_pic.ColPic_EncodeStr(color16, img_size.height(), img_size.width(), output_data,
                                                      img_size.height() * img_size.width() * 10, 1024)

            data0 = str(output_data).replace('\\x00', '')
            data1 = data0[2:len(data0) - 2]
            each_max = 1024 - 8 - 1
            max_line = int(len(data1) / each_max)
            append_len = each_max - 3 - int(len(data1) % each_max) + 10
            j = 0
            for i in range(len(output_data)):
                if output_data[i] != 0:
                    if j == max_line * each_max:
                        result += '\r;' + img_type + chr(output_data[i])
                    elif j == 0:
                        result += img_type + chr(output_data[i])
                    elif j % each_max == 0:
                        result += '\r' + img_type + chr(output_data[i])
                    else:
                        result += chr(output_data[i])
                    j += 1
            result += '\r;'
            for m in range(append_len):
                result += '0'

        except Exception as e:
            raise e

        return result + '\r'

    @classmethod
    def _parse_thumbnail_b64jpg(cls, img: QImage, width: int, height: int, img_type: str) -> str:
        """
        Parse thumbnail to string for new printers
        TODO: Maybe optimize at some time
        """
        img_type = f";{img_type}:"

        result = ""
        b_image = img.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio)

        try:
            byte_array: QByteArray = QByteArray()
            byte_buffer: QBuffer = QBuffer(byte_array)
            byte_buffer.open(QIODeviceBase.OpenModeFlag.WriteOnly)
            b_image.save(byte_buffer, "JPEG")
            base64_string: str = str(byte_array.toBase64().data(), "UTF-8")

            each_max = 1024 - 8 - 1
            max_line = int(len(base64_string) / each_max)

            for i in range(len(base64_string)):
                if i == max_line * each_max:
                    result += '\r;' + img_type + base64_string[i]
                elif i == 0:
                    result += img_type + base64_string[i]
                elif i % each_max == 0:
                    result += '\r' + img_type + base64_string[i]
                else:
                    result += base64_string[i]

        except Exception as e:
            raise e

        return result + '\r'


if __name__ == "__main__":
    """
    Init point of the script
    """
    thumbnail_generator: ElegooNeptuneThumbnails = ElegooNeptuneThumbnails()
    if thumbnail_generator.is_supported_printer():
        thumbnail_generator.add_thumbnail_prefix()
