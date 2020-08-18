"""This is the main module for starting the ttrp application"""
import logging
import time

from src.config import Configuration
from src.uvis_controller import UltraVisController

_cfg = Configuration()

if __name__ == "__main__":
    logging.info("Startup TTRP")
    start = time.process_time()
    controller = UltraVisController(debug_mode=_cfg.DEBUG)
    end = time.process_time()
    logging.info(f"TTRP started in {end-start} ms")
    controller.run()
