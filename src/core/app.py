# app.py - Connections to Sockets (ZeroMQ) an control management
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

from logging import Logger

from threading import Thread
from threading import Lock
from threading import Timer

import time
import zmq
import json
import socket
import os

from src.core.config import Config

from src.interface.dmx_eth import FocuserDriver as Focuser

class App():
    def __init__(self, logger: Logger):

        self.logger = logger
        self.config_file = os.path.join(os.path.expanduser("~"), r"Documents\Focuser160\config.toml")

        # Network Settings
        self.context = None
        self.ip_address = Config.ip_address
        self.port_pub = Config.port_pub
        self.port_pull = Config.port_pull
        self.port_rep = Config.port_rep

        # Control variables
        self.stop_var = False
        self.previous_is_mov = False
        self.previous_homing = False
        self.previous_pos = 0

        # Status Message
        self.status = {
            "is_moving": False,
            "position": 0,
            "error": '',
            "connected": False,
            "homing": False,
            "at_home": False
            }

        # self.device = FocuserDriver(logger)
        self.device = Focuser(logger)

        self.start_server()  

    def start_server(self):  
        if self.context:    
            return  
        """ Starts Server ZeroMQ"""
        # ZeroMQ Context
        self.context = zmq.Context()
        print('Context Created')

        try:
            # Status Publisher
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind(f"tcp://{self.ip_address}:{self.port_pub}")
            print(f"Publisher binded to {self.ip_address}:{self.port_pub}")
        except Exception as e:
            self.logger.error(f'Error Binding Publihser: {str(e)}')
            return

        try:
            # Command Pull
            self.puller = self.context.socket(zmq.PULL)
            self.puller.bind(f"tcp://{self.ip_address}:{self.port_pull}")
            print(f"Pull binded to {self.ip_address}:{self.port_pull}")
        except Exception as e:
            self.logger.error(f'Error Binding Puller: {str(e)}')
            return

        # Poller
        self.poller = zmq.Poller()
        self.poller.register(self.puller, zmq.POLLIN)        
        self.logger.info(f'Server Started')
    
    def close_connection(self):
        try:
            self.publisher.unbind(f"tcp://{self.ip_address}:{self.port_pub}")
            self.logger.info(f'Disconnecting Publisher')
        except Exception as e:
            self.logger.error(f'Error closing Publisher connection: {str(e)}')
        try:
            self.puller.unbind(f"tcp://{self.ip_address}:{self.port_pull}")
            self.logger.info(f'Disconnecting Puller')
        except Exception as e:
            self.logger.error(f'Error closing Puller connection: {str(e)}')
        self.poller.unregister(self.puller)
        self.context.destroy()
        self.context = None

    def disconnect(self):
        self.stop()
        self.close_connection()

        self.logger.info(f'Server Disconnecting')
    
    def pub_status(self):
        json_string = json.dumps(self.status)
        self.publisher.send_string(json_string)
    
    def stop(self):
        self.stop_var = True
    
    def ping_server(self):
        """ping server"""
        timeout=2
        try:
            socket.setdefaulttimeout(timeout)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((Config.device_ip, Config.device_port))
        except OSError:
            return False
        else:
            s.close()
            return True
    
    def run(self):
        self.start_server()
        self.stop_var = False
        while not self.stop_var:
            if round(time.time(), 0)%11 == 0:
                self.ping_server()
                                        
            if self.device:                
                # Sets timeout 
                socks = dict(self.poller.poll(50))
                # Pull is being used for operation actions, such as Move, Init and Halt
                if socks.get(self.puller) == zmq.POLLIN:
                    msg_pull = self.puller.recv().decode()
                    try:   
                        self.status["error"] = '' 
                        if msg_pull == 'PING':
                            self.ping_server()
                        if msg_pull == 'INIT':
                            try:                           
                                res = self.device.home()
                                self.logger.info(f'Device Homing {res}') 
                            except Exception as e:
                                self.status["error"] = f"{str(e)}"
                                self.logger.error(f'Homing {e}')
                                self.pub_status()
                                         
                        if msg_pull == 'HALT':
                            if self.device.Halt():
                                self.logger.info(f'Device Stopped')
                            else:
                                self.logger.info(f'Halt Fail')

                        elif msg_pull == 'CONN':
                            self.device.connected = True
                            self.logger.info(f'Device Connected') 
                            try:                           
                                res = self.device.home()
                            except Exception as e:
                                self.status["error"] = f"{str(e)}"
                                self.logger.error(f'Homing {e}')
                                self.pub_status()
                            if "OK" in res:
                                self.logger.info(f'Device Homing')
                            self.pub_status()

                        elif msg_pull == 'DC':
                            self.device.connected = False
                            self.logger.info(f'Device Disconnected')

                        elif "M" in msg_pull:
                            msg_pull = msg_pull[1:]
                            try:
                                self.device.move(int(msg_pull))
                                self.logger.info(f'Moving to {msg_pull} position')
                            except Exception as e:
                                self.status["error"] = f"{str(e)}"
                                self.logger.error(f'Moving to {msg_pull} position')
                                self.pub_status()
                        else:
                            pass
                        self.status["connected"] = self.device.connected                        
                    except Exception as e:                        
                        self.status["error"] = f"{str(e)}"
                        self.pub_status()
                        self.logger.error(f'Error: {str(e)}')

                # Retrieve current values
                if self.device.connected:
                    current_is_mov = self.device.is_moving
                    current_pos = self.device.position 
                    current_homing = self.device.homing  
                    self.status["connected"] = True   

                    if current_homing != self.previous_homing:
                        self.status["homing"] = current_homing
                        self.pub_status()
                        self.previous_homing = current_homing
                        self.logger.info(f'Status published: {self.status}')      

                    # Verifies if theres a change in is_moving status
                    if current_is_mov != self.previous_is_mov:
                        self.status["is_moving"] = current_is_mov
                        self.pub_status()
                        self.previous_is_mov = current_is_mov
                        self.logger.info(f'Status published: {self.status}')

                    # Verifies if theres a change in position value
                    if current_pos != self.previous_pos:
                        self.status["position"] = current_pos
                        self.pub_status()
                        self.previous_pos = current_pos
                        self.logger.info(f'Position published: {current_pos}')

            # Add a small delay to avoid excessive processing
            time.sleep(0.1)
