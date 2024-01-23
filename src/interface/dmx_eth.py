from logging import Logger

from threading import Lock
from threading import Timer

from src.core.config import Config

import socket
import select
import time

from scipy.interpolate import interp1d
import numpy as np

class FocuserDriver():
    def __init__(self, logger: Logger):  
        self._lock = Lock()
        self.name: str = 'LNA Focuser'
        self.logger = logger

        self.motor_socket = None
        
        self._step_size: float = 1.0
        
        self._reverse = False
        self._absolute = True
        self._max_step = Config.max_step
        self._max_increment = 100
        self._is_moving = False
        self._connected = False
        self._status = ""
        
        self._temp_comp = False 
        self._temp_comp_available = False
        self._temp = 0.0 
        self._steps_per_sec = 1

        self._position = 0
        self._last_pos = 0
        self._tgt_position = 0
        self._stopped = True
        self._homing = False
        self._at_home = False
        self._initialized = False
        self._alarm = 0

        self._timeout = 1

        self._timer: Timer = None
        self._interval: float = .15

        self._model_step = np.array([0, 1000, 1500, 2500, 4000, 5900, 8500, 
                                     12000, 15000, 18000, 22000, 27000, 32000, 
                                     38000, 45000, 55000, 65000, 75000, 84000])
        self._model_microns = np.array([0, 3, 18, 46, 52, 109, 146, 204, 
                                        149, 289, 377, 447, 539, 631, 736, 
                                        908, 1064, 1233, 1333])
        self._interp_func = interp1d(self._model_step, self._model_microns, kind='linear')

    @property
    def connected(self):
        self._lock.acquire()
        res = self._connected
        self._lock.release()
        return res
    @connected.setter
    def connected(self, connected: bool, max_retries=3, delay=.1):
        """Connects the device and open socket connection
        Args:
            connected (bool): Sets the connected state
            max_retries (int): Number os tries if first one fail
            delay (float): Small delay, in seconds, to wait after a try
        """
        self._lock.acquire()
        self._connected = connected
        if connected:
            self._lock.release()
            retries = 0
            connected_successfully = False

            while retries < max_retries and not connected_successfully:
                try:
                    self.motor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.motor_socket.connect((Config.device_ip, Config.device_port))                    
                    time.sleep(delay)
                    connected_successfully = True
                except Exception as e:
                    self.logger.error(f'Connection attempt {retries + 1} failed: {e}')
                    retries += 1
                    time.sleep(delay)

            if not connected_successfully:
                self._lock.acquire()
                self._connected = False
                self._lock.release()
                self.logger.error('Failed to establish a connection after retries')
                raise RuntimeError('Cannot Connect')

        else:
            self._lock.release()
            self.disconnect()

        if self._connected:
            self.logger.info('[Connected]')
        else:
            self.logger.info('[Disconnected]')
    
    def disconnect(self):
        """Disconnects device and close socket"""
        self._lock.acquire()
        if self._connected:
            try:
                self.motor_socket.close()
            except:
                raise RuntimeError('Cannot disconnect')
        self._lock.release()
    
    # def start(self, from_run: bool = False) -> None:
    #     print('[start]')
    #     self._lock.acquire()
    #     if from_run or self._stopped:
    #         self._stopped = False
    #         self._timer = Timer(self._interval, self._run)
    #         self._timer.start()
    #         self._lock.release()
    #         print('[start] lock released')
    #     else:
    #         self._lock.release()
    #         print('[start] lock released')
    
    # def _run(self) -> None:
    #     if not self._is_moving:
    #         self._stopped = True
    #     print('[_run] lock released')
    #     if self._is_moving:
    #         print('[_run] more motion needed, start another timer interval')
    #         self.start(from_run = True)
    
    @property
    def temp(self):
        self._lock.acquire()
        res = self._temp
        self._lock.release()
        return res
    
    @property
    def temp_comp_available(self):
        self._lock.acquire()
        res = self._temp_comp_available
        self._lock.release()
        return res
    
    @property
    def temp_comp(self):
        self._lock.acquire()
        res = self._temp_comp
        self._lock.release()
        return res
    @temp_comp.setter
    def temp_comp(self, temp: bool):
        self._lock.acquire()
        if not self._temp_comp_available and temp:
            self._temp_comp = False
        elif self._temp_comp_available:        
            self._temp_comp = temp
        self._lock.release()

    @property
    def position(self) -> int:    
        """Device enconders position"""      
        try:
            self._lock.acquire()
            step = int(self._write("EX", max_retries=3)) 
            # if step >= 0:
            #     conv_position = int(self._interp_func(step))
            # elif step < 0:
            #     conv_position = round(step*0.0162)
            #     self._homing = True
            # else:
            #     return self._last_pos
            # self._position = conv_position
            self._position = int(round(step/Config.enc_2_microns))
            self._last_pos = self._position
            self._lock.release()
            return self._position
        except ValueError as e:
            self.logger.error(f'[Device] Error reading position: {str(e)}')
            self._lock.release()  
        return self._last_pos        
    
    @property
    def is_moving(self) -> bool:
        """Checks if device is moving"""
        self._lock.acquire()
        x = self._write("V46", max_retries=3)
        if x == "1":
            self._is_moving = True
            self._lock.release()
            return self._is_moving
        elif x == "0":
            self._is_moving = False 
            self._lock.release()
            return self._is_moving          
        self._lock.release()
        return self._is_moving

    @property
    def homing(self) -> bool:
        """Check if INIT routine is being executed"""
        self._lock.acquire()
        x = self._write("V44", max_retries=3)
        if "0" in x:
            self._homing = True
        else:
            self._homing = False
        self._lock.release()
        return self._homing
    
    @property
    def initialized(self) -> bool:
        """Checks if initialization was previously executed"""
        self._lock.acquire()
        x = self._write("V44", max_retries=3)
        if "64" in x:
            self._initialized = True
        else:
            self._initialized = False
        self._lock.release()
        return self._initialized

    @property
    def get_status(self) -> str:
        self._lock.acquire()
        self._status = self._write("GS0")
        self._lock.release()
        return self._status
    
    @property
    def absolute(self) -> bool:  
        self._lock.acquire()      
        res = self._absolute
        self._lock.release()
        return res

    @property
    def max_increment(self) -> bool:
        self._lock.acquire()
        res = self._max_increment
        self._lock.release()
        return res

    @property
    def max_step(self) -> bool:
        self._lock.acquire()
        res = self._max_step
        self._lock.release()
        return res

    @property
    def step_size(self) -> bool:
        self._lock.acquire()
        res = self._step_size
        self._lock.release()
        return res
    
    @property
    def alarm(self) -> int:
        res = self._write("ALM", max_retries=3)
        try:
            self._alarm = int(res)
            if self._alarm == '1':
                self.logger.info('[Device] Temperature Alarm ON')
        except Exception as e: 
            self._alarm = 0
            self.logger.error(f'[Device] Alarm Error {str(e)}')
        
        return self._alarm

    def home(self):
        """Executes the INIT routine        
        Returns: 
            Device response or Error message
        Raises:
            RuntimeError if device is busy
        """      
        if self._is_moving:
            raise RuntimeError('Cannot start a move while the focuser is moving')

        res = self._write("GS30", max_retries=3)
        if res == 'OK':
            self.logger.info('[Device] home: Success')
            return res  
        else:
            alarm = self.alarm()
            if alarm == 1:
                self.logger.error('[Device] home: Failed and Alarm flag is up')

        self.logger.error('[Device] home: Failed after retries')
        return res      

    def move(self, position: int):  
        """Moves device position to the given position
        Args:  
            position (int): Value in microns.
        Returns: 
            Device response or Error message
        Raises:
            RuntimeError if Invalid input or if device is busy
        """      
        pos_conv = int(round((Config.enc_2_microns * position), 0))
        if self._is_moving:
            raise RuntimeError('Cannot start a move while the focuser is moving')
        if 0 >= pos_conv >= self._max_step:
            raise RuntimeError('Invalid Steps')
        if self._temp_comp:
            raise RuntimeError('Invalid TempComp')        
        resp = self._write(f"V20={pos_conv}", max_retries=3)
        if "OK" in resp:            
            resp = self._write(f"GS29", max_retries=3)
            if "OK" in resp:
                self.logger.info(f'[Device] move={str(pos_conv)}')
                return
            else:
                alarm = self.alarm()
                if alarm == 1:
                    self.logger.error('[Device] Move Failed and Alarm flag is up')
                raise RuntimeError(f'Error: {resp}')
        else:
            self.alarm()
            raise RuntimeError(f'Error: {resp}') 

    def speed(self, vel: int):  
        """Sets the speed of the motor
        Args:  
            vel (int): speed value in rpm.
        Returns: 
            Device response or Error message
        Raises:
            RuntimeError if Invalid input or if device is busy
        """      
        pass
        # if self._is_moving:
        #     raise RuntimeError('Cannot set speed while the focuser is moving')
        # if 0 > vel >= self._max_speed:
        #     raise RuntimeError('Invalid Steps')        
        # resp = self._write(f"V20={vel}", max_retries=3)
        # if "OK" in resp: 
        #     self.logger.info(f'[Device] speed={str(vel)}')
        #     return            
        # else:
        #     raise RuntimeError(f'Error: {resp}')           

    def stop(self) -> None:
        self._lock.acquire()
        print('[stop] Stopping...')        
        self._is_moving = False
        self._stopped = True
        if self._timer is not None:
            self._timer.cancel()
        self._timer = None
        self._lock.release()      
    
    def Halt(self) -> None:   
        """Send command STOP and stops main program with GS0=0 subroutine"""     
        resp_stop = self._write("STOP", 5)
        if resp_stop == 'OK':            
            self.logger.info('[Device] halt')
            self.stop()
            return True  # Command executed successfully 
        return False        
    
    def _write(self, cmd, max_retries = 0):
        """Send commands to device socket.
        Args:  
            cmd (str): Command.
            max_retries (int): Number of retries if first one fails
        Returns: 
            Device response or Error message
        """
        retries = 0
        if self._connected:              
            while retries < max_retries:  
                try:   
                    self.motor_socket.sendall(bytes(f'{cmd}\x00', 'utf-8'))
                    response = self.motor_socket.recv(1024)
                    return response.decode('utf-8').replace("\x00", "")                    
                except Exception as e:
                    err = e
                retries += 1
            self.logger.error(f"[Device] Error writing {cmd}: {str(err)}")
            if "WinError" in err:
                self._connected = False
            # print(f"Error writing ETH: {cmd}: {str(err)}")
            return str(err)
        else:
            return "Not Connected"