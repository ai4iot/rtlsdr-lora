#!/usr/bin/env python3
# -*- coding: utf8 -*-

import asyncio
import aioserial
from serial import EIGHTBITS, PARITY_NONE,  STOPBITS_ONE
import logging

from display import Display

DEFAULT_ADDR_INT = 0 # type int
DEFAULT_BAND = '868000000'
DEFAULT_PORT = '/dev/ttyS0'
DEFAULT_BAUD = '115200'
DEFAULT_CRFOP = '22' # from 0 to 22 dBm
DEFAULT_MODE  = '0'
DEFAULT_NETID = '18'
DEFAULT_SPREADING_FACTOR = '9'
DEFAULT_BANDWIDTH = '7'
DEFAULT_CODING_RATE = '1'
DEFAULT_PREAMBLE = '12'
DEFAULT_PARAMETER = DEFAULT_SPREADING_FACTOR + ',' + DEFAULT_BANDWIDTH + ',' + DEFAULT_CODING_RATE + ',' + DEFAULT_PREAMBLE 


import locale
locale.setlocale(locale.LC_ALL, '')
#stdscr.addstr(0, 0, mystring.encode('UTF-8'))

existGPIO = True
try:
    import subprocess # for call to raspi-gpio
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    existGPIO = False

import argparse 
import sys # needed to compensate for argparses argh-parsing

        
class rylr998:
    TXD1   = 14    # GPIO.BCM  pin 8
    RXD1   = 15    # GPIO.BCM  pin 10
    RST    = 4     # GPIO.BCM  pin 7

    aio : aioserial.AioSerial   = None  # asyncio serial port

    debug  = False # By default, don't go into debug mode
    reset  = False 

    def gpiosetup(self) -> None:
        if existGPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(True)
            GPIO.setup(self.RST,GPIO.OUT,initial=GPIO.HIGH) # the default anyway
            #if self.debug:
                #print('GPIO setup mode')
                #subprocess.run(["raspi-gpio", "get", '4,14,15'])

        

    def __del__(self):
        try:
            self.aio.close() # close the serial port
        except Exception as e:
            logging.error(str(e))

        if existGPIO:
            GPIO.cleanup()   # clean up the GPIO

    def __init__(self, parity=PARITY_NONE, bytesize=EIGHTBITS,
                       stopbits= STOPBITS_ONE, timeout=None):

        self.port = str(DEFAULT_PORT)     # the RYLR998 cares about this
        self.baudrate = str(DEFAULT_BAUD) # and this (type string!)
        self.parity = parity      # this is fixed
        self.bytesize = bytesize  # so is this
        self.stopbits = stopbits  # and this
        self.timeout = timeout    # and this

        # note: self.addr is a str, args.addr is an int
        self.addr = str(DEFAULT_ADDR_INT) # set the default
        self.pwr = str(DEFAULT_CRFOP)

        self.mode = str(DEFAULT_MODE) 
        self.netid = str(DEFAULT_NETID)
        self.parameter = DEFAULT_PARAMETER  # set the default
        self.spreading_factor = str(DEFAULT_SPREADING_FACTOR)
        self.bandwidth        = str(DEFAULT_BANDWIDTH)
        self.coding_rate      = str(DEFAULT_CODING_RATE)
        self.preamble         = str(DEFAULT_PREAMBLE)

        self.gpiosetup()
        
        try:
            self.aio: aioserial.AioSerial = aioserial.AioSerial(
                                                 port = self.port,
                                                 baudrate = self.baudrate,
                                                 parity = self.parity,
                                                 bytesize = self.bytesize,
                                                 stopbits = self.stopbits,
                                                 timeout = self.timeout)

            logging.info('Opened port '+ self.port + ' at ' + self.baudrate + 'baud') 
        except Exception as e:
            logging.error(str(e))
            exit(1) # quit at this point -- no serial port then no go

    # Transceiver function
    #
    # This is the main loop. The transceiver function xcvr(scr) is designed
    # to prioritize receving and parsing command responses from the RYLR998
    # over transmission and configuration. This is done one character at
    # a time, by maintining the receive buffer, receive window, transmit
    # buffer and transmit windows separately.

    async def ATcmd(self,cmd: str = '') -> int:
        command = 'AT' + ('+' if len(cmd) > 0 else '') + cmd + '\r\n'
        count : int  = await self.aio.write_async(bytes(command, 'utf8'))
        return count


async def main():
    rylr = rylr998()  # Initializing the rylr998 object

    try:
        while True:
            # Accepting user input from the terminal
            message = input("Enter message: ")
            cmd = f"SEND=0,{len(message)},{message}"
            await rylr.ATcmd(cmd=cmd)  # Sending the user input as a message
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process spread factor and band for RYLR998.')
    parser.add_argument('--spread-factor', default=DEFAULT_SPREADING_FACTOR, type=str, help='Spread factor value')
    parser.add_argument('--band', default=DEFAULT_BAND, type=str, help='Band value')
    args = parser.parse_args()

    DEFAULT_SPREADING_FACTOR = args.spread_factor
    DEFAULT_BAND = args.band

    rylr = rylr998()  # Passing spread factor and band as arguments
    asyncio.run(main())

