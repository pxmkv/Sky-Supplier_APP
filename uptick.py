import network
import socket
import time
import gc

# Configure ESP32 as an Access Point
ssid = 'Cyberpot_Setup'
password = '88888888'  # Consider a more secure password for production
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=ssid, password=password, authmode=3)  # Authmode 3 = WPA2-PSK

print('Access Point Started. SSID:', ssid)

# Web server socket setup
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
server_socket = socket.socket()
server_socket.bind(addr)
server_socket.listen(1)

print('Listening on:', addr)

def serve_client(client):
    request = client.recv(1024).decode('utf-8')
    if 'GET /uptime' in request:
        # Serve the uptime in JSON format
        response = '{{"uptime": {:.2f}, "free_memory": {}}}'.format(time.ticks_ms() / 1000, gc.mem_free())
        client.send('HTTP/1.1 200 OK\n')
        client.send('Content-Type: application/json\n')
        client.send('Connection: close\n\n')
        client.sendall(response)
    else:
        # Serve the main HTML page
        client.send('HTTP/1.1 200 OK\n')
        client.send('Content-Type: text/html\n')
        client.send('Connection: close\n\n')
        client.sendall(main_page())
    gc.collect()
    client.close()

def main_page():
    return """
        <html>
            <head>
                <title>ESP32 Uptime</title>
                <script>
                    function fetchUptime() {
                        fetch('/uptime')
                            .then(response => response.json())
                            .then(data => {
                                document.getElementById('uptime').innerText = 'Uptime: ' + data.uptime + ' seconds';
                                document.getElementById('memory').innerText = 'Free Memory: ' + data.free_memory + ' bytes';
                            });
                        setTimeout(fetchUptime, 1000);
                    }
                </script>
            </head>
            <body onload="fetchUptime()">
                <h1>ESP32 Uptime</h1>
                <p id="uptime">Uptime: 0 seconds</p>
                <p id="memory">Free Memory: 0 bytes</p>
            </body>
        </html>
    """

while True:
    client, addr = server_socket.accept()
    print('Client connected from', addr)
    serve_client(client)

