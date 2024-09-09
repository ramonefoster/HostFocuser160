# main.py - Main code
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QMessageBox, QMenu, QSystemTrayIcon, QAction

import sys
import os
from threading import Thread
from src.core.log import init_logging
import time

try:
    from src.core.config import Config    
    CONFIG_FILE = True
    ERR_VALUE = None
except Exception as e:
    ERR_VALUE = str(e)
    CONFIG_FILE = False

if CONFIG_FILE:
    from src.core.app import App
    
    from misc.client_sample import ClientSimulator

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

main_ui_path = resource_path('assets/main.ui')
icon_tray = resource_path('assets/icon.png')

class FocuserOPD(QtWidgets.QMainWindow):
    def __init__(self):
        super(FocuserOPD, self).__init__()
        uic.loadUi(main_ui_path, self)

        if not CONFIG_FILE:
            close = QMessageBox()
            close.setText(f"Arquivo de configuração com problemas!\n{ERR_VALUE}")
            close.setStandardButtons(QMessageBox.Ok)
            close = close.exec()

            if close == QMessageBox.Ok:   
                sys.exit()
            
        self.control = App(logger)

        self.config_file = r"src/config/config.toml"
        self.log_file = r"logs/focuser.log"

        main_window_geometry = self.geometry()  # Get the geometry of the main window

        # Calculate the coordinates for the right side of the main window
        dock_x = main_window_geometry.x() + main_window_geometry.width() + 100  # Adjust for spacing
        dock_y = main_window_geometry.y()
        
        self.lblIP.setText(f"IP: {self.control.ip_address}")
        self.lblPort.setText(f"PUB {self.control.port_pub}, PULL {self.control.port_pull}")

        # LOG FILE
        self.log_text_edit = QtWidgets.QTextEdit()  # Widget to display log
        self.log_dock_widget = QtWidgets.QDockWidget("Log", self)
        self.log_dock_widget.setWidget(self.log_text_edit)
        self.log_text_edit.setStyleSheet("color: lightgrey")
        self.boxLog.stateChanged.connect(self.toggle_log_view)     
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock_widget)
        self.log_dock_widget.setMinimumSize(600, 500)   
        self.log_dock_widget.setFloating(True)
        self.log_dock_widget.move(dock_x, dock_y)  
        self.log_dock_widget.hide()  # Hide log view by default  

        # Create the QTextEdit and QPushButton
        self.conf_text_edit = QtWidgets.QTextEdit()
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save_config_file)
        self.save_button.setStyleSheet("background-color: lightgrey")
        # Create a widget to hold the QTextEdit and the "Save" button
        widget_inside_dock = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.conf_text_edit)
        self.conf_text_edit.setStyleSheet("color: lightgrey")
        layout.addWidget(self.save_button)
        widget_inside_dock.setLayout(layout)
        # Create the QDockWidget and set its content
        self.conf_dock_widget = QtWidgets.QDockWidget("Config", self)
        self.conf_dock_widget.setWidget(widget_inside_dock)
        self.conf_dock_widget.move(dock_x, dock_y)        
        # Add the QDockWidget to the main window and hide it initially
        self.addDockWidget(Qt.BottomDockWidgetArea, self.conf_dock_widget)
        self.conf_dock_widget.hide()    
        self.conf_dock_widget.setMinimumSize(400, 500)   
        self.conf_dock_widget.setFloating(True)

        # Buttons
        self.btnStart.clicked.connect(self.start)
        self.btnStop.clicked.connect(self.stop)  
        self.actionSettings.triggered.connect(self.toggle_config_view)
        self.btnHide.clicked.connect(self.minimize_to_tray)
        self.actionClient_Simulator.triggered.connect(self.run_simulator)
        
        # Create a system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(icon_tray))  # Replace 'icon.png' with your icon file
        self.tray_icon.setToolTip('Focus160Server')

        self.tray_menu = QMenu(self)
        restore_action = QAction('Restore', self)
        restore_action.triggered.connect(self.restore_from_tray)
        self.tray_menu.addAction(restore_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)

        self.tray_icon.show()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(100)

        self.reachable = False

        self.run_thread = None
        self.statusBar().showMessage("Ready")

        self.ping()
        if Config.startup:
            self.start()
    
    def minimize_to_tray(self):
        """Minimize to tray"""
        self.hide()  
        self.tray_icon.show() 

    def restore_from_tray(self):
        """Restore from Tray"""
        self.show()  
        self.tray_icon.hide()
    
    def tray_activated(self, reason):
        """Restore from double click on icon"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.restore_from_tray()
    
    def run_simulator(self):
        """Opens the simulator window"""
        self.second_window = ClientSimulator()
        self.second_window.show()
    
    def start(self):
        """Start server"""
        if self.run_thread and self.run_thread.is_alive():
            print("Still Alive")
            return
        self.run_thread = Thread(target = self.control.run)
        self.run_thread.start()
        # self.run_thread.daemon = True
    
    def stop(self):
        """Stops main program and the main loop at Application interface with Device"""
        if self.control:
            self.control.disconnect()
        if self.run_thread and self.run_thread.is_alive():
            self.run_thread.join()
    
    def toggle_config_view(self):
        """Shows config side window"""
        self.read_config_file(self.config_file)
        self.conf_dock_widget.show()

    def read_config_file(self, file_path):
        """Reads config file"""
        with open(file_path, "r") as file:
            config_content = file.read()
        self.conf_text_edit.setPlainText(config_content)
    
    def save_config_file(self):
        """Save modified config in config file"""
        content_to_save = self.conf_text_edit.toPlainText()        
        with open(self.config_file, "w") as file:
            file.write(content_to_save)

    def toggle_log_view(self, state):
        """Shows LOG side window"""
        if state == Qt.Checked:
            
            if self.log_file:
                self.read_log_file(self.log_file)
                self.log_dock_widget.show()
        else:
            self.log_dock_widget.hide()

    def read_log_file(self, file_path):
        """Open LOG file"""
        with open(file_path, "r") as file:
            log_content = file.read()
            self.log_text_edit.setPlainText(log_content)
           
    def ping(self):
        """Checks if device is reachable"""
        if self.control.reachable:
            self.lblPing.setText("Device is Reachable")
            self.reachable = True
            self.statMotor.setStyleSheet("background-color: green; border-radius: 10px;")
            self.statRouter.setStyleSheet("background-color: green; border-radius: 10px;")
            self.lineSR.setStyleSheet("background-color: green; border-radius: 10px;")
            self.lineRM.setStyleSheet("background-color: green; border-radius: 10px;")
        else:
            self.statMotor.setStyleSheet("background-color: indianred; border-radius: 10px;")
            self.lineRM.setStyleSheet("background-color: indianred; border-radius: 10px;")
            self.reachable = False
            if not self.control.router:
                self.lblPing.setText("Router is NOT Reachable")
                self.statRouter.setStyleSheet("background-color: indianred; border-radius: 10px;")
                self.lineSR.setStyleSheet("background-color: indianred; border-radius: 10px;")
            else:
                self.statRouter.setStyleSheet("background-color: green; border-radius: 10px;")
                self.lblPing.setText("Device is NOT Reachable")
        
    def update(self):   
        """Main loop and UI manager"""     
        status = self.control.status
        con = status["connected"]
        
        if self.run_thread and self.run_thread.is_alive():
            self.statusBar().setStyleSheet("background-color: green")
            self.statServer.setStyleSheet("background-color: green; border-radius: 10px;")
        else:
            self.statusBar().setStyleSheet("background-color: indianred")
            self.statServer.setStyleSheet("background-color: indianred; border-radius: 10px;")
        if con:
            self.statusBar().showMessage("Device Socket Connected")
            if not self.reachable:
                self.lblPing.setText("Device is Reachable")
                self.reachable = True
        else:
            if self.reachable:
                self.lblPing.setText("Device is NOT Reachable")
                self.reachable = False
            self.statusBar().showMessage("Device Socket Disconnected")
        self.lblPos.setText(str(status["position"]))
        self.lblEnc.setText(str(self.control.encoder))
        self.txtClientID.setText(str(self.control.busy_id))
        self.lblCommSpeed.setText(str(self.control.connection_speed))
        if len(status["error"]) > 1:
            self.lblErr.setToolTip(status["error"])
            self.lblErr.setStyleSheet("background-color: indianred; border-radius: 10px;")
        else:
            self.lblErr.setStyleSheet("background-color: rgb(119, 118, 123); border-radius: 10px;")
        if status["isMoving"]:
            self.lblMov.setStyleSheet("background-color: green; border-radius: 10px;")
        else:
            self.lblMov.setStyleSheet("background-color: rgb(119, 118, 123); border-radius: 10px;")
        
        #updates UI Stats every 15sec
        if time.time() % 15 == 0:
            self.ping()
    
    def closeEvent(self, event):
        """Close application"""
        close = QMessageBox()
        close.setText("Deseja sair?")
        close.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        close = close.exec()

        if close == QMessageBox.Yes:   
            self.stop()  
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":

    logger = init_logging() 
    app = QtWidgets.QApplication([])       

    main_window1 = FocuserOPD()
    main_window1.show()
    

    sys.exit(app.exec_()) 
    
    
