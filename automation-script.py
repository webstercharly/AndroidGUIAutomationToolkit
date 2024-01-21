import os
import time
import cv2
import random
import pyautogui
import logging
import configparser
import sys
import numpy as np
from pytesseract import image_to_string
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt5.QtGui import QImage, QPainter, QPen, QPixmap
from PyQt5.QtCore import Qt, QTimer
from adb_utils import AdbUtils
from tap_utils import TapUtils
from window_utils import WindowUtils

app = QApplication([])

# Read the configuration file
config = configparser.ConfigParser()
config.read('config.ini')

# Get the configuration values
log_file = config.get('DEFAULT', 'log_file')

# Set up logging

logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode='w', format='%(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

IMAGES = {
    "freezing_edge": "imgs/freezing_edge.png",
    "freezing_edge2": "imgs/freezing_edge2.png",
    "freezing_edge3": "imgs/freezing_edge3.png",
    "freezing_edge4": "imgs/freezing_edge4.png",
    "freezing_edge5": "imgs/freezing_edge5.png",
    "freezing_edge6": "imgs/freezing_edge6.png",
    "freezing_edge7": "imgs/freezing_edge7.png",
    "frozen_queue_open_arrow": "imgs/frozen_queue_open_arrow.png",
    "frozen_queue_open_arrow2": "imgs/frozen_queue_open_arrow2.png",
    "frozen_queue_open_arrow3": "imgs/frozen_queue_open_arrow3.png",
    "frozen_queue_open_arrow4": "imgs/frozen_queue_open_arrow4.png",
    "frozen_queue_open_arrow5": "imgs/frozen_queue_open_arrow5.png",
    "frozen_queue_open_arrow6": "imgs/frozen_queue_open_arrow6.png",
    "frozen_queue_open_arrow7": "imgs/frozen_queue_open_arrow7.png",
    "queue_open_arrow": "imgs/queue_open_arrow.png",
    "queue_open_arrow2": "imgs/queue_open_arrow2.png",
    "queue_open_arrow3": "imgs/queue_open_arrow3.png",
    "infantry_queue_idle": "imgs/infantry_queue_idle.png",
    "infantry_queue_training": "imgs/infantry_queue_training.png",
    "infantry_queue_completed": "imgs/infantry_queue_completed.png",
    "infantry_camp": "imgs/infantry_camp.png",
    "infantry_camp2": "imgs/infantry_camp2.png",
    "infantry_camp3": "imgs/infantry_camp3.png",
    "infantry_camp4": "imgs/infantry_camp4.png",
    "infantry_camp5": "imgs/infantry_camp5.png",
    "tapping_train_infantry": "imgs/tapping_train_infantry.png",
    "senior_infantry_lvl3": "imgs/senior_infantry_lvl3.png",
    "train_infantry": "imgs/train_infantry.png",
    "training_success": "imgs/training_success.png",
    "back_button": "imgs/back_button.png",
    "queue_close_arrow": "imgs/queue_close_arrow.png",
    "explore_full": "imgs/explore_full.png",
    "explore_claim_button": "imgs/explore_claim_button.png",
    "explore_claim_button_bigger": "imgs/explore_claim_button_bigger.png",
    "explore_tap_exit": "imgs/explore_tap_exit.png",
    "explore_back_button": "imgs/explore_back_button.png",
    "first_purchase_cross": "imgs/first_purchase_cross.png",
    "welcome_back_title": "imgs/welcome_back_title.png",
    "welcome_back_confirm_button": "imgs/welcome_back_confirm_button.png"
}

