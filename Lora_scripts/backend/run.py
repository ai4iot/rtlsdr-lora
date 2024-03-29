# type: ignore
import signal
import sys
import os
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
from dotenv import load_dotenv
from matplotlib import pyplot as plt

load_dotenv()
# Configure device
sdr = None
sample_rate = float(os.getenv("SAMPLE_RATE"))
center_freq = float(os.getenv("CENTER_FREQ"))
gain = int(os.getenv("GAIN"))
NFFT = int(os.getenv("NFFT"))
collected_samples = float(os.getenv("COLLECTED_SAMPLES"))
initial_repeats = int(os.getenv("INITIAL_REPEAT"))
auto_thresh = bool(os.getenv("AUTOTHRESH"))
pxx = []
power_result = 0
### MQTT config ###
broker = str(os.getenv("BROKER"))
port = int(os.getenv("PORT"))
topic = str(os.getenv("TOPIC"))
# generate client ID with pub prefix randomly
client_id = str(os.getenv("CLIENT_ID"))
# username = str(os.getenv("USERNAME"))
# password = str(os.getenv("PASSWORD"))
client = connect_mqtt(client_id=client_id, broker=broker, port=port)
if client:
    client.loop_start()
### UDP Config ###
udp_host = str(os.getenv("UDP_HOST"))
udp_port = int(os.getenv("UDP_PORT"))
udp_buffer = []
len_pwr_buffer = int(os.getenv("LEN_POWER_BUFFER"))
pwr_buffer = deque([0] * len_pwr_buffer, maxlen=len_pwr_buffer)
thresh_count = int(os.getenv("THRESHOLD_COUNT"))
extra_threshold = float(os.getenv("EXTRA_THRESHOLD"))
pwr_threshold = 0


def handle_sigint(signum, frame):
    global sdr
    print("Received Ctrl+C. Stopping the program and releasing resources...")
    sdr.cancel_read_async()
    sdr.close()
    sys.exit(0)


def sdrConfig(sdr):
    global f
    sdr.sample_rate = sample_rate
    sdr.center_freq = center_freq
    sdr.gain = gain
    f = np.float32((np.fft.fftfreq(NFFT, 1 / sample_rate) / 1e6) + sdr.center_freq / 1e6)
    f = deque(f)
    f.rotate(128)
    f = np.float32(f)

async def initial_measurement():
    sdr_initial = RtlSdr()
    sdrConfig(sdr_initial)
    initial_collected_samples = collected_samples * 10
    index = 0
    power_threshold = 0
    async for samples in sdr_initial.stream(num_samples_or_bytes=initial_collected_samples):
        # Calculate the power threshold based on the initial measurement
        _, initial_pxx = welch(x=samples, fs=sdr_initial.center_freq, nperseg=NFFT, scaling='spectrum',
                               return_onesided=False)
        pxx = deque(initial_pxx)
        pxx.rotate(128)
        initial_power = np.trapz(pxx, f)  # Integrate in linear scale
        power_threshold += initial_power
        print(f"Initial power: {initial_power:.10f}")
        index += 1
        if index > initial_repeats:
            break
    sdr_initial.cancel_read_async()
    sdr_initial.close()
    return power_threshold / index


async def processing_task(udp_thread_instance):
    global sdr, pwr_threshold
    if auto_thresh:
        pwr_threshold = await initial_measurement()
    else:
        pwr_threshold = float(os.getenv("POWER_THRESHOLD"))
    # Start both threads after the initial measurement
    #mqtt_thread_instance.start()
    udp_thread_instance.start()
    pwr_threshold *= (1 + extra_threshold)
    sdr = RtlSdr()
    sdrConfig(sdr)
    # Registrar la función de manejo de la señal SIGINT
    signal.signal(signal.SIGINT, handle_sigint)
    try:
        async for samples in sdr.stream(num_samples_or_bytes=sample_rate):
            pwr, pxx = await process_samples(samples, sdr)
            pwr_buffer.append(1 if pwr > pwr_threshold else 0)
    finally:
        sys.exit(0)


async def process_samples(samples, sdr):
    global udp_buffer
    start_time = time.time()
    _, pxx = welch(x=samples, fs=sdr.center_freq, nperseg=NFFT, scaling='spectrum', return_onesided=False)
    pxx = deque(pxx)
    pxx.rotate(128)
    power_result = np.trapz(pxx, f)  # Integrate in linear scale
    pxx = 10 * np.log10(pxx)
    #plt.plot(pxx,f)
    #plt.show()
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken for data collection and processing: {elapsed_time:.5f} seconds, power={power_result:.10f}")
    process_udp(pxx, power_result)
    return power_result, pxx


def process_udp(pxx, power_result):
    data = {
        "frequencies": f,
        "pxx": np.float32(pxx),
        "power_result": power_result,
        "isOverThreshold": power_result > pwr_threshold,
    }
    data_bytes = pickle.dumps(data)
    udp_buffer.append(data_bytes)


def mqtt_thread():
    while True:
        print(sum(pwr_buffer))
        if sum(pwr_buffer) >= thresh_count:
            publish_mqtt()
        time.sleep(1)


def publish_mqtt(msg="Detected LoRa message"):
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
    udp_thread_instance = threading.Thread(target=udp_thread)
    #mqtt_thread_instance = threading.Thread(target=mqtt_thread)
    #mqtt_thread_instance.daemon = True
    udp_thread_instance.daemon = True
    streaming_task_instance = asyncio.create_task(processing_task(udp_thread_instance))
    #streaming_task_instance = asyncio.create_task(processing_task(mqtt_thread_instance, udp_thread_instance))
    await streaming_task_instance


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
