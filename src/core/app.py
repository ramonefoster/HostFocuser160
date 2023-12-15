# app.py - Main code
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

from logging import Logger

from threading import Lock
from threading import Timer
import time
import zmq

from src.core.config import Config

class App():
    def __init__(self, logger: Logger):

        self.logger = logger

        # Network Settings
        self.ip_address = Config.ip_address
        self.port_pub = Config.port_pub
        self.port_pull = Config.port_pull

        # Control variables
        self.previous_is_mov = False
        self.previous_pos = 0

        # Status Message
        self.status = {
            "is_moving": False,
            "position": 0,
            "error": ''
            }

        self.start_server()

    def start_server(self):        
        """ Starts Server ZeroMQ"""
        # ZeroMQ Context
        self.context = zmq.Context()

        try:
            # Status Publisher
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind(f"tcp://{self.ip_address}:{self.port_pub}")
        except Exception as e:
            self.logger.error(f'Error Binding Publihser: {e}')
            return

        try:
            # Command Pull
            self.puller = self.context.socket(zmq.PULL)
            self.puller.bind(f"tcp://{self.ip_address}:{self.port_pull}")
        except Exception as e:
            self.logger.error(f'Error Binding Puller: {e}')
            return
        
        try:
            # Command Pull
            self.replier = self.context.socket(zmq.REP)
            self.replier.bind(f"tcp://{self.ip_address}:{self.port_rep}")
        except Exception as e:
            self.logger.error(f'Error Binding Replier: {e}')
            return

        # Poller
        self.poller = zmq.Poller()
        self.poller.register(self.puller, zmq.POLLIN)
        self.logger.info(f'[Initializing] Server Started')
    
    def run(self):
        while True:
            # Sets timeout 
            socks = dict(self.poller.poll(100))

            # Pull is being used for operation actions, such as Move, Init and Halt
            if socks.get(self.puller) == zmq.POLLIN:
                msg_pull = self.puller.recv().decode()
                try:
                    self.device.move(int(msg_pull))
                except Exception as e:
                    self.logger.error(f'Error Moving: {e}')

            # Req/Reply can be used both as cmd receiver and status
            elif socks.get(self.replier) == zmq.POLLIN:
                msg_pull = self.replier.recv().decode()
                self.replier.send(self.status.encode())

            # Retrieve current values
            current_is_mov = self.device.is_moving
            current_pos = self.device.position            

            if current_is_mov != self.previous_is_mov:
                print("is_mov", current_is_mov)
                self.publisher.send_string(f"/focuser/0/ismoving {current_is_mov}")
                previous_is_mov = current_is_mov

            if current_pos != self.previous_pos:
                print("pos", current_pos)
                self.publisher.send_string(f"/focuser/0/position {current_pos}")
                previous_pos = current_pos

                # Add a small delay to avoid excessive processing
                # You can adjust this delay as needed
            time.sleep(0.1)
