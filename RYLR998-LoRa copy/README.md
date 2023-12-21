# RYLR998-LoRa

A Python program for 2-way texting with the 33cm band
[REYAX RYLR998](https://reyax.com/products/rylr998/) LoRa® module, 
either with a Raspberry Pi 4, five wires, and ten female-female 
GPIO connectors, or with a Linux PC running Ubuntu (or Debian), a
Windows PC running Ubuntu under WSL2 and a CP2102 USB 2.0 to TTL serial 
converter, four wires, and eight female-female GPIO connectors. 
There are no threads here, only asynchronous, non-blocking I/O calls.

WARNING: Windows requires `windows-curses`, which does not implement 
`curses.set_escdelay()` as of Python 3.11. Comment out `cur.set_escdelay(1)`
in `display.py` and run at your own risk. The text handling is erratic
in Windows, with the `set_escdelay()` function missing. If you run under 
Ubuntu or Debian under WSL2 in Windows, you will not have this problem.

> This script is too complex for a test usage. For a simplified version, try `rylr998_terminal.py`, which lets you send messages using the terminal and not a graphical user interface. Usage is simple:
>   * ***--spread-factor***: for the spreading factor (7..11, default 9)
>   * ***-band***: for choosing the operating band. Default is 868 MHz.
## Usage
```bash
usage: rylr998.py [-h] [--debug] [--factory] [--noGPIO] [--addr [0..65535]] 
                  [--band [902250000..927750000]] [--pwr [0..22]]
                  [--mode [0|1|2,30..60000,30..60000]] [--netid [3..15|18]] 
                  [--parameter [7..11,7..9,1..4,4..24]]
                  [--port [/dev/ttyS0../dev/ttyS999|
                           /dev/ttyUSB0../dev/ttyUSB999|
                           COM0..COM999]]
                  [--baud (300|1200|4800|9600|19200|28800|38400|57600|115200)]

options:
  -h, --help            show this help message and exit
  --debug               log DEBUG information
  --factory             Factory reset to manufacturer defaults. BAND: 915MHz, 
                        UART: 115200, Spreading Factor: 9, Bandwidth: 125kHz (7), 
                        Coding Rate: 1, Preamble Length: 12, Address: 0, 
                        Network ID: 18, CRFOP: 22
  --noGPIO              Do not use rPI.GPIO module even if available. 
                        Useful if using a USB to TTL converter with the RYLR998.

rylr998 config:
  --addr [0..65535]     Module address (0..65535). Default is 0
  --band [902250000..927750000]
                        Module frequency (902250000..927750000) in Hz. NOTE: the 
                        full 33cm ISM band limits 902 MHz and 928 MHz are guarded by 
                        the maximum configurable bandwidth of 500 KHz (250 KHz on 
                        either side of the configured frequency). See PARAMETER for 
                        bandwidth configuration.  Default: 915000000
  --pwr [0..22]         RF pwr out (0..22) in dBm. Default: FACTORY setting of 22 
                        or the last configured value.
  --mode [0|1|2,30..60000,30..60000]
                        Mode 0: transceiver mode. Mode 1: sleep mode. Mode 2,x,y: 
                        receive for x msec, sleep for y msec, and indefinitely. 
                        Default: 0
  --netid [3..15|18]    NETWORK ID. Note: PARAMETER values depend on NETWORK ID. 
                        Default: 18
                        NOTE: This is also known as the sync word. The available sync 
                        words on the RYLR998 are incompatible with Meshtastic (tm).
  --parameter [7..11,7..9,1..4,4..24]
                        PARAMETER. Set the RF parameters Spreading Factor, Bandwidth, 
                        Coding Rate, Preamble. Spreading factor 7..11, default 9. 
                        Bandwidth 7..9, where 7 is 125 KHz (only if spreading factor 
                        is in 7..9); 8 is 250 KHz (only if spreading factor is in 7..10); 
                        9 is 500 KHz (only if the spreading factor is in 7..11). 
                        The default bandwidth is 7. 
                        The coding rate is 1..4, default 4. 
                        The preamble is 4..25 if the NETWORK ID is 18; otherwise, the 
                        preamble must be 12. Default: 9,7,1,12

serial port config:
  --port [/dev/ttyS0../dev/ttyS999|/dev/ttyUSB0../dev/ttyUSB999|COM0..COM999]
                        Serial port device name. Default: /dev/ttyS0
  --baud (300|1200|4800|9600|19200|28800|38400|57600|115200)
                        Serial port baudrate. Default: 115200
```

### Example command line

```bash
pi@raspberrypi:~/RYLR998-LoRa$ python3 rylr998.py --pwr 22 --port /dev/ttyS0  --band 902687500  --netid 6
```

## Python Module Dependencies

* python 3.10+
* rPI.GPIO (except windows)
* [asyncio](https://pypi.org/project/asyncio/)
* [aioserial](https://pypi.org/project/aioserial/) 1.3.1+
* [curses](https://docs.python.org/3/library/curses.html) 
* windows-curses if running on Windows. Note: set_escdelay() is not implemented. Run at your own risk!!

`pip install asyncio` and so on should work.

## GPIO connections for the Raspberry Pi

The GPIO connections are as follows:

* VDD to 3.3V physical pin 1 on the GPIO
* RST to GPIO 4, physical pin 7
* TXD to GPIO 15 RXD1 this is physical pin 10
* RXD to GPIO 14 TXD1 this is physical pin 8
* GND to GND physical pin 9.

**WARNING:** get this wrong and you could fry your Raspberry Pi 4 and your REYAX RYLR998 LoRa® module. 
I haven't had problems, knock wood, but the [MIT license](https://github.com/flengyel/RYLR998-LoRa/blob/main/LICENSE) 
comes with no warranty. Check your connections! Under no circumstances apply 5V to the RYLR998 LoRa® module. Only 3.3V. 

## Disable Bluetooth and enable uart1 (/dev/ttyS0)

1. Ensure that the login shell over the serial port is disabled, but the serial port is enabled. 
In `sudo raspi-config`, select Interfacing Options, then select Serial. Answer "no" to "Would you like a login shell to be accessible over serial?" and answer "yes"  to "woud you like the serial port hardware to be enabled?".

2. Disable Bluetooth in ```/boot/config.txt``` by appending 
```bash
disable-bt=1
enable-uart=1 
```
Disable the bluetooth service with 
```bash
sudo systemctl disable hciuart.service
```

3. Enable `uart1` with the device tree overlay facility before running the code. I do this in `/etc/rc.local` with 

```bash
sudo dtoverlay uart1
```

## Connection to a PC with a CP2102 USB 2.0 to TTL module serial converter

Similar to the GPIO, only VDD goes to the 3.3V output of the converter; RX and TX are swapped, as usual; and GND goes to GND.
See the pictures below.

<p float="left">
<img src="https://user-images.githubusercontent.com/431946/216791228-058dd28e-4c32-43dd-a351-1a0bd575dc06.jpg" width="300">
<img src="https://user-images.githubusercontent.com/431946/216791243-bd2dd829-fa44-45e2-9f36-a1b2585429bb.jpg" width="300">
</p>
