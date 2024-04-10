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
import json

# Configure ESP32 as an Access Point
ssid = 'Cyberpot_Setup'
password = '88888888'
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=ssid, password=password, authmode=3)
uart = UART(1, baudrate=9600, tx=14, rx=34)  # Update pins according to your hardware setup
my_gps = micropyGPS.MicropyGPS()
gps_data = "data"

STRINGS_FILE = 'user_strings.dat'
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

i2c = I2C(sda=Pin(21), scl=Pin(22))
display = ssd1306.SSD1306_I2C(128, 64, i2c)
btn   = Pin(35,Pin.IN,Pin.PULL_UP)




btn   = Pin(35,Pin.IN,Pin.PULL_UP)

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
buf=['WIFI','88888888','','','','']

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
    uptime_seconds = time.ticks_ms() / 1000
    free_memory = gc.mem_free()
    gps_data = get_packet()
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
            <p>GPS Data: {gps_data}</p>  <!-- Display GPS data -->
            <form action="/submit" method="post">
                <input type="radio" id="option1" name="data" value="1" {'checked' if last_option == '1' else ''}><label for="option1">Option 1</label><br>
                <input type="radio" id="option2" name="data" value="2" {'checked' if last_option == '2' else ''}><label for="option2">Option 2</label><br>
                <input type="radio" id="option3" name="data" value="3" {'checked' if last_option == '3' else ''}><label for="option3">Option 3</label><br>
                <input type="submit" value="Submit">
            </form>
            <p>Last Selected Option: {last_option}</p>
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
    send_response(client, "<html><script>window.location = '/';</script></html>")

def start_server():
    setup_server()
    while True:
        client, addr = server_socket.accept()
        request = client.recv(1024).decode('utf-8')
        if request.startswith('POST /submit'):
            handle_submit(client, request)
        else:
            handle_root(client, request)
        client.close()

def get_packet():
    if uart.any():
        my_sentence = uart.readline().decode('utf-8')
        for x in my_sentence:
            my_gps.update(x)
            

        # Check if the data is valid
        if my_gps.valid:
            return str([my_gps.timestamp, convert_to_decimal(my_gps.latitude), convert_to_decimal(my_gps.longitude)])
            
        else:
            sample = [37, 52.51906, 'N']
            
            print("Waiting for GPS fix...")
            return ""
            # print("Raw GPS data:", my_sentence)
            #print(convert_to_decimal(sample))
            #print_size_in_kb(sample)
            #print_size_in_kb(convert_to_decimal(sample))

        # Optional: Log GPS data
        # my_gps.start_logging('gps_log.txt')
        # my_gps.write_log(my_sentence)
        # my_gps.stop_logging()

    else:
        print("No data from GPS module.")
        return ""

def convert_to_decimal(loc):
    decimal = loc[0] + loc[1] / 60
    if loc[2] in ['S', 'W']:
        decimal = -decimal
    return decimal

def send_location():
    while True:
        lora.send(str(gps_data))
        print('lora sent')
        lora.recv()
        sleep(2)

def callback(pack):
    global t_mode,buf, data,last_pack_time, last_rssi
    print('lora_pack',pack)
    try:
        tmp=json.loads(pack.decode())
        data = tmp
        print("lora recv callback")
        print(data)
        last_rssi=str(max(-lora.get_rssi()-43,0))
    except Exception as e:
        print(f"Error processing input: {e}")
    t_mode=True
    last_pack_time=time.ticks_ms()//1000

def print_messages(thread_name, delay):
    count = 0
    while count < 5:  # Each thread prints 5 messages and then stops
        sleep(delay)
        count += 1
        print(f"{thread_name}: {count}")




if __name__ == "__main__":
    lora.on_recv(callback)
	# Start thread 1

    _thread.start_new_thread(setup_server, ())
    send_location()
    
    # _thread.start_new_thread(send_location, ())


