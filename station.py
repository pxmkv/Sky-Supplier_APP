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


#config
# sd = SDCard(slot=3)  # sck=18, mosi=23, miso=19, cs=5
# os.mount(sd, "/sd")
i2c = I2C(sda=Pin(21), scl=Pin(22))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

display.invert(1)

display.text("  OUTDOOR", 0, 10, 1)
display.text("      GUARDIAN", 0, 20, 1)
display.text("    Group 6", 0, 50, 1)
display.show()

btn   = Pin(35,Pin.IN,Pin.PULL_UP)



# Initialize GPS
uart = UART(1, baudrate=9600, tx=14, rx=34)  # Update pins according to your hardware setup
my_gps = micropyGPS.MicropyGPS()
data = [[13, 50, 25.0], 37.8752, -122.2577]#cory
last_saved= [[13, 50, 25.0], 37.8728, -122.2609]#moffit
# last_saved= [[13, 50, 25.0], 37.8760, -122.2601]#bollywood cafe




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


def disp():
    display.fill(0)
    display.text(buf[0], 0, 0, 1)
    display.text(buf[1], 0, 10, 1)
    display.text(buf[2], 0, 20, 1)
    display.text(buf[3], 0, 30, 1)
    display.text(buf[4], 0, 40, 1)
    display.text(buf[5], 0, 50, 1)
    display.show()

has_message=False    


def haversine(coord1, coord2):
    # Radius of the Earth in km
    R =  6378137.0
    # Extract latitude and longitude from the coordinates
    lat1, lon1 = coord1[1], coord1[2]
    lat2, lon2 = coord2[1], coord2[2]

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


    
def convert_to_decimal(loc):
    decimal = loc[0] + loc[1] / 60
    if loc[2] in ['S', 'W']:
        decimal = -decimal
    return decimal


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False



def get_packet():
    global last_saved
    try:    
        if uart.any():
            my_sentence = uart.readline().decode('utf-8')
            for x in my_sentence:
                my_gps.update(x)
            # Check if the data is valid
            if my_gps.valid:
                last_saved = [my_gps.timestamp, convert_to_decimal(my_gps.latitude), convert_to_decimal(my_gps.longitude)]
            else:        
                print("Waiting for GPS fix...")
        else:
            print("No data from GPS module.")
    except Exception as e:
        print(f"Error processing input: {e}")
    return last_saved

t_mode=False #tracking mode

buf=['PRESS TO SPEAK','','','','','']
last_pack_time = 0
last_rssi=''

def callback(pack):
    global t_mode,buf, data,last_pack_time, last_rssi
    print('lora_pack',pack)
    try:
        tmp=json.loads(pack.decode())
        data = tmp
        last_rssi=str(max(-lora.get_rssi()-43,0))
    except Exception as e:
        print(f"Error processing input: {e}")
    t_mode=True
    last_pack_time=time.ticks_ms()//1000

def send_location():
    display.invert(1)
    buf[3]='EMERGENCY'
    buf[4]='     MODE'
    disp()
    while True:
        lora.send(str(get_packet()))
        print('lora sent')
        sleep(0.5)






ssid = 'Cyberpot_Setup'
password = '88888888'
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=ssid, password=password, authmode=3)
uart = UART(1, baudrate=9600, tx=17, rx=16)  # Update pins according to your hardware setup
my_gps = micropyGPS.MicropyGPS()


STRINGS_FILE = 'user_strings.dat'
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)





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


start_server()









# lora.on_recv(callback)
# def main():
#     global buf
#     while True:
#         while True:
#             if t_mode:    
#                 break
#             if heart.available() :
#                 ir  = heart.pop_ir_from_storage()
#                 if ir < 10000 or ir > 20000:
#                     send_location()
#             sleep(1)
#         #tracking mode
#         packs=get_packet()
#         buf[2] = 'Dist ' + str(haversine(packs, data)) +' m'
            
#         # buf[4] = "Compass " + str(compass.calculate_heading())
#         # buf[5] = "Bearing " + str(calculate_bearing(packs, data) )


#         buf[4] = 'Lora Dist ' + last_rssi 
#         time_diff=time.ticks_ms()//1000-last_pack_time
#         buf[5]='RECD ' +str(time_diff) + 's ago'# update buffer
#         disp() # show display
#         sleep(0.2)#update every 0.2 second


sleep(3)
display.invert(0)
disp()


lora.on_recv(callback)
lora.recv() #lora recv thread
# audio_s_thread = _thread.start_new_thread(send_audio,())
# audio_r_thread = _thread.start_new_thread(recv_audio,())
if __name__ == '__main__': # main thread
    main()






