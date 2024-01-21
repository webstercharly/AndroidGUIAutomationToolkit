import logging
import pyautogui
import configparser
import pygetwindow as gw

class WindowUtils:
    def __init__(self):
        # Read the configuration file
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.window_name = config.get('DEFAULT', 'window_name')
        self.offLeft = 1
        self.offRight = 5
        self.offTop = 35
        self.offBottom = 36

    def get_window(self):
        try:
            window = gw.getWindowsWithTitle(self.window_name)[0]
            return window
        except IndexError:
            logging.error(f"Window with title '{self.window_name}' not found.")
            return None

    def get_window_region(self):
        try:
            window = self.get_window()
            return (window.left + self.offLeft, window.top + self.offTop, window.width - self.offRight, window.height - self.offBottom)
        except IndexError:
            logging.error(f"Window with title '{self.window_name}' not found.")
            return None

    def screenshot(self):
        window_region = self.get_window_region()
        if window_region is not None:
            return pyautogui.screenshot(region=window_region)
        else:
            return None
