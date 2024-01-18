from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import *

from src.core.config import Config

import zmq
import sys
import json
import os
import time

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

main_ui_path = resource_path('../assets/client.ui')

class ClientSimulator(QtWidgets.QMainWindow):
    def __init__(self):
        super(ClientSimulator, self).__init__()
        uic.loadUi(main_ui_path, self)

        self.btnMove.clicked.connect(self.move_to)
        self.btnConnect.clicked.connect(self.connect)
        self.btnHalt.clicked.connect(self.halt)
        self.btnHome.clicked.connect(self.home)
        self.btnUp.clicked.connect(self.move_out)
        self.btnDown.clicked.connect(self.move_in)

        self.context = zmq.Context()       

        self.BarFocuser.setStyleSheet("QProgressBar::chunk ""{"'background-color: rgb(26, 26, 26)'"} QProgressBar { color: indianred; }")
        self.BarFocuser.setTextDirection(0) 

        self.previous_is_mov = None
        self.previous_pos = None

        self.connected = False
        self.is_moving = False
        self.homing = False
        self.position = 0

        self._client_id = 666

        self._msg_json = {
            "clientId": self._client_id,
            "transactionId": 0,
            "device": "Focuser",
            "action": {"cmd": "STATUS"}
            }

        self.start_client()
        self.txtStatus.setText(f"{Config.ip_address}")
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.get_status()
        self.timer.start(100)        

    def start_client(self):
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(f"tcp://{Config.ip_address}:{Config.port_pub}")
        topics_to_subscribe = ''

        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, topics_to_subscribe)

        self.poller = zmq.Poller()
        self.poller.register(self.subscriber, zmq.POLLIN)

        self.pusher = self.context.socket(zmq.PUSH)
        self.pusher.connect(f"tcp://{Config.ip_address}:{Config.port_pull}")
    
    def connect(self):
        self._msg_json["action"]["cmd"] = "CONNECT"
        self.pusher.send_string(json.dumps(self._msg_json))
    
    def home(self):
        self._msg_json["action"]["cmd"] = "HOME"
        self.pusher.send_string(json.dumps(self._msg_json))
    
    def disconnect(self):
        self._msg_json["action"]["cmd"] = "DISCONNECT"
        self.pusher.send_string(json.dumps(self._msg_json))
    
    def halt(self):
        self._msg_json["action"]["cmd"] = "HALT"
        self.pusher.send_string(json.dumps(self._msg_json))

    def move_to(self):
        if not self.is_moving:
            pos = self.txtMov.text()
            self._msg_json["action"]["cmd"] = F"MOVE={pos}"
            self.pusher.send_string(json.dumps(self._msg_json))
    
    def move_in(self):
        if not self.is_moving:
            self._msg_json["action"]["cmd"] = F"FOCUSIN"
            self.pusher.send_string(json.dumps(self._msg_json))
    
    def move_out(self):
        if not self.is_moving:
            self._msg_json["action"]["cmd"] = F"FOCUSOUT"
            self.pusher.send_string(json.dumps(self._msg_json))
    
    def get_status(self):
        self._msg_json["action"]["cmd"] = "STATUS"
        self.pusher.send_string(json.dumps(self._msg_json))
    
    def update(self):
        if round(time.time()%35) == 0:
            self.get_status()
        self.socks = dict(self.poller.poll(100))
        if self.socks.get(self.subscriber) == zmq.POLLIN:
            message = self.subscriber.recv_string()
            self.txtStatus.setText(message)
            data = json.loads(message)
            try: 
                self.position = int(data["position"])                    
                self.BarFocuser.setValue(int(self.position))
                if int(data["clientId"]) != 0:
                    self.statBusy.setStyleSheet("background-color: lightgreen")
                    self.statBusy.setText(str(data["clientId"]))
                else:
                    self.statBusy.setText('')
                    self.statBusy.setStyleSheet("background-color: indianred")
                if data["homing"]:
                    self.homing = True
                    self.statInit.setStyleSheet("background-color: lightgreen")
                else:
                    self.homing = False
                    self.statInit.setStyleSheet("background-color: indianred") 
                if data["isMoving"]:
                    self.is_moving = True
                    self.statMov.setStyleSheet("background-color: lightgreen")
                else:
                    self.is_moving = False
                    self.statMov.setStyleSheet("background-color: indianred") 
                if data["connected"]:
                    self.connected = True
                    self.statConn.setStyleSheet("background-color: lightgreen")
                else:
                    self.connected = False
                    self.statConn.setStyleSheet("background-color: indianred")               
            except Exception as e:
                print(e)
                self.BarFocuser.setValue(0)
    
    def closeEvent(self, event):
        """Close application"""
        print("Closing")
        self.disconnect()
        event.accept()
