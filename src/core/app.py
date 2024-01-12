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
        self.config_file = os.path.join(os.path.expanduser("~"), "Documents/Focuser160/config.toml")

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

        #variables for status request
        self._is_moving = False
        self._position = 0
        self._homing = False
        self._stopping = False
        self._id = None

        # Status Message
        self.status = {
            "absolute": Config.absolute,
            "maxincrement": Config.maxincrement,
            "tempcomp": Config.temp_comp,
            "tempcompavailable": Config.tempcompavailable,
            "ismoving": False,
            "position": 0,
            "error": '',
            "connected": False,
            "homing": False,
            "athome": False
            }

        # self.device = FocuserDriver(logger)
        self.device = Focuser(logger)
        self.device.connected = True

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
            self.status["error"] = f'{str(e)}'
            self.logger.error(f'Error Binding Publihser: {str(e)}')
            return

        try:
            # Command Pull
            self.puller = self.context.socket(zmq.PULL)
            self.puller.bind(f"tcp://{self.ip_address}:{self.port_pull}")
            print(f"Pull binded to {self.ip_address}:{self.port_pull}")
        except Exception as e:
            self.status["error"] = f'{str(e)}'
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
            # if round(time.time(), 0)%11 == 0:
            #     self.ping_server()
                                        
            if self.device:                
                # Sets timeout 
                socks = dict(self.poller.poll(10))
                # Pull is being used for operation actions, such as Move, Init and Halt
                if socks.get(self.puller) == zmq.POLLIN:
                    msg_pull = self.puller.recv_string()
                    try:  
                        self.status["error"] = '' 
                        if msg_pull == 'PING':
                            self.ping_server()
                        elif msg_pull == 'HOME':
                            try:                           
                                res = self.device.home()
                                self._homing = True
                                self._is_moving = True
                                self.logger.info(f'Device Homing {res}') 
                            except Exception as e:
                                self.status["error"] = f"{str(e)}"
                                self.logger.error(f'Homing {e}')
                                self.pub_status()
                                         
                        if msg_pull == 'HALT':
                            if self.device.Halt():
                                self._is_moving = True
                                self.logger.info(f'Device Stopped')
                            else:
                                self.logger.info(f'Halt Fail')

                        elif msg_pull == 'CONNECT':                            
                            self.logger.info(f'Device Connected')                             
                            self.device.position                            
                            self.pub_status()                            

                        elif msg_pull == 'DISCONNECT':
                            self.device.connected = False
                            self.logger.info(f'Device Disconnected')
                        
                        elif msg_pull == 'STATUS':
                            self.pub_status()

                        elif "MOVE" in msg_pull:
                            msg_pull = msg_pull[4:]
                            try:
                                self.device.move(int(msg_pull))
                                self.logger.info(f'Moving to {msg_pull} position')
                                self._is_moving = True
                            except Exception as e:
                                self.status["error"] = f"{str(e)}"
                                self.logger.error(f'Moving {msg_pull}: {str(e)}')
                                self.pub_status()
                        else:
                            pass
                        self.status["connected"] = self.device.connected                        
                    except Exception as e:                        
                        self.status["error"] = f"{str(e)}"
                        self.pub_status()
                        self.logger.error(f'Error: {str(e)}')

                current_pos = 0
                # Retrieve current values
                if self.device.connected:
                    if self._is_moving:
                        self._is_moving = self.device.is_moving
                        self._position = self.device.position
                    if self._homing:                   
                        self._homing = self.device.homing 
                        self._position = self.device.position 
                     
                    self.status["connected"] = True   

                    if self._homing != self.previous_homing:
                        self.status["homing"] = self._homing
                        self.pub_status()
                        self.previous_homing = self._homing
                        self.logger.info(f'Status published: {self.status}')      

                    # Verifies if theres a change in is_moving status
                    if self._is_moving != self.previous_is_mov:
                        self.status["ismoving"] = self._is_moving
                        self.pub_status()
                        self.previous_is_mov = self._is_moving
                        self.logger.info(f'Status published: {self.status}')

                    # Verifies if theres a change in position value
                    if self._position != self.previous_pos:
                        self.status["position"] = self._position
                        self.pub_status()
                        self.previous_pos = self._position
                        self.logger.info(f'Position published: {self._position}')

            # Add a small delay to avoid excessive processing
            time.sleep(0.05)
