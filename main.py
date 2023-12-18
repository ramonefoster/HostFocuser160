# main.py - Main code
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

from src.core.app import App
from src.core.log import init_logging

if __name__ == "__main__":
    logger = init_logging()
    app = App(logger)
    app.run()
