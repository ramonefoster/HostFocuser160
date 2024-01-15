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
        self.poller = None

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
        self._client_id = 0

        # Status Message
        self.status = {
            "Absolute": Config.absolute,
            "Maxincrement": Config.maxincrement,
            "Tempcomp": Config.temp_comp,
            "Tempcompavailable": Config.tempcompavailable,
            "Ismoving": False,
            "Position": 0,
            "Error": '',
            "Connected": False,
            "Homing": False,
            "Initialized": False,
            "ClientID": 0
            }

        # self.device = FocuserDriver(logger)
        self.device = Focuser(logger)
        try:
            self.device.connected = True
            self._position =self.device.position
            self.status["Position"] = self._position
        except Exception as e:
            print(e)

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
            self.status["Error"] = f'{str(e)}'
            self.logger.error(f'Error Binding Publihser: {str(e)}')
            return

        try:
            # Command Pull
            self.puller = self.context.socket(zmq.PULL)
            self.puller.bind(f"tcp://{self.ip_address}:{self.port_pull}")
            print(f"Pull binded to {self.ip_address}:{self.port_pull}")
        except Exception as e:
            self.status["Error"] = f'{str(e)}'
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
        
        
        self.context.destroy()
        self.context = None

    def disconnect(self):
        self.stop()
        self.close_connection()

        self.logger.info(f'Server Disconnecting')
    
    def pub_status(self):
        json_string = json.dumps(self.status)        
        self.publisher.send_string(json_string)
        self.logger.info(f'Status published: {self.status}')
    
    def stop(self):
        self.stop_var = True
        if self.poller:
            self.poller.unregister(self.puller)
            self.poller = None
    
    def ping_server(self):
        """ping server"""
        timeout=.5
        try:
            socket.setdefaulttimeout(timeout)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((Config.device_ip, Config.device_port))
        except OSError:
            return False
        else:
            s.close()
            return True

    def handle_home(self):
        try:
            res = self.device.home()
            self._homing = True
            self._is_moving = True
            self.logger.info(f'Device Homing {res}')
        except Exception as e:
            self.status["Error"] = str(e)
            self.logger.error(f'Homing {e}')
            self.pub_status()

    def handle_halt(self):
        if self.device.Halt():
            self._is_moving = True
            self.logger.info(f'Device Stopped')
        else:
            self.logger.info(f'Halt Fail')

    def handle_connect(self):
        self.logger.info(f'Device Connected')
        self.device.position
        self.pub_status()

    def handle_disconnect(self):
        self.logger.info(f'Device Disconnected')

    def handle_move(self, pos):
        try:
            self.device.move(int(pos))
            self.logger.info(f'Moving to {pos} position')
            self._is_moving = True
        except Exception as e:
            self.status["Error"] = str(e)
            self.logger.error(f'Moving {pos}: {str(e)}')
            self.pub_status()

    def update_status(self):
        if self._is_moving != self.previous_is_mov:
            self.status["Ismoving"] = self._is_moving
            self.previous_is_mov = self._is_moving
            self.pub_status()

        if self._homing != self.previous_homing:
            self.status["Homing"] = self._homing
            self.status["Initialized"] = self.device.initialized
            self.previous_homing = self._homing
            self.pub_status()

        if self._position != self.previous_pos:
            self.status["Position"] = self._position
            self.previous_pos = self._position
            self.pub_status()

    def run(self):
        self._client_id = 0
        self.start_server()
        self.stop_var = False
        while not self.stop_var:
            if round(time.time()) % 15 == 0:
                self.ping_server()
                self.pub_status()

            if self.device and self.device.connected and self.poller:
                socks = dict(self.poller.poll(10))
                if socks.get(self.puller) == zmq.POLLIN:
                    msg_pull = self.puller.recv_string()
                    try:
                        msg_pull = json.loads(msg_pull)
                        action = msg_pull.get("Action")
                        cmd = action.get("CMD")
                        self._client_id = msg_pull.get("ClientID") 
                    except:
                        self.status["Error"] = "Invalid JSON command."
                              
                    try:
                        self.status["Error"] = ''
                        command_handlers = {
                            'PING': self.ping_server,
                            'HOME': self.handle_home,
                            'HALT': self.handle_halt,
                            'CONNECT': self.handle_connect,
                            'DISCONNECT': self.handle_disconnect,
                            'STATUS': self.pub_status,
                        }

                        if "MOVE=" in cmd:
                            self.handle_move(cmd[5:])
                        
                        if "HALT" in cmd and self._client_id == self.status["ClientID"]:
                            self.handle_halt()

                        if cmd in command_handlers and self._client_id == 0:
                            command_handlers[cmd]()

                        self.status["Connected"] = self.device.connected

                    except Exception as e:
                        self.status["Error"] = str(e)
                        self.pub_status()
                        self.logger.error(f'Error: {str(e)}')

                if self._is_moving:
                    self._is_moving = self.device.is_moving
                    self._position = self.device.position
                if self._homing:                   
                    self._homing = self.device.homing 
                    self._position = self.device.position 
                if not self._homing and not self._is_moving:
                    self._client_id = 0
                
                self.status["ClientID"] = self._client_id
                self.update_status()

            time.sleep(0)
