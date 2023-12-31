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
import time
import os
from threading import Thread

from src.core.app import App
from src.core.log import init_logging
from src.core.config import Config

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

main_ui_path = resource_path('assets/main.ui')
icon_tray = resource_path('assets/icon.png')

print(main_ui_path, icon_tray)
Ui_MainWindow, QtBaseClass = uic.loadUiType(main_ui_path)

class FocuserOPD(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.control = App(logger)

        self.config_file = os.path.join(os.path.expanduser("~"), "Documents/Focuser160/config.toml")
        self.log_file = os.path.join(os.path.expanduser("~"), "Documents/Focuser160/focuser.log")

        main_window_geometry = self.geometry()  # Get the geometry of the main window

        # Calculate the coordinates for the right side of the main window
        dock_x = main_window_geometry.x() + main_window_geometry.width() + 100  # Adjust for spacing
        dock_y = main_window_geometry.y()
        
        self.lblIP.setText(f"IP: {self.control.ip_address}")
        self.lblPort.setText(f"{self.control.port_pub}, {self.control.port_pull}, {self.control.port_rep}")

        # LOG FILE
        self.log_text_edit = QtWidgets.QTextEdit()  # Widget to display log
        self.log_dock_widget = QtWidgets.QDockWidget("Log", self)
        self.log_dock_widget.setWidget(self.log_text_edit)
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
        # Create a widget to hold the QTextEdit and the "Save" button
        widget_inside_dock = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.conf_text_edit)
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

        self.run_thread = None
        self.statusBar().showMessage("Ready")
        self.ping()

        if Config.startup:
            self.start()
    
    def minimize_to_tray(self):
        self.hide()  
        self.tray_icon.show() 

    def restore_from_tray(self):
        self.show()  
        self.tray_icon.hide()
    
    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.restore_from_tray()
    
    def start(self):
        if self.run_thread and self.run_thread.is_alive():
            print("Still Alive")
        self.run_thread = Thread(target = self.control.run)
        self.run_thread.start()
        # self.run_thread.daemon = True
    
    def stop(self):
        self.control.disconnect()
        if self.run_thread and self.run_thread.is_alive():
            self.run_thread.join()
    
    def toggle_config_view(self):   
        self.read_config_file(self.config_file)
        self.conf_dock_widget.show()

    def read_config_file(self, file_path):
        with open(file_path, "r") as file:
            log_content = file.read()
            self.conf_text_edit.setPlainText(log_content)
    
    def save_config_file(self):
        content_to_save = self.conf_text_edit.toPlainText()        
        with open(self.config_file, "w") as file:
            file.write(content_to_save)

    def toggle_log_view(self, state):
        if state == Qt.Checked:
            
            if self.log_file:
                self.read_log_file(self.log_file)
                self.log_dock_widget.show()
        else:
            self.log_dock_widget.hide()

    def read_log_file(self, file_path):
        with open(file_path, "r") as file:
            log_content = file.read()
            self.log_text_edit.setPlainText(log_content)
        
        self.update_log_timer = QTimer(self)
        self.update_log_timer.timeout.connect(lambda: self.read_log_file(file_path))
        self.update_log_timer.start(20000)
    
    def ping(self):
        if self.control.ping_server():
            self.lblPing.setText("Device is Reachable")
        else:
            self.lblPing.setText("Device is NOT Reachable")
        
    def update(self):        
        status = self.control.status
        con = status["connected"]
        # if round(time.time(), 0)%33 == 0:
        #     self.ping()
        if self.run_thread and self.run_thread.is_alive():
            self.statusBar().setStyleSheet("background-color: green")
        else:
            self.statusBar().setStyleSheet("background-color: indianred")
        if con:
            self.statusBar().showMessage("Client Connected")
        else:
            self.statusBar().showMessage("Client Disconnected")
        self.lblPos.setText(str(status["position"]))
        if len(status["error"]) > 1:
            self.lblErr.setStyleSheet("background-color: indianred; border-radius: 10px;")
        else:
            self.lblErr.setStyleSheet("background-color: rgb(119, 118, 123); border-radius: 10px;")
        if status["ismoving"]:
            self.lblMov.setStyleSheet("background-color: green; border-radius: 10px;")
        else:
            self.lblMov.setStyleSheet("background-color: rgb(119, 118, 123); border-radius: 10px;")
    
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
    main_app = QtWidgets.QApplication(sys.argv)
    window = FocuserOPD()
    
    window.show()
    sys.exit(main_app.exec_())

    
    
    
