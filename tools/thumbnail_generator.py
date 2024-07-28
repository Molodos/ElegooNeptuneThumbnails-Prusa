from typing import Callable, List
import math


class SliceData:
    """
    Result data from slicing
    """

    def __init__(self, printer_model: str, layer_height: float = 0.2, time_seconds: int = 3960, filament_meters: float = 3.9,
                 filament_grams: float = 11.6, model_height: float = 48.0, filament_cost: float = 0.25,
                 line_width: float = 0.4, currency: str = "€"):
        self.printer_model = printer_model
        self.layer_height: float = layer_height
        self.time_seconds: int = time_seconds
        self.filament_meters: float = filament_meters
        self.filament_grams: float = filament_grams
        self.model_height: float = model_height
        self.filament_cost: float = filament_cost
        self.line_width: float = line_width
        self.currency: str = currency


class ThumbnailGenerator:
    _corner_choices: dict[str, Callable[[SliceData], str]]

    @staticmethod
    def _nothing(slice_data: SliceData) -> str:
        return ""

    @staticmethod
    def _time_estimate(slice_data: SliceData) -> str:
        time_minutes: int = math.floor(slice_data.time_seconds / 60)
        return f"⧖ {time_minutes // 60}:{time_minutes % 60:02d}h"

    @staticmethod
    def _filament_grams_estimate(slice_data: SliceData) -> str:
        return f"⭗ {round(slice_data.filament_grams)}g"

    @staticmethod
    def _layer_height(slice_data: SliceData) -> str:
        if slice_data.layer_height < 0:
            return f"⧗ N/A"
        else:
            return f"⧗ {round(slice_data.layer_height, 2)}mm"

    @staticmethod
    def _model_height(slice_data: SliceData) -> str:
        if slice_data.model_height < 0:
            return f"⭱ N/A"
        else:
            return f"⭱ {round(slice_data.model_height, 2)}mm"

    @staticmethod
    def _filament_cost_estimate(slice_data: SliceData) -> str:
        return f"⛁ {round(slice_data.filament_cost, 2):.02f}{slice_data.currency}"

    @staticmethod
    def _filament_meters_estimate(slice_data: SliceData) -> str:
        return f"⬌ {round(slice_data.filament_meters, 2):.02f}m"

    @staticmethod
    def _line_width(slice_data: SliceData) -> str:
        return f"◯ {round(slice_data.line_width, 2):.02f}mm"

    @classmethod
    def available_options(cls) -> List[str]:
        return list(cls._corner_choices)

    @classmethod
    def calculate_option(cls, option: str, slice_data: SliceData) -> str:
        func = cls._corner_choices.get(option, None)
        if func is not None:
            return func(slice_data)
        else:
            return ""

    @classmethod
    def generate_option_lines(cls, corner_options, slice_data: SliceData) -> list[str]:
        """
        Generate the texts for the corners from settings
        """
        lines: list[str] = []
        for option in corner_options:
            line = cls.calculate_option(option, slice_data)
            lines.append(line)
        return lines

ThumbnailGenerator._corner_choices = {
    "nothing": ThumbnailGenerator._nothing,
    "time_estimate": ThumbnailGenerator._time_estimate,
    "filament_grams_estimate": ThumbnailGenerator._filament_grams_estimate,
    "layer_height": ThumbnailGenerator._layer_height,
    "model_height": ThumbnailGenerator._model_height,
    "filament_cost_estimate": ThumbnailGenerator._filament_cost_estimate,
    "filament_meters_estimate": ThumbnailGenerator._filament_meters_estimate,
    "line_width": ThumbnailGenerator._line_width,
}