class Overlay(QWidget):
    def __init__(self, image):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # Ensure top-left alignment
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.label.setPixmap(QPixmap.fromImage(image))

    def update_image(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

class Automation:
    def __init__(self):
        self.qimage = None
        self.painter = None
        self.overlay = None
        self.app = QApplication(sys.argv)

    def recognize_imageSQDIFF(self, template_path, screenshot):
      # Convert images to grayscale
      screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)
      template_gray = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

      # Template match using SQDIFF_NORMED
      result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_SQDIFF_NORMED)

      # Get min_val and min_loc from result
      min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

      # Threshold match
      if min_val < 0.1:
          logging.error("recognize_image: %s", str((min_loc, *template_gray.shape[::-1])))
          # Return match result and min_loc
          return (*min_loc, *template_gray.shape[::-1])
      else:
          return None

    def recognize_image_DOESNOTWORK(self, template_path, screenshot, threshold = 0.8):
      try:
          # Define base name for output files
          base_name = os.path.splitext(os.path.basename(template_path))[0]
          logging.info(base_name)
          screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
          template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

          # Create a binary mask of the template where white (255) represents the non-transparent parts
          _, mask = cv2.threshold(template, 1, 255, cv2.THRESH_BINARY)

          logging.info(f"Attempting to recognize image from template path: {template_path}")

          result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCORR_NORMED, mask=mask)
          _, result_thresh = cv2.threshold(result, threshold, 255, cv2.THRESH_BINARY)

          # Save intermediate images to disk for debugging
          cv2.imwrite(f'debug/{base_name}_screenshot_gray.png', screenshot_gray)
          cv2.imwrite(f'debug/{base_name}_template.png', template)
          cv2.imwrite(f'debug/{base_name}_mask.png', mask)
          cv2.imwrite(f'debug/{base_name}_result.png', result)
          cv2.imwrite(f'debug/{base_name}_result_thresh.png', result_thresh)

          _, max_val, _, max_loc = cv2.minMaxLoc(result)
          if max_val > threshold:
              logging.info(f"Image recognized at location: {max_loc}")
              return (*max_loc, *template.shape[::-1])
          else:
              logging.info("Image not recognized.")
              return None
      except Exception as e:
          logging.error("Error recognizing image: %s", str(e))
          return None


    def recognize_image(self, template_path, screenshot, threshold = 0.8):
        try:
            # Define base name for output files
            base_name = os.path.splitext(os.path.basename(template_path))[0]
            logging.info(base_name)

            screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            logging.info(f"Attempting to recognize image from template path: {template_path}")
            result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
            cv2.imwrite(f'debug/{base_name}_screenshot_gray.png', screenshot_gray)
            cv2.imwrite(f'debug/{base_name}_template.png', template)
            cv2.imwrite(f'debug/{base_name}_result.png', result)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val > threshold:
                logging.info(f"Image recognized at location: {max_loc}")
                return (*max_loc, *template.shape[::-1])
            else:
                logging.info("Image not recognized.")
                return None
        except Exception as e:
            logging.error("Error recognizing image: %s", str(e))
            return None

    def read_text(self):
        try:
            screenshot = WindowUtils.screenshot()
            text = image_to_string(screenshot)
            return text
        except Exception as e:
            logging.error("Error reading text: %s", str(e))
            return None

    def swipe(self, start, end, duration=1.0):
        self.run_adb_command(f"shell input swipe {start[0]} {start[1]} {end[0]} {end[1]} {int(duration*1000)}")

    def wait_and_click(self, image, timeout = 4, interval = 1, threshold = 0.8):
        coords = self.wait_for_image(image, timeout, interval, threshold)
        logging.debug(f"wait_and_click: {image} - {coords}")
        if coords is not None:
            self.click_image_cords(coords)
            return True
        return False

    def wait_for_image(self, template_path, timeout=4, interval=1, threshold = 0.8):
        start_time = time.time()
        last_location_and_size = None
        while time.time() - start_time < timeout:
            screenshot = WindowUtils().screenshot()
            if screenshot is not None:
                location_and_size = self.recognize_image(IMAGES[template_path], screenshot, threshold)
                self.draw_and_update_overlay(location_and_size)
                if location_and_size is not None:
                    if timeout > interval and last_location_and_size != location_and_size:
                        last_location_and_size = location_and_size
                        continue
                    return location_and_size
            time.sleep(interval)
        return None

    def check_and_parse_text(self, image_path, text_list, timeout=10, interval=1, threshold = 0.8):
        location_and_size = self.wait_for_image(image_path, timeout, interval, threshold)
        if location_and_size is not None:
            text = self.read_text()
            if text is not None and any(word in text for word in text_list):
                return True
        return False

    def create_qimage(self, width, height):
        logging.info(f"Creating QImage with width {width} and height {height}")
        qimage = QImage(width, height, QImage.Format_ARGB32)
        qimage.fill(Qt.transparent)
        return qimage

    def draw_on_qimage(self, qimage, location_and_size):
        logging.info(f"Drawing on QImage at location and size: {location_and_size}")
        painter = QPainter(qimage)
        painter.setPen(QPen(Qt.red, 3))

        if location_and_size is not None:
            center_x = int(location_and_size[0] + location_and_size[2] / 2)
            center_y = int(location_and_size[1] + location_and_size[3] / 2)
            logging.info(f"Drawing center at location: {(center_x, center_y)}")
            painter.drawPoint(center_x, center_y)
            painter.drawPoint(0, 0)
            painter.drawRect(location_and_size[0], location_and_size[1], location_and_size[2], location_and_size[3])

        painter.end()

    def update_overlay(self, qimage, window_x, window_y, window_width, window_height):
        logging.info(f"Updating overlay at position ({window_x}, {window_y}) with size ({window_width}, {window_height})")
        if self.overlay is None:
            self.overlay = Overlay(qimage)
        else:
            self.overlay.update_image(qimage)
        self.overlay.show()
        self.overlay.move(window_x, window_y)
        #self.overlay.resize(window_width, window_height)

    def load_image(self, image_path):
        logging.info(f"Loading image from path: {image_path}")
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is not None:
            logging.info("Image loaded successfully.")
        else:
            logging.error("Failed to load image.")
        return image

    def valid_images(self, screenshot, template_image):
        if screenshot is None or template_image is None:
            return False

        screenshot_size = screenshot.size[::-1]
        template_image_size = (template_image.shape[1], template_image.shape[0])
        if screenshot_size < template_image_size:
            logging.debug("Template image is larger than the screenshot. Skipping image recognition.")
            return False

        return True

    def hide_overlay_if_exists(self):
        if self.overlay is not None:
            self.overlay.hide()

    def draw_and_update_overlay(self, location_and_size):
        window = WindowUtils()
        window_left, window_top, window_width, window_height = window.get_window_region()
        qimage = self.create_qimage(window_width, window_height)
        logging.debug(location_and_size, qimage.width(), qimage.height())
        self.draw_on_qimage(qimage, location_and_size)
        self.update_overlay(qimage, window_left, window_top, window_width, window_height)

    def click_image_cords(self, image_cords):
        tap = TapUtils()
        top_coordinates = tap.scale_coordinates((image_cords[0], image_cords[1]));
        bottom_coordinates = tap.scale_coordinates((image_cords[2], image_cords[3]));
        location = tap.get_center_pixel(top_coordinates + bottom_coordinates)
        tap.tap(location);

    def check_explore(self):
      if self.wait_and_click("explore_full", 1, 1, 1):
          return all(self.wait_and_click(image) for image in [
              "explore_claim_button", "explore_claim_button_bigger",
              "explore_tap_exit", "explore_back_button"
          ])
      return False

    def check_queue(self):
      if self.wait_for_image("queue_close_arrow"):
          if self.wait_and_click("infantry_queue_idle"):
              logging.debug("INFO: Infantry queue is idle")
          elif self.wait_and_click("infantry_queue_completed"):
              logging.debug("INFO: Infantry queue has completed")
              self.wait_and_click("infantry_camp")
              self.wait_and_click("infantry_camp2")
              self.wait_and_click("infantry_camp3")
          else:
              logging.debug("INFO: Infantry queue is in progress")
              self.wait_and_click("queue_close_arrow", 1, 1)
              return True
      return False

    def train_infantry(self):
      success = self.wait_and_click("infantry_camp")
      if not success:
          success = self.wait_and_click("infantry_camp2")
      if not success:
          success = self.wait_and_click("infantry_camp3")
      if not success:
          success = self.wait_and_click("infantry_camp4")
      if not success:
          self.wait_and_click("infantry_camp5")
      return all(self.wait_and_click(image, 4, 1) for image in [
          "tapping_train_infantry",
          "senior_infantry_lvl3", "train_infantry", "training_success",
          "back_button"
      ])

    def dismiss_first_purchase(self):
        self.wait_and_click("first_purchase_cross")

    def dismiss_welcome_back(self):
        success = self.wait_for_image("welcome_back_title")
        if success is not None:
          self.wait_and_click("welcome_back_confirm_button")

    def check_nonfrozen_open_arrows(self):
        for open_arrow in NON_FROZEN_ARROWS:
            arrow_cords = self.wait_for_image(open_arrow, 4, 1, 0.9)
            if arrow_cords is not None:
                return open_arrow
        return None

    def check_freezing(self):
      # Check for different levels of freezing
      for freeze_level, (freeze_edge, frozen_arrow) in enumerate(zip(FREEZING_EDGES, FROZEN_ARROWS), 1):
          result = self.wait_for_image(freeze_edge, 1, 1)
          logging.debug(f"Checking for {freeze_edge}, result: {result}")
          if result is not None:
              logging.debug("Image found, breaking the loop")
              return frozen_arrow
          logging.debug("Image not found, continuing the loop")
      return None

