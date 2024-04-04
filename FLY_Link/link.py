from machine import UART
from time import sleep
uart = UART(1, baudrate=115200, tx=14, rx=34)
uart.init(115200, bits=8, parity=None, stop=1) # init with given parameters
while True:
    a=uart.read()
    if a is not None:
        print ((a.decode().strip()))    
        sleep(0.05)