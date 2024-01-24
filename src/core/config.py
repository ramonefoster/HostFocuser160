# config.py - Device configuration file
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

import os
import toml

docs_folder = os.path.join(os.path.expanduser("~"), "Documents")

new_folder_path = os.path.join(docs_folder, "Focuser160")
config_file = os.path.join(new_folder_path, "config.toml")

def create_config_file():
    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)

    if not os.path.exists(config_file):
        # If the file doesn't exist, create it
        try:
            # You can create an empty file using open() in 'w' mode
            create_default_toml_file()
                # This will create an empty file if it doesn't exist
                # print("Config file didn't exist but was CREATED with success")
        except IOError as e:
            print(f"Error creating the file: {e}")

def create_default_toml_file():
    # Default data to be written in the TOML file
    default_data = {
        "title" : "Focuser160MQ",
        "General": {
            "name" : 'Focuser160',
            "version" : '0.1.0',
            "description" : 'Interface for Perkin-Elmer Focuser',
            "startup" : True
        },
        "Device": {
            "absolute" : True,
            "device_name" : 'Mirror2',
            "deviceID" : '3285e9af-8d1d-4f9d-b368-d129d8e9a24b', # https://guidgenerator.com/online-guid-generator.aspx
            "device_ip" : '192.168.1.250',
            "device_port" : 5001,
            "encoder2microns": 47.778,
            "max_step" : 1000000,            
            "maxincrement": 0,
            "tempcompavailable": False,
            "temp_comp" : False,
            "stepsize": 0,
            "max_speed": 0            
        },
        "Network" : {
                "ip_address" : '127.0.0.1',
                "port_pub" : 7001,
                "port_pull" : 7002,
        },
        "Logging": {
                "log_level" : 'INFO',
                "log_to_stdout" : False,
                "log_max_size_mb" : 5,
                "log_num_keep" : 10
                }
    }

    # Write the default data to the TOML file
    with open(config_file, "w") as toml_file:
        toml.dump(default_data, toml_file)

create_config_file()

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
    port_pull: int = get_toml('Network', 'port_pull')
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
    maxincrement: int = get_toml('Device', 'max_increment')
    tempcompavailable: bool = get_toml('Device', 'tempcompavailable')
    # ---------------
    # Logging Section
    # ---------------
    log_level: str = get_toml('Logging', 'log_level')
    log_to_stdout: bool = get_toml('Logging', 'log_to_stdout')
    log_max_size_mb: int = get_toml('Logging', 'log_max_size_mb')
    log_num_keep: int = get_toml('Logging', 'log_num_keep')
