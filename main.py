"""This is the main module for starting the ttrp application
Track to reference implements an electromagnetic navigated ultrasound system.

Copyright (C) 2020 Thanh Nam Bach
<thanh_nam.bach@student.reutlingen-university.de>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>

"""
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
