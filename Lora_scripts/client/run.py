import signal
import sys
import asyncio
from rtlsdr import RtlSdr
import numpy as np
from scipy.signal import welch
from paho_util import *
import time
import threading
import pickle
import socket
from collections import deque

# Configure device
sdr = None
sample_rate = 0.25e6
NFFT = 256
collected_samples = 15 * 1024
pxx = []
power_result = 0
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
power_buffer = deque([0] * 100)
threshold_count = 50
extra_threshold = 2
max_pwr = 0

def handle_sigint(signum, frame):
    global sdr
    print("Received Ctrl+C. Stopping the program and releasing resources...")
    sdr.cancel_read_async()
    sdr.close()
    sys.exit(0)
def sdrConfig(sdr):
    global f
    sdr.sample_rate = sample_rate
    sdr.center_freq = 868e6
    sdr.gain = 4
    print("Hola")
    f = deque((np.fft.fftfreq(NFFT, 1 / sample_rate) / 1e6)+sdr.center_freq / 1e6)
    f.rotate(128)
async def initial_measurement():
    sdr_initial = RtlSdr()
    sdrConfig(sdr_initial)
    initial_measurement_buffer = []
    initial_collected_samples = collected_samples*10
    total_collected_samples = initial_collected_samples*5
    async for samples in sdr_initial.stream(num_samples_or_bytes=initial_collected_samples):
        initial_measurement_buffer.extend(samples)  # Collect data for the initial measurement
        if len(initial_measurement_buffer) > total_collected_samples:
            break  
        # Calculate the power threshold based on the initial measurement
        _, initial_pxx = welch(x=initial_measurement_buffer, fs=sdr_initial.center_freq, nperseg=NFFT, scaling='spectrum', return_onesided=False)
        pxx = deque(10 * np.log10(initial_pxx))
        pxx.rotate(128)
        pxx[0] = max_pwr  
        pxx[-1] = max_pwr
        initial_power = np.trapz(pxx, f)  # Integrate in linear scale
        power_threshold = initial_power
        print(f"Power threshold set to: {power_threshold:.10f}")
    sdr_initial.cancel_read_async()
    sdr_initial.close()
    return power_threshold
async def streaming_task():
    global sdr
    buffer = []
    samples_collected = 0
    pwr_threshold = await initial_measurement()
    pwr_threshold += extra_threshold
    sdr = RtlSdr()
    sdrConfig(sdr)
    # Registrar la función de manejo de la señal SIGINT
    signal.signal(signal.SIGINT, handle_sigint)
    try:
        async for samples in sdr.stream(num_samples_or_bytes=collected_samples):
            buffer.extend(samples)
            samples_collected += len(samples)
            if samples_collected >= collected_samples:
                pwr = await process_samples(buffer, sdr)
                buffer = []
                samples_collected = 0
                power_buffer.append(1 if pwr > pwr_threshold else 0)
                if len(power_buffer) > 100:
                    power_buffer.popleft()
    finally:
        sys.exit(0)

async def process_samples(buffer,sdr):
    global  udp_buffer
    start_time = time.time()
    _, pxx = welch(x=buffer, fs=sdr.center_freq, nperseg=NFFT, scaling='spectrum', return_onesided=False)
    pxx = deque(10 * np.log10(pxx))
    pxx.rotate(128)
    pxx[0] = max_pwr  
    pxx[-1] = max_pwr
    power_result = np.trapz(pxx, f)  # Integrate in linear scale
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken for data collection and processing: {elapsed_time:.5f} seconds, power={power_result:.10f}")
    process_udp(pxx, power_result)
    return power_result

def process_udp(pxx, power_result):
    data = {
        "frequencies": list(f),
        "pxx": list(pxx),
        "power_result": power_result
    }
    data_bytes = pickle.dumps(data)
    udp_buffer.append(data_bytes)
def mqtt_thread():
    while True:
        print(sum(power_buffer))
        if sum(power_buffer) >= threshold_count:
            publish_mqtt()
        time.sleep(1)
def publish_mqtt(msg="Detected LoRa message"):
    while True:
        time.sleep(0.2)
        result = client.publish(topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Message `{msg}` sent to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
def udp_thread():
    global udp_buffer
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        if udp_buffer:
            data = udp_buffer.pop(0)
            udp_socket.sendto(data, (udp_host, udp_port))

async def main():
    streaming_task_instance = asyncio.create_task(streaming_task())
    mqtt_thread_instance = threading.Thread(target=mqtt_thread)
    udp_thread_instance = threading.Thread(target=udp_thread)
    mqtt_thread_instance.daemon = True
    udp_thread_instance.daemon = True
    mqtt_thread_instance.start()
    udp_thread_instance.start()
    await streaming_task_instance    

if __name__ == "__main__":
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
