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
        self._tgt_position = 0
        self._stopped = True
        self._homing = False
        self._at_home = False

        self._timeout = 1

        self._timer: Timer = None
        self._interval: float = 1.0 / self._steps_per_sec

        self._model_step = np.array([0, 1200, 1800, 2500, 3500, 5000, 7000, 
                                     10000, 13000, 16000, 20000, 24500, 29000, 
                                     31250, 36870, 40000, 43000, 45000, 50000, 57000, 
                                     61000, 66000, 70000, 75000, 78500, 80000, 82000, 84000])
        self._model_microns = np.array([0, 5, 27, 46, 55, 79, 111, 171, 236, 
                                        282, 334, 395, 489, 517, 609, 661, 
                                        708, 732, 817, 911, 985, 1074, 1134, 
                                        1230, 1280, 1276, 1324, 1331])
        self._interp_func = interp1d(self._model_step, self._model_microns, kind='linear')

    @property
    def connected(self):
        self._lock.acquire()
        res = self._connected
        self._lock.release()
        return res
    @connected.setter
    def connected(self, connected: bool, max_retries=3, delay=.1):
        self._lock.acquire()
        self._connected = connected
        if connected:
            self._lock.release()
            retries = 0
            connected_successfully = False

            while retries < max_retries and not connected_successfully:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                        client_socket.connect((Config.device_ip, Config.device_port))
                    time.sleep(0.1)
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
        self._lock.acquire()
        if self._connected:
            try:
                pass
            except:
                raise RuntimeError('Cannot disconnect')
        self._lock.release()
    
    def start(self, from_run: bool = False) -> None:
        print('[start]')
        self._lock.acquire()
        print('[start] got lock')
        if from_run or self._stopped:
            self._stopped = False
            print('[start] new timer')
            self._timer = Timer(self._interval, self._run)
            print('[start] now start the timer')
            self._timer.start()
            print('[start] timer started')
            self._lock.release()
            print('[start] lock released')
        else:
            self._lock.release()
            print('[start] lock released')
    
    def _run(self) -> None:
        print('[_run] (tmr expired) get lock')
        if not self._is_moving:
            self._stopped = True
        print('[_run] lock released')
        if self._is_moving:
            print('[_run] more motion needed, start another timer interval')
            self.start(from_run = True)
    
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
        res = self._temp_comp

    @property
    def position(self, max_retries = 2) -> int:          
        retries = 0
        while retries < max_retries:
            try:
                self._lock.acquire()
                step = int(self._write("EX")) 
                y_interp = int(self._interp_func(step))
                self._position = y_interp
                self._lock.release()
                return self._position
            except ValueError as e:
                self.logger.error(f'[Device] Error reading position: {str(e)}')
                retries += 1  
                self._lock.release()  
                time.sleep(.05)       
        return 0        
    
    @property
    def is_moving(self) -> bool:
        self._lock.acquire()
        x = self._write("V46")
        if "1" in x:
            self._is_moving = True
        elif "0" in x:
            self._is_moving = False        
        self._lock.release()
        res = self._is_moving
        return res

    @property
    def homing(self) -> bool:
        self._lock.acquire()
        x = self._write("V44")
        if "0" in x:
            self._homing = True
        else:
            self._homing = False
        res = self._homing
        self._lock.release()
        return res

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
    
    def home(self, max_retries=3, delay=0.1):
        if self._is_moving:
            raise RuntimeError('Cannot start a move while the focuser is moving')

        retries = 0
        while retries < max_retries:
            res = self._write("GS30")
            if res == 'OK':
                self.start()
                self.logger.info('[Device] home: Success')
                return res  # Command executed successfully
            else:
                retries += 1
                time.sleep(delay)  # Wait for some time before retrying

        self.logger.error('[Device] home: Failed after retries')
        return res      

    def move(self, position: int, max_retries=3, delay=.05):        
        self._lock.acquire()        
        if self._is_moving:
            self._lock.release()
            raise RuntimeError('Cannot start a move while the focuser is moving')
        if position > self._max_step:
            raise RuntimeError('Invalid Steps')
        if self._temp_comp:
            raise RuntimeError('Invalid TempComp')
        self._tgt_position = position 
        retries = 0
        while retries < max_retries:
            resp = self._write(f"V20={position}")
            if "OK" in resp:
                print('[move]', resp)
                self._write(f"GS29")
                self.logger.info(f'[Device] move={str(position)}')
                self._lock.release() 
                self.start() 
                return
            else:
                retries += 1
                self._lock.release() 
                time.sleep(delay)
                return

    def stop(self) -> None:
        self._lock.acquire()
        print('[stop] Stopping...')        
        self._is_moving = False
        self._stopped = True
        if self._timer is not None:
            self._timer.cancel()
        self._timer = None
        self._lock.release()      
    
    def Halt(self, max_retries=3, delay=.05) -> None:        
        retries = 0
        while retries < max_retries:
            resp_stop = self._write("STOP")
            if resp_stop == 'OK':
                self._write("GS0=0")
                self.logger.info('[Device] halt')
                self.stop()
                return True  # Command executed successfully
            else:
                retries += 1
                time.sleep(delay)  # Wait for some time before retrying

        return False        
    
    def _write(self, cmd):
        if self._connected:
            time.sleep(.25)
            try:   
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                    client_socket.connect((Config.device_ip, Config.device_port)) 
                    cmd = f'{cmd}\x00'
                    client_socket.sendall(bytes(cmd, 'utf-8'))
                    # Check if there is data available to read without blocking
                    ready = select.select([client_socket], [], [], 0.1)  # Timeout set to 1 second
                    if ready[0]:
                        response = client_socket.recv(1024)                         
                        return response.decode('utf-8').replace("\x00", "")  
                    print("timeout")
                    self.logger.error(f"[Device] Connection timeout")
                    return "Timeout"  # No response received within the timeout
            except Exception as e:
                self.logger.error(f"[Device] Error writing to device: {str(e)}")
                print("Error writing ETH: "+ str(e))
                return "Error"
        else:
            return "Not Open"