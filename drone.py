import os
import time
import urandom
import micropyGPS
import json
import uasyncio as asyncio
from machine import Pin,I2C,SPI,UART, ADC, PWM
import ssd1306
import _thread
import network
import socket
from time import sleep
from lora import LoRa
import math
import json
import machine
from mpl3115a2 import MPL3115A2
from machine import I2C, Pin, ADC

i2c_mpl = I2C(sda=Pin(21), scl=Pin(22)) 
mpl = MPL3115A2(i2c_mpl, mode=MPL3115A2.ALTITUDE)

servo = PWM(Pin(25), freq=50) 

VOLTAGE_SUPPLY = 3.3  # Voltage supplied to ADC
ADC_RESOLUTION = 4095  # For a 12-bit ADC

ir_l = ADC(Pin(36)) 
ir_l.width(ADC.WIDTH_12BIT)
ir_l.atten(ADC.ATTN_11DB)
ir_f = ADC(Pin(39)) 
ir_f.width(ADC.WIDTH_12BIT)
ir_f.atten(ADC.ATTN_11DB)
ir_r = ADC(Pin(35)) 
ir_r.width(ADC.WIDTH_12BIT)
ir_r.atten(ADC.ATTN_11DB)


#integrate altitude and etc



uart = UART(1, baudrate=9600, tx=14, rx=34)  # Update pins according to your hardware setup
my_gps = micropyGPS.MicropyGPS()
#gps_data = [[13, 50, 25.0], 37.8752, -122.2577, 0]
gps_data = [[13, 50, 25.0], 37.87276, -122.26082]
last_option = 0
direction = [0, 0, 0] # only for drone

STRINGS_FILE = 'user_strings.dat'
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)




# Lora initialization
# SPI pins
SCK  = 5
MOSI = 27
MISO = 19
CS   = 18
RX   = 26
# Setup SPI
spi = SPI(
    1,
    baudrate=10000000,
    sck=Pin(SCK, Pin.OUT, Pin.PULL_DOWN),
    mosi=Pin(MOSI, Pin.OUT, Pin.PULL_UP),
    miso=Pin(MISO, Pin.IN, Pin.PULL_UP),
)
spi.init()
# Setup LoRa

lora = LoRa(
    spi,
    cs=Pin(CS, Pin.OUT),
    rx=Pin(RX, Pin.IN),
    frequency=915.0,
    bandwidth=250000,
    spreading_factor=10,
    coding_rate=5,
)
print('setup')
buf=['WIFI','88888888','','','','']

packs = {
    # 'id': [[[timestamp], lat, lon], 'id', last option, [ir distance], altitude, drop],
    'bcn': [[[13, 50, 25.0], 37.87276, -122.26082], 'bcn', 0, [0, 0, 0], 0],
    'drn': [[[13, 50, 25.0], 37.87431, -122.25934], 'drn', -1, [0, 0, 0], 0],
    'gnd': [[[13, 50, 25.0], 37.87431, -122.25934], 'gnd', -1, [0, 0, 0], 0],
}




unique_id = machine.unique_id()

id = 'drn'

def read_distance(ir):
    adc_value = ir.read()
    voltage = (adc_value / ADC_RESOLUTION) * VOLTAGE_SUPPLY
    if voltage == 0:
        return float('inf')  # Avoid division by zero, return 'infinity' if no reading
    distance = 27.86 * (voltage ** -1.15)  # Example formula, might need calibration for accuracy
    return distance
    
def sensor_read():
    return [read_distance(ir_l),read_distance(ir_f),read_distance(ir_r),mpl.altitude(),mpl.temperature()]




def read_distance(ir):
    adc_value = ir.read()
    voltage = (adc_value / ADC_RESOLUTION) * VOLTAGE_SUPPLY
    if voltage == 0:
        return float('inf')  # Avoid division by zero, return 'infinity' if no reading
    distance = 27.86 * (voltage ** -1.15)  # Example formula, might need calibration for accuracy
    return distance > 30

def sensor_read():
    return [read_distance(ir_l),read_distance(ir_f),read_distance(ir_r)]


def get_packet():
    if uart.any():
        my_sentence = uart.readline().decode('utf-8')

        for x in my_sentence:
            my_gps.update(x)

        # Check if the data is valid
        if my_gps.valid:
            return str([my_gps.timestamp, convert_to_decimal(my_gps.latitude), convert_to_decimal(my_gps.longitude)])
            
        else:
            sample = [[13, 50, 25.0], 37.8752, -122.2577]
            
            #print("Waiting for GPS fix...")
            return [[13, 50, 25.0], 37.87431, -122.25934]
            # print("Raw GPS data:", my_sentence)
            #print(convert_to_decimal(sample))
            #print_size_in_kb(sample)
            #print_size_in_kb(convert_to_decimal(sample))
    else:
        print("No data from GPS module.")
        return ""

def convert_to_decimal(loc):
    decimal = loc[0] + loc[1] / 60
    if loc[2] in ['S', 'W']:
        decimal = -decimal
    return decimal

def send_location():
    interval = 500
    last_log = 0	
    while True:
       if time.time() - last_log > interval:
           packs[id][4] = mpl.altitude()
	   packs[id][3] = sensor_read()
	   gps_data = get_packet()
	   if gps_data != '':
	       packs[id][0] = gps_data
           lora.send(str(packs[id]))
       lora.recv()
        
def callback(pack):
    global t_mode,buf, data,last_pack_time, last_rssi
    print('lora_pack',pack)
    try:
        # Replace single quotes with double quotes for valid JSON
        corrected_string = pack.decode('utf-8').replace("'", '"')
        
        # Parse the JSON data
        tmp = json.loads(corrected_string)
        data = tmp
        print("lora recv callback")
        print(data)
        packs[data[1]] = data
        if data[1] == 'bcn':
            packs[data[1]][2] = data[1][2]
            with open(STRINGS_FILE, 'w') as file:
                file.write(option)
        if data[1] == 'gnd' and data[5] == 1:
           drop()
        # Update the last RSSI value
        last_rssi = str(max(-lora.get_rssi()-43, 0))
    except Exception as e:
        print(f"Error processing input: {e}")

def drop():
    print("dropping")
    servo.duty(20)
    sleep(2)
    servo.duty(80)
    sleep(2)
    # turn motor for set time

def print_messages(thread_name, delay):
    count = 0
    while count < 5:  # Each thread prints 5 messages and then stops
        sleep(delay)
        count += 1
        print(f"{thread_name}: {count}")




if __name__ == "__main__":
    print('main')
    lora.on_recv(callback)
    lora.recv()
    send_location()



