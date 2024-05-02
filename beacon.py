import os
import time
import urandom
import micropyGPS
import json
import uasyncio as asyncio
from machine import Pin,I2C,SPI,UART
import ssd1306
import _thread
import network
import socket
from time import sleep
from lora import LoRa
import math
import machine

#TODO
#auto refresh


# Configure ESP32 as an Access Point
ssid = 'BEACON'
password = '88888888'
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=ssid, password=password, authmode=3)
uart = UART(1, baudrate=9600, tx=14, rx=34)  # Update pins according to your hardware setup
my_gps = micropyGPS.MicropyGPS()
gps_data = [[13, 50, 25.0], 37.87276, -122.26082]
#gps_data = ['no fix'] # moffit
last_option = 0
direction = [0, 0, 0] # only for drone
refresh_rate = "5"

STRINGS_FILE = 'user_strings.dat'
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

i2c = I2C(sda=Pin(21), scl=Pin(22))
display = ssd1306.SSD1306_I2C(128, 64, i2c)
btn = Pin(35,Pin.IN,Pin.PULL_UP)

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
buf=[ssid,'88888888','192.168.4.1','','','']

#id = '-'.join([
#    unique_id[4:6].hex()])
id = 'bcn'

packs = {
    'bcn': [[[13, 50, 25.0], 37.87276, -122.26082], 'bcn', 0, [0, 0, 0], 0],
    'drn': [[[13, 50, 25.0], 37.87431, -122.25934], 'drn', -1, [0, 0, 0], 0],
    'gnd': [[[13, 50, 25.0], 37.87431, -122.25934], 'gnd', -1, [0, 0, 0], 0],
}

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



def setup_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    server_socket.bind(addr)
    server_socket.listen(1)
    print('Listening on:', addr)

def send_response(client, payload, status_code=200, content_type="text/html"):
    client.send("HTTP/1.1 {} OK\r\nContent-Type: {}\r\nConnection: close\r\nContent-Length: {}\r\n\r\n{}".format(status_code, content_type, len(payload), payload))

def read_last_option():
    try:
        with open(STRINGS_FILE, 'r') as file:
            return file.read().strip()
    except OSError:
        return ""

def handle_root(client, request):
    
    last_option = read_last_option()
    packs['bcn'][2] = last_option
    uptime_seconds = time.ticks_ms() / 1000
    free_memory = gc.mem_free()
    gps_data = get_packet()
    if gps_data != '':
        packs[id][0] = gps_data
    dist = haversine(packs['bcn'], packs['drn'])
    html_content = f"""
    <html>
        <head>
            <title>ESP32 Uptime & Option Select</title>
            <meta http-equiv="refresh" content="5">
        </head>
        <body>
            <h1>ESP32 Uptime & GPS Info</h1>
            <p>Uptime: {uptime_seconds:.2f} seconds</p>
            <p>Free Memory: {free_memory} bytes</p>
            <p>Distance: {dist} meters</p>  <!-- Display Beacon to Drone -->
            <form action="/submit" method="post">
                <input type="radio" id="option1" name="data" value="1" {'checked' if last_option == '1' else ''}><label for="option1">Option 1</label><br>
                <input type="radio" id="option2" name="data" value="2" {'checked' if last_option == '2' else ''}><label for="option2">Option 2</label><br>
                <input type="radio" id="option3" name="data" value="3" {'checked' if last_option == '3' else ''}><label for="option3">Option 3</label><br>
                <input type="submit" value="Submit">
            </form>
            <p>Package Type: {last_option}</p>
        </body>
    </html>
    """
    send_response(client, html_content)

def handle_submit(client, request):
    post_data = request.split('\r\n\r\n', 1)[1]
    option = post_data.split('=')[1]
    print("Selected Option ", option)
    with open(STRINGS_FILE, 'w') as file:
        file.write(option)
    gc.collect()

    # Send a response redirecting to the landing page
    redirect_response = "HTTP/1.1 303 See Other\r\nLocation: /landing_page\r\n\r\n"
    client.send(redirect_response)
    client.close()

def handle_landing_page(client, request):
    # Create a simple HTML for the landing page
    last_option = read_last_option()
    packs['bcn'][2] = last_option
    uptime_seconds = time.ticks_ms() / 1000
    free_memory = gc.mem_free()
    gps_data = get_packet()

    if gps_data != '':
        packs[id][0] = gps_data
    print("before dist")
    dist = haversine(packs['bcn'], packs['drn'])
    print("dist")
    print(dist)
    html_content = f"""
    <html>
        <head>
            <title>ESP32 Uptime & Option Select</title>
            <meta http-equiv="refresh" content="1">
        </head>
        <body>
            <h1>ESP32 Uptime & GPS Info</h1>
            <p>Uptime: {uptime_seconds:.2f} seconds</p>
            <p>Free Memory: {free_memory} bytes</p>
            <p>Distance: {dist} meters</p>  <!-- Display Beacon to Drone -->
            <p>Package Type: {last_option}</p>
        </body>
    </html>
    """
    send_response(client, html_content)

def start_server():
    print("Server thread started")
    try:
        setup_server()
        print("Server bound to address and listening...")
        while True:
            #print("Waiting for a connection...")
            client, addr = server_socket.accept()
            print(f"Connection from {addr}")
            request = client.recv(1024).decode('utf-8')
            if request:
                print(f"Received request: {request}")
                path = request.split(' ')[1]
                if path == '/submit':
                    handle_submit(client, request)
                elif path == '/landing_page':
                    handle_landing_page(client, request)
                else:
                    handle_root(client, request)
            client.close()
            #print("Client connection closed.")
    except Exception as e:
        print(f"Exception in server thread: {e}")



def get_packet():
    if uart.any():
        my_sentence = uart.readline().decode('utf-8')
        buf[4] = my_sentence 
        disp()
        for x in my_sentence:
            my_gps.update(x)

        # Check if the data is valid
        if my_gps.valid:
            return [my_gps.timestamp, convert_to_decimal(my_gps.latitude), convert_to_decimal(my_gps.longitude)]
            
        else:
            sample = [[13, 50, 25.0], 37.8752, -122.2577, 0]
            
            buf[3] = "no fix" 
            disp()
            return [[13, 50, 25.0], 37.87276, -122.26082]
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
    interval = 1
    last_log = 0	
    print('send location')
    while True:
    	if (time.time() - last_log) > interval:
	    gps_data = get_packet()
	    if gps_data != '':
	        packs[id][0] = gps_data
            lora.send(str(packs[id]))
            print('lora sent')
            print(str(packs[id]))
            last_log = time.time()
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
            
        
        # Update the last RSSI value
        last_rssi = str(max(-lora.get_rssi()-43, 0))
    except Exception as e:
        print(f"Error processing input: {e}")


def print_messages(thread_name, delay):
    count = 0
    while count < 5:  # Each thread prints 5 messages and then stops
        sleep(delay)
        count += 1
        print(f"{thread_name}: {count}")

def haversine(coord1, coord2):
    # Radius of the Earth in km
    R =  6378137.0
    # Extract latitude and longitude from the coordinates
    lat1, lon1 = coord1[0][1], coord1[0][2]
    lat2, lon2 = coord2[0][1], coord2[0][2]
    

    # Convert coordinates from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Difference in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c 
    return distance

#_thread.start_new_thread(threaded_server, ())
#start_server()
#_thread.start_new_thread(print_messages, ("Thread-1", 1))



#if id != '3984':
#print("setting up server")



if __name__ == "__main__":
    lora.on_recv(callback)
    _thread.start_new_thread(start_server, ())
    lora.recv()
    send_location()


