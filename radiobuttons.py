import network
import socket
import ure


# Configure ESP32 as an Access Point
ssid = 'Cyberpot_Setup'
password = '88888888'  # Consider a more secure password for production
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=ssid, password=password, authmode=3)  # Authmode 3 = WPA2-PSK

# File to store user strings
STRINGS_FILE = 'user_strings.dat'

server_socket = None



def send_response(client, payload, status_code=200):
    client.send("HTTP/1.0 {} OK\r\n".format(status_code).encode())
    client.send("Content-Type: text/html\r\n".encode())
    client.send("Content-Length: {}\r\n".format(len(payload)).encode())
    client.send("\r\n".encode())
    client.sendall(payload.encode())

def read_user_strings():
    try:
        with open(STRINGS_FILE, 'r') as file:
            return file.read().strip()  # Read the entire file and strip whitespace
    except OSError:  # Handle the case where the file does not exist
        return ""


def handle_root(client):
    last_option = read_user_strings().strip()
    response_html = f"""
        <html>
            <head>
                <title>Cyberpot Setup</title>
            </head>
            <body>
                <h1>Welcome to Cyberpot Setup</h1>
                <p>Please select an option to be sent to the Access Point.</p>
                <form action="submit" method="post">
                    <input type="radio" id="option1" name="data" value="1" {'checked' if last_option == '1' else ''}>
                    <label for="option1">Option 1</label><br>
                    <input type="radio" id="option2" name="data" value="2" {'checked' if last_option == '2' else ''}>
                    <label for="option2">Option 2</label><br>
                    <input type="radio" id="option3" name="data" value="3" {'checked' if last_option == '3' else ''}>
                    <label for="option3">Option 3</label><br>
                    <input type="submit" value="Submit" />
                </form>
                <h2>Last Selected Option: {last_option}</h2>
            </body>
        </html>
    """
    send_response(client, response_html)
    
def handle_clear(client):
    open(STRINGS_FILE, 'w').close()  # Open the file in write mode and immediately close it, clearing the contents
    send_response(client, "<html><h1>Data cleared successfully!</h1></html>")



def parse_post_data(request):
    headers, body = request.split("\r\n\r\n", 1)
    post_data = {}
    for pair in body.split("&"):
        key, value = pair.split("=")
        post_data[key] = value.replace("+", " ").replace("%3F", "?").replace("%21", "!").replace("%22", '"')
    return post_data

def handle_submit(client, request):
    post_data = parse_post_data(request)
    user_data = post_data.get("data", None)

    if user_data:
        with open(STRINGS_FILE, 'w') as f:  # 'w' mode to overwrite the file
            f.write(user_data)
        send_response(client, "<html><h1>Option submitted successfully!</h1></html>")
    else:
        send_response(client, "<html><h1>Error: No option found.</h1></html>", status_code=400)



def start_server(port=80):
    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
    global server_socket
    server_socket = socket.socket()
    server_socket.bind(addr)
    server_socket.listen(1)
    print('listening on', addr)
    
    while True:
	    client, addr = server_socket.accept()
	    print('client connected from', addr)
	    
	    request = b""
	    try:
		client.settimeout(5.0)
		while not b"\r\n\r\n" in request:
		    request += client.recv(512)
	    except OSError:
		pass
	    
	    if b"POST /clear" in request:
		handle_clear(client)
	    elif b"POST /submit" in request:
		handle_submit(client, request.decode('utf-8'))
	    else:
		handle_root(client)
	    
	    client.close()


# Start the server
start_server()
