# config.py - Device configuration file
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

import sys
import toml

_dict = {}
_dict = toml.load(r'src/config/config.toml')
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
    device_ip: str = get_toml('Device', 'device_port')
    device_port: int = get_toml('Device', 'device_port')
    absolute: bool = get_toml('Device', 'absolute')
    max_step: int = get_toml('Device', 'max_step')
    temp_comp: bool = get_toml('Device', 'temp_comp')
    # ---------------
    # Logging Section
    # ---------------
    log_level: str = get_toml('Logging', 'log_level')
    log_file: str = get_toml('Logging', 'log_file')
    log_to_stdout: bool = get_toml('Logging', 'log_to_stdout')
    log_max_size_mb: int = get_toml('Logging', 'log_max_size_mb')
    log_num_keep: int = get_toml('Logging', 'log_num_keep')
