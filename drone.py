import os
import time
import urandom
import micropyGPS
import json
import uasyncio as asyncio
from machine import Pin,I2C,SPI,UART, ADC, PWM
from micropython_servo_pdm_360 import ServoPDM360
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
import ssd1306




i2c = I2C(sda=Pin(21), scl=Pin(22))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

servo_pwm = PWM(Pin(25))
servo = ServoPDM360(pwm=servo_pwm, min_us=1000, max_us=2000, freq=50)


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
buf=['SKY_SUPPLIER','','','','','']

dropped = False

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

buf=['Sky Supplier','','','','','']

packs = {
    #id: [gps, id, package type, blockages, altitude, drop]
    #'bcn': [[[13, 50, 25.0], 37.87276, -122.26082, 0], 'bcn', -1, [0, 0, 0], 0],
    'bcn': [[[13, 50, 25.0], 37.87431, -122.25934], 'bcn', -1, [0, 0, 0], 0],
    'drn': [[[13, 50, 25.0], 37.87431, -122.25934], 'drn', -1, [0, 0, 0], 0],
    #'drn': [[[13, 50, 25.0], 37.87276, -122.26082, 0], 'drn', -1, [0, 0, 0], 0],
    'gnd': [[[12, 4, 34.0], 37.87439, -122.2594], 'gnd', -1, [0, 0, 0], 0, 0],
}




unique_id = machine.unique_id()

id = 'drn'


def disp():
    display.fill(0)
    display.text(buf[0], 0, 0, 1)
    display.text(buf[1], 0, 10, 1)
    display.text(buf[2], 0, 20, 1)
    display.text(buf[3], 0, 30, 1)
    display.text(buf[4], 0, 40, 1)
    display.text(buf[5], 0, 50, 1)
    display.show()
disp()

def read_distance(ir):
    adc_value = ir.read()
    voltage = (adc_value / ADC_RESOLUTION) * VOLTAGE_SUPPLY
    if voltage == 0:
        return float('inf')  # Avoid division by zero, return 'infinity' if no reading
    distance = 27.86 * (voltage ** -1.15)  # Example formula, might need calibration for accuracy
    return distance
    
def sensor_read():
    return [read_distance(ir_l),read_distance(ir_f),read_distance(ir_r)]




def read_distance(ir):
    adc_value = ir.read()
    voltage = (adc_value / ADC_RESOLUTION) * VOLTAGE_SUPPLY
    if voltage == 0:
        return str(False)  # Avoid division by zero, return 'infinity' if no reading
    distance = 27.86 * (voltage ** -1.15)  # Example formula, might need calibration for accuracy
    if distance < 30:
    	return 1
    else:
        return 0

def sensor_read():
    return [read_distance(ir_l),0,read_distance(ir_r)]


def get_packet():
    if uart.any():
        raw_data = uart.readline()
        try:
            # Attempt to decode without specifying error handling
            my_sentence = raw_data.decode('utf-8')
        except UnicodeError:
            # Handle the error by using a fallback or by handling the data as best as you can
            my_sentence = raw_data.decode('utf-8', 'ignore')  # Fallback decoding if the above fails
            print("Failed to decode data properly, ignoring errors.")

        buf[4] = my_sentence  # Display the GPS data on the screen
        disp()
        for x in my_sentence:
            my_gps.update(x)

        if my_gps.valid:
            packs[id][0] = [my_gps.timestamp, convert_to_decimal(my_gps.latitude), convert_to_decimal(my_gps.longitude)]
            return packs[id][0]
        else:
            buf[3] = "no fix"
            disp()
            return packs[id][0]  # Use the last known good coordinates if no fix available

    else:
        print("No data from GPS module.")
        return packs[id][0]  # Return last known good coordinates if no data available

def convert_to_decimal(loc):
    # This function assumes 'loc' is a tuple containing the degree, minute, and optionally the hemisphere ('N', 'S', 'E', 'W')
    degrees, minutes = loc[0], loc[1]
    decimal = degrees + minutes / 60
    if len(loc) > 2 and loc[2] in ['S', 'W']:  # Check hemisphere and adjust accordingly
        decimal = -decimal
    return decimal


def send_location():
    interval = 1
    last_log = 0	
    while True:
       if time.time() - last_log > interval:
           #packs[id][4] = mpl.altitude()
	   packs[id][3] = sensor_read()
	   gps_data = get_packet()
	   if gps_data != '':
	       packs[id][0] = gps_data
           lora.send(str(packs[id]))
           print('lora sent')
           print(str(packs[id]))
           last_log = time.time()
       lora.recv()
        
def callback(pack):
    global t_mode,buf, data,last_pack_time, last_rssi, dropped
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
        if data[1] == 'gnd' and data[5] == 1 and dropped == False:
            drop()
        if data[1] == 'gnd' and data[5] == 2:
            load()
           #dropped = True
        # Update the last RSSI value
        last_rssi = str(max(-lora.get_rssi()-43, 0))
    except Exception as e:
        print(f"Error processing input: {e}")
        

def load():
    print("dropping")
# Rotate forward
    servo.set_duty(2000)  # Adjust as needed
    sleep(4)  # Rotate for 2 seconds
# Stop the servo
    servo.set_duty(1500)  # Return to stop position
    sleep(3)
# Rotate backward
    servo.set_duty(1000)  # Adjust as needed
    sleep(2)  # Rotate for 2 seconds
# Stop the servo
    servo.set_duty(1500)  # Return to stop position
    # turn motor for set time

def drop():
    print("dropping")
# Rotate forward
    servo.set_duty(2000)  # Adjust as needed
    sleep(3)  # Rotate for 2 seconds
# Stop the servo
    servo.set_duty(1500)  # Return to stop position
    sleep(2)
# Rotate backward
    servo.set_duty(1000)  # Adjust as needed
    sleep(5)  # Rotate for 2 seconds
# Stop the servo
    servo.set_duty(1500)  # Return to stop position
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