automation = Automation()
running = True
FREEZING_EDGES = ["freezing_edge", "freezing_edge2", "freezing_edge3", "freezing_edge4", "freezing_edge5", "freezing_edge6", "freezing_edge7"]
FROZEN_ARROWS = ["frozen_queue_open_arrow", "frozen_queue_open_arrow2", "frozen_queue_open_arrow3", "frozen_queue_open_arrow4", "frozen_queue_open_arrow5", "frozen_queue_open_arrow6", "frozen_queue_open_arrow7"]
NON_FROZEN_ARROWS = ["queue_open_arrow", "queue_open_arrow2", "queue_open_arrow3"]
arrow_image = "queue_open_arrow"


def automation_main():
    automation.dismiss_first_purchase()
    automation.dismiss_welcome_back()
    automation.check_explore()
    arrow_image = automation.check_nonfrozen_open_arrows()
    if arrow_image is None:
      arrow_image = automation.check_freezing()
    if arrow_image is not None:
      success = automation.wait_and_click(arrow_image, 1, 1)
      if success:
        queue_running = automation.check_queue()
        logging.debug(queue_running)
        if not queue_running:
          automation.train_infantry()

# Create a QTimer
timer = QTimer()
timer.timeout.connect(automation_main)

# Start the timer with a 10 minute (600,000 millisecond) interval
timer.start(5000)

while running:
    automation.app.processEvents()
    time.sleep(1)
#     #if not automation.check_and_parse_text("/path/to/image2.png", ["string1", "string2"]):
#     #    automation.click_image("/path/to/image3.png")
