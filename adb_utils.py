import logging
import configparser
from subprocess import Popen, PIPE, TimeoutExpired

class AdbUtils:
    def __init__(self):
        # Read the configuration file
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.adb_path = config.get('DEFAULT', 'adb_path')

    def run_adb_command(self, command):
      logging.debug("Running: %s", command)

      try:
          proc = Popen([self.adb_path] + command.split(), stdout=PIPE, stderr=PIPE)
          stdout, stderr = proc.communicate(timeout=10)

          if proc is None:
              print("Error running command")
              return None

          if proc.returncode != 0 and proc.returncode != -9:
              # -9 is timeout return code
              logging.error("Command failed, return code %d", proc.returncode)

          logging.debug("stdout: %s", stdout)
          logging.error("stderr: %s", stderr)
          return stdout, stderr
      except TimeoutExpired:
          proc.kill()
          stdout = b''
          stderr = b'Timeout'
          return stdout, stderr

    def get_android_resolution(self):
        stdout, stderr = self.run_adb_command("shell wm size")
        logging.debug(f"shell wm size: ({stdout})")
        size = stdout.decode().split()[2]
        width, height = size.split("x")
        #logging.debug(f"Width: {width}")
        #logging.debug(f"Height: {height}")
        return int(width), int(height)

    def get_android_density(self):
        stdout, stderr = self.run_adb_command('shell wm density')
        lines = stdout.decode().split("\r\n")
        physical_density = int(lines[0].split(":")[1].strip())
        override_density = int(lines[1].split(":")[1].strip())
        return physical_density, override_density