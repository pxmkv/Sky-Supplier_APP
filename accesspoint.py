import network
import socket
import time
import gc
from machine import UART, Pin
import micropyGPS
import json

# Configure ESP32 as an Access Point
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

