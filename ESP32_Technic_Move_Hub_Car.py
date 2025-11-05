from machine import Pin, ADC
from time import sleep_ms as delay

import neopixel

import uasyncio as asyncio
import aioble
import bluetooth
from struct import pack

# UUIDs del LEGO Technic Move Hub
SERVICE_UUID = bluetooth.UUID("00001623-1212-efde-1623-785feabcd123")
CHARACTERISTIC_UUID = bluetooth.UUID("00001624-1212-efde-1623-785feabcd123")

MOTOR_A  = 0x32
MOTOR_B  = 0x33
MOTOR_C  = 0x34
LIGHTS_ON_ON =      0b000
LIGHTS_ON_BRAKE =   0b001
LIGHTS_OFF_OFF =    0b100
LIGHTS_OFF_BRAKE =  0b101


# Bitmap 5×5 (stringhe di '1' e '0')
BT_ICON = [
    "00110",
    "10101",
    "01110",
    "10101",
    "00110"
]

CHECK_ICON = [
    "00000",
    "00001",
    "00010",
    "10100",
    "01000"
]

CROSS_ICON = [
    "10001",
    "01010",
    "00100",
    "01010",
    "10001"
]

def display_icon(bitmap, color):
    """
    Disegna sulla matrice 5×5 il bitmap con il colore RGB dato.
    bitmap: lista di 5 stringhe di 5 caratteri '1'/'0'
    color: tupla (r, g, b)
    """
    turn_leds_off()
    for y, row in enumerate(bitmap):
        for x, c in enumerate(row):
            if c == "1":
                idx = y * 5 + x
                display[idx] = color
    display.write()
        
# Connessione globale al Move Hub
connection = None
characteristic = None

async def scan_and_connect(device_name):
    global connection

    print("Searching for Move Hub...")
    # mostro icona Bluetooth blu
    display_icon(BT_ICON, (0, 0, 255))    
    #async with aioble.scan(duration_ms=5000, interval_us=30000, window_us=30000, active=True) as scanner:
    #    async for result in scanner:
    #        print(result, result.name(), result.rssi, result.services())
    #return None

    async with aioble.scan(duration_ms=10000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            #print(result, result.name(), result.rssi, result.services())            
            
            if result.name() is not None and device_name in result.name():
                print(f"Found Device: {result.name()}")
                device = result.device
                try:
                    connection = await device.connect(timeout_ms=3000)
                    await connection.pair(bond=True, le_secure=True) # crucial to make it work!!!
                    print(f"Connected to {device_name}")
                    # ora che siamo connessi, mostro checkmark verde
                    display_icon(CHECK_ICON, (0, 255, 0))                    
                    return connection
                except asyncio.TimeoutError:
                    print('Timeout')
                

            
    print(f"Device {device_name} not found.")
    return None

async def send_command(data):
    global characteristic
    
    try:
        if characteristic is not None:
            await characteristic.write(data, False)
            print(f"Sent data: {data}")
    except Exception as e:
        print(f"Failed to send data: {e}")

async def change_led_color(colorID):
    command = bytearray([0x08,0x00,0x81,0x3F,0x11,0x51,0x00,colorID&0xFF])
    await send_command(command)

async def drive_car(speed = 0, steer_angle = 0, lights = 0):
    command = bytearray([0x0d,0x00,0x81,0x36,0x11,0x51,0x00,0x03,0x00, speed&0xFF, steer_angle&0xFF, lights&0xFF,0x00])
    await send_command(command)

async def calibrate_steering():
    await send_command(bytes.fromhex("0d008136115100030000001000"))
    await asyncio.sleep(0.1)
    await send_command(bytes.fromhex("0d008136115100030000000800"))
    await asyncio.sleep(0.1)

async def motor_start_power(motor, power):
    await send_command(bytearray([0x08, 0x00, 0x81, motor&0xFF, 0x00, 0x51, 0x00, 0xFF&power]))

async def motor_stop(motor, brake = True):
    await send_command(bytearray([0x08, 0x00, 0x81, motor&0xFF, 0x00, 0x51, 0x00, 0x7F if brake else 0x00]))

def sign(n):
    if n==0:
        return 0
    elif n>0:
        return 1
    else :
        return -1

# 32 LED strip connected to X8.
N_LEDS = 25
display = neopixel.NeoPixel(pin=Pin(13), n=N_LEDS, bpp=3, timing = 1)

def turn_leds_off():
    for i in range(25):
        display[i] = (0, 0, 0)
    display.write()
    
    
   
# joystick P8 (click)
# joystick P1 (x axis analog) 
x_axis = ADC(Pin(32), atten=ADC.ATTN_11DB)
y_axis = ADC(Pin(25), atten=ADC.ATTN_11DB)
z_axis = Pin(4, Pin.IN)
key_f = Pin(23, Pin.IN) # RED, UP
key_a = Pin(36, Pin.IN)
key_b = Pin(39, Pin.IN)
vibrator = Pin(15, Pin.OUT)
buzzer = Pin(33, Pin.OUT)
key_c = Pin(18, Pin.IN) # GREEN, DOWN
key_d = Pin(19, Pin.IN) # YELLOW, RIGHT
key_f = Pin(23, Pin.IN) # RED, UP
key_e = Pin(2, Pin.IN) # BLUE, LEFT

async def connect(device_name):
    global connection, characteristic
    connection = await scan_and_connect(device_name)

    if not connection:
        print("Connection Failed. Check the Move Hub.")
        display_icon(CROSS_ICON, (255, 0, 0))    
        return
    
    try:
        service = await connection.service(SERVICE_UUID)
        characteristic = await service.characteristic(CHARACTERISTIC_UUID)
        print(characteristic)
        
    except asyncio.TimeoutError:
        print("Timeout discovering services/characteristics")
        return    


async def main():
    global connection, characteristic
    
    turn_leds_off()
    device_name = "Technic Move"  # Nome del dispositivo LEGO
    await connect(device_name)
    if not characteristic:
        #print("connection failed!")
        return

   
    print("calibrate steering")
    await calibrate_steering()
    await asyncio.sleep(1)
    
    turn_leds_off()
    
    x0 = 0
    for i in range(20):
        x0 += x_axis.read()
    x0 = int(x0/20)
    
    y0 = 0
    for i in range(20):
        y0 += y_axis.read()
    y0 = int(y0/20)
    
    headlights = LIGHTS_ON_ON
    while True:
        drive = int((y_axis.read()-y0)/20)
        steer = int((x_axis.read()-x0)/20)
        #dead zone
        if abs(drive)<10:
            drive = 0
        if abs(steer)<10:
            steer = 0
        
       
        if key_a.value() == 0 : # left trigger
            headlights = LIGHTS_OFF_OFF
        elif key_b.value() == 0: # right trigger
            headlights = LIGHTS_ON_ON
            
        if key_f.value() == 0 : # brake
            await drive_car(-40*sign(drive), steer, headlights | 0x01) #flash back lights
            await asyncio.sleep_ms(200)
            await drive_car(0, steer, headlights)
            await asyncio.sleep_ms(50)
            
        #print(steer, drive, "    ", end="\r")
        await drive_car(drive, steer, headlights)
        await asyncio.sleep_ms(50)
        

# Avvia lo script
asyncio.run(main())

