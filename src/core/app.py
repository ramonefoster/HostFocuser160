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

from src.core.config import Config

from src.interface.dmx_eth import FocuserDriver
from src.interface.sample_serial import Focuser

class App():
    def __init__(self, logger: Logger):

        self.logger = logger

        # Network Settings
        self.ip_address = Config.ip_address
        self.port_pub = Config.port_pub
        self.port_pull = Config.port_pull
        self.port_rep = Config.port_rep

        # Control variables
        self.previous_is_mov = False
        self.previous_pos = 0

        # Status Message
        self.status = {
            "is_moving": False,
            "position": 0,
            "error": '',
            "connected": False
            }

        # self.device = FocuserDriver(logger)
        self.device = Focuser()

        self.start_server()  

    def start_server(self):        
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
        
        try:
            # Command Reply
            self.replier = self.context.socket(zmq.REP)
            self.replier.bind(f"tcp://{self.ip_address}:{self.port_rep}")
            print(f"Replier binded to {self.ip_address}:{self.port_rep}")
        except Exception as e:
            self.logger.error(f'Error Binding Replier: {str(e)}')
            return

        # Poller
        self.poller = zmq.Poller()
        self.poller.register(self.puller, zmq.POLLIN)
        self.logger.info(f'Server Started')
    
    def close_connection(self, connection, connection_name):
        try:
            connection.close()
            self.logger.info(f'Disconnecting {connection_name}')
        except Exception as e:
            self.logger.error(f'Error closing {connection_name} connection: {str(e)}')

    def disconnect(self):
        connections = {
            self.replier: 'Replier',
            self.publisher: 'Publisher',
            self.puller: 'Pull'
        }

        for connection, name in connections.items():
            self.close_connection(connection, name)

        self.logger.info(f'Server Disconnecting')
    
    def pub_status(self):
        json_string = json.dumps(self.status)
        self.publisher.send_string(json_string)
    
    def run(self):
        while True:
            if self.device:                
                # Sets timeout 
                socks = dict(self.poller.poll(100))
                # Pull is being used for operation actions, such as Move, Init and Halt
                if socks.get(self.puller) == zmq.POLLIN:
                    msg_pull = self.puller.recv().decode()
                    try:                        
                        if msg_pull == 'HALT':
                            self.device.Halt()
                        elif msg_pull == 'CONN':
                            self.device.connected = True
                            self.status["connected"] = self.device.connected
                            self.pub_status()
                        elif msg_pull == 'DC':
                            self.device.connected = False
                        elif "M" in msg_pull:
                            msg_pull = msg_pull[1:]
                            self.device.move(int(msg_pull))
                            self.logger.info(f'Moving to {msg_pull} position')
                        else:
                            pass
                    except Exception as e:
                        self.publisher.send_string(f"Error {str(e)}")
                        self.logger.error(f'Error Moving: {str(e)}')

                # Req/Reply can be used both as cmd receiver and status
                elif socks.get(self.replier) == zmq.POLLIN:
                    msg = self.replier.recv_string()
                    if msg == 'HALT':
                        self.device.Halt()
                    elif msg == 'CONN':
                        self.device.connected(True)
                    elif msg == 'DC':
                        self.device.connected(False)
                    self.logger.info(f'Status Requested: {msg}')
                    self.replier.send(self.status.encode())
                    self.logger.info(f'Status Sent: {self.status}')

                # Retrieve current values
                if self.device.connected:
                    current_is_mov = self.device.is_moving
                    current_pos = self.device.position   
                    self.status["connected"] = True         

                    # Verifies if theres a change in is_moving status
                    if current_is_mov != self.previous_is_mov:
                        print("is_mov", current_is_mov)
                        self.status["is_moving"] = current_is_mov
                        self.pub_status()
                        self.previous_is_mov = current_is_mov
                        self.logger.info(f'Status published: {self.status}')

                    # Verifies if theres a change in position value
                    if current_pos != self.previous_pos:
                        print("pos", current_pos)
                        self.status["position"] = current_pos
                        self.pub_status()
                        self.previous_pos = current_pos
                        self.logger.info(f'Position published: {current_pos}')

                    # Add a small delay to avoid excessive processing
            time.sleep(0.1)
