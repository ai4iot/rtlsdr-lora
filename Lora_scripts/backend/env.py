import asyncio
import os
from rtlsdr import RtlSdr
import numpy as np
from scipy.signal import welch
from paho_util import *
import time
import threading
import pickle
import socket
sdr = RtlSdr()
# Configure device
sample_rate = 0.25e6
sdr.sample_rate = sample_rate
sdr.center_freq = 868e6
sdr.gain = 4
NFFT = 256
f = np.fft.fftfreq(NFFT, 1 / sample_rate) / 1e6
f += sdr.center_freq / 1e6
collected_samples = 15 * 1024
pxx = []
power_result = 0
power_threshold = 0
initial_measurement_time = 5

### MQTT config ###
broker = '192.168.77.106'
port = 1883
topic = "mqtt/edu"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'
# username = 'emqx'
# password = 'public'
client = connect_mqtt(client_id=client_id, broker=broker, port=port)
client.loop_start()
### UDP Config ###
udp_host = "192.168.79.119"  # Change this to your destination IP
udp_port = 12345  # Change this to your desired port
udp_buffer = []