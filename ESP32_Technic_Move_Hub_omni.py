from machine import Pin, ADC
from time import sleep_ms as delay
import math

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

    print("Searching for Technic Move Hub...")
    # mostro icona Bluetooth blu
    display_icon(BT_ICON, (0, 0, 255))    
    #async with aioble.scan(duration_ms=5000, interval_us=30000, window_us=30000, active=True) as scanner:
    #    async for result in scanner:
    #        print(result, result.name(), result.rssi, result.services())
    #return None

    async with aioble.scan(duration_ms=5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            #print(result, result.name(), result.rssi, result.services())            
            
            if result.name() is not None and device_name in result.name():
                print(f"Trovato dispositivo: {result.name()}")
                device = result.device
                try:
                    connection = await device.connect(timeout_ms=2000)
                    await connection.pair(bond=True, le_secure=True) # crucial to make it work!!!
                    print(f"Connesso a {device_name}")
                    # ora che siamo connessi, mostro checkmark verde
                    display_icon(CHECK_ICON, (0, 255, 0))                    
                    return connection
                except asyncio.TimeoutError:
                    print('Timeout')
                

            
    print(f"Dispositivo {device_name} non trovato.")
    return None

async def send_command(data):
    global characteristic
    
    try:
        if characteristic is not None:
            await characteristic.write(data, False)
            #print(f"Sent data: {data}")
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
key_a = Pin(36, Pin.IN)
key_b = Pin(39, Pin.IN)
vibrator = Pin(15, Pin.OUT)
buzzer = Pin(33, Pin.OUT)
key_c = Pin(18, Pin.IN) # GREEN, DOWN
key_d = Pin(19, Pin.IN) # YELLOW, RIGHT
key_f = Pin(23, Pin.IN) # RED, UP
key_e = Pin(2, Pin.IN) # BLUE, LEFT

# vibrator.on()
# vibrator.off()


async def connect(device_name):
    global connection, characteristic
    connection = await scan_and_connect(device_name)

    if not connection:
        print("Connessione fallita. Controlla il Move Hub.")
        display_icon(CROSS_ICON, (255, 0, 0))          
        return
    
    try:
        service = await connection.service(SERVICE_UUID)
        characteristic = await service.characteristic(CHARACTERISTIC_UUID)
        #print(characteristic)
        
    except asyncio.TimeoutError:
        print("Timeout discovering services/characteristics")
        return    

#async def main_car():
#    import math

# --- precompute wheel angles and their sin/cos ---
# frontal wheel:   θ0 =   0°
# rear-left wheel: θ1 = 240° = 4π/3
# rear-right wheel:θ2 = 120° = 2π/3
wheel_angles = [0, 4*math.pi/3, 2*math.pi/3]

sinA = [math.sin(θ) for θ in wheel_angles]
cosA = [math.cos(θ) for θ in wheel_angles]

# clamp helper
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v
   

async def main_car():
    global connection, characteristic
    
    turn_leds_off()
    device_name = "Technic Move"  # Nome del dispositivo LEGO
    await connect(device_name)
    if not characteristic:
        print("connection failed!")
        return

   
    print("calibrate steering")
    await calibrate_steering()
    await asyncio.sleep(3)
    
    """
    print("power test")
    await motor_start_power(MOTOR_A,50)
    await asyncio.sleep(0.5)
    await motor_start_power(MOTOR_A,-50)
    await asyncio.sleep(0.5)
    await motor_stop(MOTOR_A)
    await motor_start_power(MOTOR_B,50)
    await asyncio.sleep(0.5)
    await motor_start_power(MOTOR_B,-50)
    await asyncio.sleep(0.5)
    await motor_stop(MOTOR_B)
    await motor_start_power(MOTOR_C,50)
    await asyncio.sleep(0.5)
    await motor_start_power(MOTOR_C,-50)
    await asyncio.sleep(0.5)
    await motor_stop(MOTOR_C)
    await asyncio.sleep(0.5)
    await motor_start_power(MOTOR_A,50)
    await motor_start_power(MOTOR_B,50)
    await motor_start_power(MOTOR_C,50)
    await asyncio.sleep(0.5)
    await motor_start_power(MOTOR_A,-50)
    await motor_start_power(MOTOR_B,-50)
    await motor_start_power(MOTOR_C,-50)
    await asyncio.sleep(0.5)
    await motor_stop(MOTOR_A)
    await motor_stop(MOTOR_B)
    await motor_stop(MOTOR_C)
    """
    turn_leds_off()
    
    x0 = 0
    for i in range(20):
        x0 += x_axis.read()
    x0 = int(x0/20)
    
    y0 = 0
    for i in range(20):
        y0 += y_axis.read()
    y0 = int(y0/20)
    
   
    while True:
        drive = int((y_axis.read()-y0)/20)
        steer = int((x_axis.read()-x0)/20)
        #dead zone
        if abs(drive)<20:
            drive = 0
        if abs(steer)<10:
            steer = 0
            
        print(steer, drive, not z_axis.value())
        await drive_car(drive, steer)
        await asyncio.sleep_ms(50)
        

async def holonomic_drive_loop():
    global connection, characteristic
    
    turn_leds_off()
    device_name = "Technic Move"  # Nome del dispositivo LEGO
    await connect(device_name)
    if not characteristic:
        print("connection failed!")
        return
    
    # calibrate joystick zero
    x0 = sum(x_axis.read() for _ in range(50)) // 50
    y0 = sum(y_axis.read() for _ in range(50)) // 50

    # --- precompute wheel angles and their sin/cos ---
    # frontal wheel:   θ0 =   0°
    # rear-left wheel: θ1 = 240° = 4π/3
    # rear-right wheel:θ2 = 120° = 2π/3
    # A, B, C
    wheel_angles = [-60, 60, 180]
    
    sinA = [math.sin(t*math.pi/180) for t in wheel_angles]
    cosA = [math.cos(t*math.pi/180) for t in wheel_angles]

    """
    print("test dead zone")
    for p in range (0,30, 5):

        await motor_start_power(MOTOR_A,p)
        await motor_start_power(MOTOR_B,p)
        await motor_start_power(MOTOR_C,p)
        print (p, "%  ")
        await asyncio.sleep(2)
    """

    while True:
        # raw joystick [-204..+204] roughly
        raw_x = (x_axis.read() - x0) // 20
        raw_y = (y_axis.read() - y0) // 20

        # dead-zone
        vx = raw_x if abs(raw_x) >= 10 else 0
        vy = raw_y if abs(raw_y) >= 10 else 0
        
        # rotation from keys
        if key_a.value() == 0:
            w =  -30   # spin CCW
        elif key_b.value() == 0:
            w = 30   # spin CW
        else:
            w =  0
            
        # blue left            
        if key_e.value() == 0:
            vx = -60
        # yellow right
        elif key_d.value() == 0:
            vx = 60
        
        # green down
        if key_c.value() == 0:
            vy = -70
        # red up
        elif key_f.value() == 0:
            vy = 70        
          

        print("joystick:",vx,vy,w)
        
        # compute raw wheel speeds:
        v0 = vx * cosA[0] + vy * sinA[0] + w
        v1 = vx * cosA[1] + vy * sinA[1] + w
        v2 = vx * cosA[2] + vy * sinA[2] + w
        
        # compensate for motor C being slower
        v0 *= 0.8
        v1 *= 0.8
        v2 *= 1.0

        # scale so that max(|v|)≤100
        vmax = max(abs(v0), abs(v1), abs(v2))
        scale = -100.0 / vmax  if vmax and vmax > 100 else -1.0
        
        # final speeds, clamped to int -100..100
        s0 = int(clamp(v0 * scale, -100, 100))
        s1 = int(clamp(v1 * scale, -100, 100))
        s2 = int(clamp(v2 * scale, -100, 100))

        # send to the hub
        await motor_start_power(MOTOR_A, s0)
        await motor_start_power(MOTOR_B, s1)
        await motor_start_power(MOTOR_C, s2)

        await asyncio.sleep_ms(50)        

# Avvia lo script
asyncio.run(holonomic_drive_loop())

