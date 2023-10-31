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

async def streaming_task():
    buffer = []
    samples_collected = 0

    async for samples in sdr.stream(num_samples_or_bytes=15 * 1024):
        buffer.extend(samples)
        samples_collected += len(samples)
        if samples_collected >= collected_samples:
            await process_samples(buffer)
            buffer = []
            samples_collected = 0

async def process_samples(buffer):
    global power_result, udp_buffer
    start_time = time.time()
    _, pxx = welch(x=buffer, fs=sdr.center_freq, nperseg=NFFT, scaling='spectrum', return_onesided=False)
    pxx = 10 * np.log10(pxx)
    power_result = np.trapz(10**(pxx / 10), f)  # Integrate in linear scale
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken for data collection and processing: {elapsed_time:.5f} seconds, power={power_result:.5f}")
    data = {
        "frequencies": f.tolist(),
        "pxx": pxx.tolist(),
        "power_result": power_result
    }
    data_bytes = pickle.dumps(data)
    udp_buffer.append(data_bytes)
def mqtt_thread():
    while True:
        if power_result >0:
            publish_mqtt()
def publish_mqtt():
    while True:
        time.sleep(0.2)
        msg = "Detected LoRa message"
        result = client.publish(topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
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
    #mqtt_thread_instance = threading.Thread(target=mqtt_thread)
    udp_thread_instance = threading.Thread(target=udp_thread)
    #mqtt_thread_instance.daemon = True
    udp_thread_instance.daemon = True
    #mqtt_thread_instance.start()
    udp_thread_instance.start()
    try:
        await streaming_task_instance
    except KeyboardInterrupt:
        print("Ctrl+C pressed. Exiting gracefully.")
    finally:
        sdr.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Ctrl+C pressed. Exiting gracefully.")
    finally:
        loop.close()

