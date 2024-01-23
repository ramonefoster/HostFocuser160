# log.py - Main code
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

import logging
import logging.handlers
import time
import os
try:
    from src.core.config import Config    
    CONFIG_FILE = True
except:
    CONFIG_FILE = False

def init_logging():
    if not CONFIG_FILE:
        return
    
    """ Create customized logger """
    docs_folder = os.path.join(os.path.expanduser("~"), "Documents")

    new_folder_path = os.path.join(docs_folder, "Focuser160")
    log_path = os.path.join(new_folder_path, "focuser.log")
    
    if not os.path.exists(log_path):
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
        # If the file doesn't exist, create it        
        try:
            # You can create an empty file using open() in 'w' mode
            with open(log_path, 'a') as file:
                # This will create an empty file if it doesn't exist
                print("Log file didn't exist but was CREATED with success")
        except IOError as e:
            print(f"Error creating the file: {e}")    

    logging.basicConfig(level=Config.log_level)
    logger = logging.getLogger()                # Root logger, see above
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)s %(message)s', '%Y-%m-%dT%H:%M:%S')
    formatter.converter = time.gmtime           # UTC time
    logger.handlers[0].setFormatter(formatter)  # This is the stdout handler, level set above
    # Add a logfile handler, same formatter and level
    handler = logging.handlers.RotatingFileHandler(log_path,
                                                    mode='a',
                                                    delay=True,     # Prevent creation of empty logs
                                                    maxBytes=Config.log_max_size_mb * 1000000,
                                                    backupCount=Config.log_num_keep)

    handler.setLevel(Config.log_level)
    handler.setFormatter(formatter)
    # handler.doRollover()                                            
    logger.addHandler(handler)
    if not Config.log_to_stdout:        
        logger.debug('Logging to stdout disabled in settings')
        logger.removeHandler(logger.handlers[0])    
    return logger