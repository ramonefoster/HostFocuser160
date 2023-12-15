# config.py - Device configuration file
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

import sys
import toml

_dict = {}
_dict = toml.load(r'/home/ramones/Documents/HostControllerF160/src/config/config.toml')
def get_toml(sect: str, item: str):
    if not _dict is {}:
        return _dict[sect][item]
    else:
        return ''

class Config:
    """Device configuration in ``config.toml``"""
    # ---------------
    # Network Section
    # ---------------
    ip_address: str = get_toml('Network', 'ip_address')
    port_pub: int = get_toml('Network', 'port_pub')
    port_pull: int = get_toml('Network', 'port_pull')
    port_rep: int = get_toml('Network', 'port_rep')
    # --------------
    # Device Section
    # --------------
    motor_ip: str = get_toml('Device', 'motor_ip')
    motor_port: int = get_toml('Device', 'motor_port')
    absolute: bool = get_toml('Device', 'absolute')
    max_step: int = get_toml('Device', 'max_step')
    temp_comp: bool = get_toml('Device', 'temp_comp')
    # ---------------
    # Logging Section
    # ---------------
    log_level: str = get_toml('Logging', 'log_level')
    log_file: str = get_toml('Logging', 'log_file')