# LEGO Technic Move Hub 88019 Control Protocol

This document describes the communication protocol for controlling the LEGO Technic Move Hub 88019 included in the LEGO Technic set 42176 Porsche GT4 e-performance. The hub must be connected and paired using the specified UUIDs and in the security mode detailed below.

## Connection Details

### Hub Name
- **Technic Move**

### Service and Characteristic UUIDs
- **Service UUID**: `00001623-1212-EFDE-1623-785FEABCD123`
- **Characteristic UUID**: `00001624-1212-EFDE-1623-785FEABCD123`

### Security Mode
Your application must pair with the hub in security mode 1 level 2, which involves unauthenticated encrypted communication.

## Commands

### Calibrating the Steering
To calibrate the steering, send the following commands sequentially:

1. `0x0d, 0x00, 0x81, 0x36, 0x11, 0x51, 0x00, 0x03, 0x00, 0x00, 0x00, 0x10, 0x00`
2. `0x0d, 0x00, 0x81, 0x36, 0x11, 0x51, 0x00, 0x03, 0x00, 0x00, 0x00, 0x08, 0x00`

### Driving the Car
To drive the car, send the following command with the specified parameters:

`0x0d, 0x00, 0x81, 0x36, 0x11, 0x51, 0x00, 0x03, 0x00, speed, steering_angle, lights, 0x00`

| Parameter | Description |
|------------|-------------|
| `speed` | Car speed |
| `steering_angle` | Steering angle |
| `lights` | Light mode |

### Lights Parameter Values

| Mode | Value |
|------|--------|
| Front + Back on | `0x00` |
| Front + Back on when braking | `0x01` |
| Front + Back off | `0x04` |
| Front off, Back on when braking | `0x05` |

## Resources
For more details on the LEGO Wireless Protocol, refer to the [LEGO BLE Wireless Protocol documentation](https://lego.github.io/lego-ble-wireless-protocol-docs/).

---
This document serves as a quick reference guide for developers looking to integrate and control the LEGO Technic Move Hub 88019 in their applications. Ensure your application adheres to the specified security mode and correctly sequences the commands for optimal performance.
---

## Tutorial – Setup the Custom Controller (DFRobot Gamepad + Elecrow mBits)

### 1. Buy the hardware
- [DFRobot Gamepad](https://s.click.aliexpress.com/e/_EJiPxwU)
- [Elecrow mBits board](https://s.click.aliexpress.com/e/_EuhiRuu)

### 2. Install Thonny IDE
Download from [https://thonny.org/](https://thonny.org/)

### 3. Flash latest MicroPython image
In Thonny:  
`Tools → Options → Interpreter → Install or Update`

### 4. Install `aioble` module
In Thonny:  
`Tools → Manage Packages → search "aioble" → Install`

### 5. Load the control script
Download and open the provided `.py` script in Thonny.

### 6. Save to the board
Save it on the MicroPython device as **main.py**.

### 7. Enjoy
Reboot the board and start controlling your LEGO Technic Move Hub.

---

This README serves as a quick-start guide for developers and hobbyists integrating the LEGO Technic Move Hub 88019 with custom MicroPython-based controllers.

