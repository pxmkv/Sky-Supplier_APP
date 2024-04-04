from machine import Pin, UART, SPI
import time
import micropyGPS
from lora import LoRa

# Configure the button
btn = Pin(35, Pin.IN, Pin.PULL_UP)

# Emergency mode flag
emergency_mode = False

# Previous button state to detect changes
prev_btn_state = btn.value()

# Initialize GPS
uart = UART(1, baudrate=9600, tx=14, rx=34)  # Update pins according to your hardware setup
my_gps = micropyGPS.MicropyGPS()
data = [[13, 50, 25.0], 37.8752, -122.2577]
last_saved= [[13, 50, 25.0], 37.8757, -122.2587]

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


def send_location():
    while True:
        lora.send(str(get_packet()))
        # lora.send("test")
        # print(str(get_packet()))
        print('lora sent')
        time.sleep(0.5)



def check_button():
    global prev_btn_state, emergency_mode
    current_btn_state = btn.value()
    
    # Check if button state changed from high to low (button press)
    if prev_btn_state and not current_btn_state:
        # Toggle emergency mode
        emergency_mode = not emergency_mode
        print("Emergency mode activated" if emergency_mode else "Emergency mode deactivated")
        
        # If emergency mode is activated, call send_location
        if emergency_mode:
            send_location()
    
    # Update previous button state
    prev_btn_state = current_btn_state
    
    
def get_packet():
    global last_saved
    try:    
        if uart.any():
            my_sentence = uart.readline().decode('utf-8')
            print('my_sentence', my_sentence)
            # for x in my_sentence:
            #     my_gps.update(x)
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
    

def main():
    while True:
        check_button()
        time.sleep(0.1)  # Polling delay to debounce and manage button press detection

if __name__ == '__main__':
    main()

