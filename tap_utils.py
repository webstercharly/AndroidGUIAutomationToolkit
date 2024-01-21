import logging
from adb_utils import AdbUtils
from window_utils import WindowUtils

class TapUtils:
    def __init__(self):
        self.adb = AdbUtils()

    def scale_coordinates(self, location):
        android_width, android_height = self.adb.get_android_resolution()
        window = WindowUtils()
        window_left, window_top, window_width, window_height = window.get_window_region()

        scale_x = android_width / window_width
        scale_y = android_height / window_height
        x = (location[0]) * scale_x
        y = (location[1]) * scale_y
        return (x, y)

    def tap(self, location):
        logging.info(f"Tapping at location: ({location[0]}, {location[1]})")
        self.adb.run_adb_command(f"shell input tap {int(location[0])} {int(location[1])}")

    def get_center_pixel(self, location_and_size):
        center_x = int(location_and_size[0] + location_and_size[2] / 2)
        center_y = int(location_and_size[1] + location_and_size[3] / 2)
        return center_x, center_y

    def tap_at_center(self, location_and_size):
        center = self.get_center_pixel(location_and_size)
        self.tap(center)
