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
from datetime import datetime

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
        self.connection_speed = 0

        # Control variables
        self.stop_var = False
        self.previous_is_mov = False
        self.previous_homing = False
        self.previous_pos = 0
        self.last_ping_time = datetime.now()

        #variables for status request
        self._is_moving = False
        self._position = 0
        self._homing = False
        self._stopping = False
        self._client_id = 0
        self.busy_id = 0
        self._speed = Config.max_speed

        # Status Message
        self.status = {
            "absolute": Config.absolute,
            "alarm": 0,
            "cmd": '',
            "connected": False,
            "error": '',
            "homing": False,
            "initialized": False,
            "isMoving": False,
            "maxStep": Config.max_step,
            "tempComp": Config.temp_comp,
            "tempCompAvailable": Config.tempcompavailable, 
            "temperature": 0, 
            "timestamp": datetime.timestamp(datetime.now()),       
            "position": 0,
            "maxSpeed": Config.max_speed,
            }

        # self.device = FocuserDriver(logger)
        
        self.device = Focuser(self.logger)
        self.reach_device()
        self.start_server() 

    def reach_device(self):
        _try = 0
        for _try in range(5):
            self.reachable = self.ping_server()
            if self.reachable:
                break
            _try += 1
        
        if self.reachable:
            try:
                self.device.connected = True
                self._position =self.device.position
                self.status["position"] = self._position
                self.status["initialized"] = self.device.initialized
            except Exception as e:
                print(e) 

    def start_server(self): 
        """ Starts Server ZeroMQ, creating context 
        then binding PUB and PULL sockets"""

        if self.context:    
            return  
        
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
        self.pub_status()
    
    def close_connection(self):
        """Unbind all sockets and destroy context"""
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
        
        self.device.disconnect()
        self.context.destroy()
        self.context = None

    def disconnect(self):
        """Stops main loop and close all sockets"""
        self.stop()
        self.close_connection()

        self.logger.info(f'Server Disconnecting')
    
    def pub_status(self):
        """Publishes status via ZeroMQ"""
        self.status["timestamp"] = round(datetime.timestamp(datetime.now()), 2)
        json_string = json.dumps(self.status)        
        self.publisher.send_string(json_string)
        self.logger.info(f'Status published: {self.status}')
    
    def stop(self):
        """Stop main loop and unregister zmq.POLL"""
        self.stop_var = True
        if self.poller:
            self.poller.unregister(self.puller)
            self.poller = None
            time.sleep(.2)
    
    def ping_server(self):
        """Check if motor is reachable
        ::returns:: bool
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(.6)
            s.connect((Config.device_ip, Config.device_port))
            s.close()
            time.sleep(.2)
            return True
        except Exception as e:
            print(e)
            return False           

    def handle_home(self):
        """Executes the INIT routine, which means moving motor axis to the
        microswitches and then removing the backlash until the encoder return 0"""
        try:
            res = self.device.home()
            time.sleep(.2)
            if res == "OK":
                self._homing = True
                self._is_moving = True
            else:
                self.status["alarm"] = self.device.alarm()
            self.logger.info(f'Device Homing {res}')
        except Exception as e:
            print(e)
            self.status["alarm"] = self.device.alarm()
            self.status["error"] = str(e)
            self.logger.error(f'Homing {e}')
            self.pub_status()

    def handle_halt(self):
        """Stops the motor"""
        if self.device.Halt():
            time.sleep(.2)
            self._is_moving = True # set _is_moving to true so the main loop can realy check if the motor is moving or not
            self.logger.info(f'Device Stopped')
        else:
            self.status["alarm"] = self.device.alarm()
            self.logger.info(f'Halt Fail')

    def handle_speed(self, vel):
        """Change the motor's speed"""
        if self.device.speed(int(vel)):
            time.sleep(.2)
            self.logger.info(f'Speed changed')
        else:
            self.logger.info(f'Speed change Fail')

    def handle_connect(self):
        self.logger.info(f'Device Connected')
        self.device.position
        self.pub_status()

    def handle_disconnect(self):
        self.logger.info(f'Device Disconnected')

    def handle_move(self, pos, vel):
        """Move focuser to a position
        Args: 
            position (integer)
            vel (integer)
        """        
        if vel > Config.max_speed:
            vel = Config.max_speed
        elif vel <=0:
            vel = Config.max_speed
        try:
            if vel != self._speed:
                self.handle_speed(int(vel))
            self.device.move(int(pos))
            self.logger.info(f'Moving to {pos} position')
            time.sleep(.2)
            self._is_moving = True
            self._speed = vel
        except Exception as e:
            self.status["alarm"] = self.device.alarm()
            self.status["error"] = str(e)
            self.logger.error(f'Moving {pos}: {str(e)}')
            self.pub_status()

    def update_status(self):
        """Verifies if there is a change in state variables, 
        such as _is_moving, _homing and _position and publishes in ZeroMQ"""
        if self._is_moving != self.previous_is_mov:
            self.status["isMoving"] = self._is_moving
            self.previous_is_mov = self._is_moving 
            self.status["initialized"] = self.device.initialized           
            self.pub_status()

        if self._homing != self.previous_homing:
            self.status["homing"] = self._homing            
            self.previous_homing = self._homing
            self.pub_status()

        if self._position != self.previous_pos:
            self.status["position"] = self._position
            self.previous_pos = self._position
            self.pub_status()
        
        # if self._is_moving and self._homing:
        #     self.status["clientId"] = 0

    def run(self):
        self._client_id = 0
        self.start_server()
        self.stop_var = False
        self.status["connected"] = self.device.connected
        while not self.stop_var:
            t0 = time.time()
            current_time = datetime.now()
            if self.device and self.device.connected and self.poller:
                socks = dict(self.poller.poll(50))
                if socks.get(self.puller) == zmq.POLLIN:
                    msg_pull = self.puller.recv_string()
                    try:
                        msg_pull = json.loads(msg_pull)
                        action = msg_pull.get("action")
                        cmd = action.get("cmd")
                        if not 'STATUS' in cmd:
                            self.status["cmd"] = msg_pull
                            self._client_id = msg_pull.get("clientId") 
                    except:
                        self.status["error"] = "Invalid JSON command."
                        continue
                              
                    try:
                        self.status["error"] = ''
                        command_handlers = {
                            'HOME': self.handle_home,
                            'HALT': self.handle_halt,
                            'CONNECT': self.handle_connect,
                            'DISCONNECT': self.handle_disconnect,
                            'STATUS': self.pub_status,
                        }

                        if "MOVE=" in cmd:
                            self.handle_move(cmd[5:], Config.max_speed)
                        
                        if "FOCUSIN=" in cmd:
                            self.handle_move(1, cmd[8:])
                        
                        if "FOCUSOUT=" in cmd:
                            self.handle_move(Config.max_step, cmd[9:])
                        
                        if "HALT" in cmd and self._client_id == self.busy_id:
                            self.handle_halt()

                        if cmd in command_handlers and self.busy_id == 0:
                            command_handlers[cmd]()

                        self.status["connected"] = self.device.connected

                    except Exception as e:
                        self.status["error"] = str(e)
                        self.pub_status()
                        self.logger.error(f'Error: {str(e)}')

                if self._is_moving:
                    self._is_moving = self.device.is_moving
                    self._position = self.device.position
                if self._homing:                   
                    self._homing = self.device.homing 
                    # self._position = self.device.position 
                if not self._homing and not self._is_moving:
                    self._client_id = 0
                    self.status["cmd"] = ''                    
                
                self.busy_id = self._client_id
                self.update_status()                
                self.status["alarm"] = 0
            else:
                if (current_time - self.last_ping_time).total_seconds() >= 15:
                    self.reachable = self.ping_server()
                    self.last_ping_time = current_time
            self.connection_speed = f"interval:  {round(time.time()-t0, 3)}"

