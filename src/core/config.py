# config.py - Device configuration file
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

import os
import toml

config_file = "src/config/config.toml"

_dict = {}
_dict = toml.load(config_file)
def get_toml(sect: str, item: str):
    if not _dict is {}:
        return _dict[sect][item]
    else:
        return ''

class Config:
    """Device configuration in ``config.toml``"""
    # ---------------
    # General Section
    # ---------------
    startup: str = get_toml('General', 'startup')
    name: str = get_toml('General', 'name')
    # ---------------
    # Network Section
    # ---------------
    ip_address: str = get_toml('Network', 'ip_address')
    port_pub: int = get_toml('Network', 'port_pub')
    port_rep: int = get_toml('Network', 'port_rep')
    # --------------
    # Device Section
    # --------------
    device_name: str = get_toml('Device', 'device_name')
    device_ip: str = get_toml('Device', 'device_ip')
    device_port: int = get_toml('Device', 'device_port')
    absolute: bool = get_toml('Device', 'absolute')
    max_step: int = get_toml('Device', 'max_step')
    temp_comp: bool = get_toml('Device', 'temp_comp')
    stepsize: int = get_toml('Device', 'step_size')
    max_speed: int = get_toml('Device', 'max_speed')
    enc_2_microns: float = get_toml('Device', 'encoder2microns')
    speed_factor: int = get_toml('Device', 'speedFactor')
    maxincrement: int = get_toml('Device', 'max_increment')
    speed_security: int = get_toml('Device', 'speed_security')
    tempcompavailable: bool = get_toml('Device', 'tempcompavailable')
    # ---------------
    # Logging Section
    # ---------------
    log_level: str = get_toml('Logging', 'log_level')
    log_to_stdout: bool = get_toml('Logging', 'log_to_stdout')
    log_max_size_mb: int = get_toml('Logging', 'log_max_size_mb')
    log_num_keep: int = get_toml('Logging', 'log_num_keep')
