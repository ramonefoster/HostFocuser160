import serial
import serial.tools.list_ports

from threading import Lock
from threading import Timer

import time
import os

class Focuser():
    def __init__(self):  
        self._lock = Lock()
        self.name: str = 'LNA Focuser'
       
        self._step_size: float = 1.0
       
        self._reverse = False
        self._absolute = True
        self._max_step = 20000
        self._max_increment = 300
        self._is_moving = False
        self._connected = False
       
        self._temp_comp = False
        self._temp_comp_available = False
        self._temp = 0.0
        self._steps_per_sec = 1

        self._position = 0
        self._tgt_position = 0
        self._stopped = True

        self._serial = None
        self._timeout = 1

        self._timer: Timer = None
        self._interval: float = 1.0 / self._steps_per_sec

        self._ports()
   
    def _ports(self):
        self.list = serial.tools.list_ports.comports()
        coms = []
        for element in self.list:
            print(f"Port: {element.device}, Description: {element.description}")
            coms.append(element.device)

        return(coms)
    
    def get_serial_port():
        if os.name == 'posix':  # Linux
            return '/dev/ttyUSB0'  # Change this to the appropriate device name for your system
        elif os.name == 'nt':  # Windows
            return 'COM1'  # Change this to the appropriate COM port for your system
        else:
            raise OSError("Unsupported operating system for serial communication")

    @property
    def connected(self):
        self._lock.acquire()
        res = self._connected
        self._lock.release()
        return res
    @connected.setter
    def connected(self, connected: bool):
        print("Connecting")
        self._lock.acquire()
        self._connected = connected
        if connected:            
            self._serial = serial.Serial(
                port='/dev/ttyUSB0',
                baudrate='9600',                
                timeout=self._timeout
            )
            self._serial.close()
            if not self._serial.is_open:
                try:
                    self._serial.open()
                    self._serial.flush()
                    time.sleep(1)
                except:
                    self._connected = False
                    raise RuntimeError('Cannot Connect')
            self._lock.release()
            print("Connected")
        elif not connected:
            self._lock.release()
            self.disconnect()       
   
    def disconnect(self):
        self._lock.acquire()
        if self._serial.is_open:
            try:
                self._serial.close()
            except:
                raise RuntimeError('Cannot disconnect')
        self._lock.release()
   
    def start(self, from_run: bool = False) -> None:
        #print('[start]')
        self._lock.acquire()
        #print('[start] got lock')
        if from_run or self._stopped:
            self._stopped = False
            #print('[start] new timer')
            self._timer = Timer(self._interval, self._run)
            #print('[start] now start the timer')
            self._timer.start()
            #print('[start] timer started')
            self._lock.release()
            #print('[start] lock released')
        else:
            self._lock.release()
            #print('[start] lock released')
   
    def _run(self) -> None:
        #print('[_run] (tmr expired) get lock')
        self.position
        self._lock.acquire()
        delta = self._tgt_position - self._position
        self._lock.release()
        #print(f'[_run] final delta={str(delta)}')
        if delta != 0:
            self.position
            self._lock.acquire()
            #self._is_moving = True
            self._lock.release()
        else:
            self._lock.acquire()
            #self._is_moving = False
            self._stopped = True
            self._lock.release()
        #print('[_run] lock released')
        if self._is_moving:
            #print('[_run] more motion needed, start another timer interval')
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
    def position(self) -> int:
        max_retries = 3  
        retries = 0
        while retries < max_retries:
            try:
                self._lock.acquire()
                self._position = int(self._write("P\n"))
                self._lock.release()
                #print(f"[position] {self._position}")
                return self._position
            except ValueError as e:
                # Handle the ValueError (or other exceptions) here
                retries += 1  
                self._lock.release()
       
        return -1        
   
    @property
    def is_moving(self) -> bool:
        self._lock.acquire()
        self.is_running = self._write("R\n")
        if self.is_running == '0':            
            self._is_moving = False
        elif self.is_running == '1':
            self._is_moving = True
        else:
            self._is_moving= False
        res = self._is_moving
        self._lock.release()
        return res
   
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

    def move(self, position: int):
        self._lock.acquire()        
        if self._is_moving == '1':
            self._lock.release()
            raise RuntimeError('Cannot start a move while the focuser is moving')
        if position > self._max_step:
            raise RuntimeError('Invalid Steps')
        if self._temp_comp:
            raise RuntimeError('Invalid TempComp')
        self._tgt_position = position
        resp = self._write(f"M{position}\n")
        c = 0
        while not resp:
            if c >= 5:
                self._is_moving = True
            c += 1    
            resp = bool(self._write(f"M{position}\n"))  
        self._is_moving = bool(resp)
        #print('[move]', self._is_moving)
        self._lock.release()
        self.start()

    def stop(self) -> None:
        self._lock.acquire()
        #print('[stop] Stopping...')
        self._stopped = True
        self._is_moving = False
        if self._timer is not None:
            self._timer.cancel()
        self._timer = None
        self._lock.release()      
   
    def Halt(self) -> None:
        self._write(f"S\n")
        self.stop()        
   
    def _write(self, cmd):
        if self._serial.is_open:
            try:    
                time.sleep(.05)            
                self._serial.write(bytes(cmd, 'utf-8'))
                ack = self._serial.readline().decode('utf-8').rstrip()                            
                return ack
            except Exception as e:
                print("Error writing COM: "+ str(e))
                return "Error"
        else:
            return "Not Open"