# type: ignore
import signal
import sys
import os
import asyncio
from rtlsdr import RtlSdr
import numpy as np
from paho_util import *
import time
import threading
import pickle
import socket
from collections import deque
from dotenv import load_dotenv
from matplotlib import pyplot as plt

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env_mod"))
# Configure device
sdr = None

sample_rate = float(os.getenv("SAMPLE_RATE"))
center_freq = float(os.getenv("CENTER_FREQ"))
gain = int(os.getenv("GAIN"))
nfft = int(os.getenv("NFFT"))
rotation = int(nfft/2)

# Program parameters
t_sample = 1 / sample_rate
collected_samples = int(os.getenv("COLLECTED_SAMPLES"))
collected_time_iteration = t_sample*collected_samples
buffer_time_ms = int(os.getenv("BUFFER_TIME_MS"))
buffer_len = int((buffer_time_ms/1000)//collected_time_iteration)
energy_buffer = deque([(0,0)] * buffer_len, maxlen=buffer_len)
buffer_index = 0
extra_threshold = float(os.getenv("EXTRA_THRESHOLD"))
energy_thresh_buffer = 0
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
buffer_lock = threading.Lock()



## Display program configuration and info ##
display_freq = lambda sample_rate: (f"{sample_rate} Hz" if sample_rate < 1e3 else
                                            f"{sample_rate / 1e3} kHz" if sample_rate < 1e6 else
                                            f"{sample_rate / 1e6} MHz")
text_time = lambda collected_time_s: (f"{collected_time_s} s" if collected_time_s >= 1 else
                                         f"{collected_time_s * 1e3} ms" if collected_time_s >= 1e-3 else
                                         f"{collected_time_s * 1e6} µs")
print("Single sample time set to: "+text_time(t_sample))
print("Sample rate set to: "+display_freq(sample_rate))
print("Central frequency set to: "+display_freq(center_freq))

print("Sample collection time set to: "+text_time(collected_time_iteration))

############################################

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
    f = np.float32((np.fft.fftfreq(nfft, 1 / sample_rate) / 1e6) + sdr.center_freq / 1e6)
    f = deque(f)
    f.rotate(rotation)
    f = np.float32(f)


async def initial_measurement():
    sdr_initial = RtlSdr()
    sdrConfig(sdr_initial)
    initial_collected_samples = collected_samples *10
    index = 0
    
    energy_threshold = 0
    async for samples in sdr_initial.stream(num_samples_or_bytes=initial_collected_samples):
        init_energy_norm = np.sum(np.square(np.abs(samples)))/len(samples)
        energy_threshold += init_energy_norm
        print(f"Initial energy per sample: {init_energy_norm:.10f}")
        index += 1
        if index > buffer_len:
            break
    sdr_initial.cancel_read_async()
    sdr_initial.close()
    print("Initial power threshold: ", energy_threshold)
    return energy_threshold


async def processing_task(udp_thread_instance,mqtt_thread_instance):
    global sdr, energy_thresh_buffer, buffer_index
    if auto_thresh:
        energy_thresh_buffer = await initial_measurement()
    else:
        energy_thresh_buffer = float(os.getenv("ENERGY_THRESHOLD"))
    if auto_thresh:
        energy_thresh_buffer *= (1 + extra_threshold)
    # Empezamos ambos hilos de forma paralela
    if client:
        mqtt_thread_instance.start()
    udp_thread_instance.start()
    sdr = RtlSdr()
    sdrConfig(sdr)
    # Registrar la función de manejo de la señal SIGINT
    signal.signal(signal.SIGINT, handle_sigint)
    try:
        async for samples in sdr.stream(num_samples_or_bytes=collected_samples):
            energy_norm = process_samples(samples)     
            energy_buffer.appendleft([energy_norm, buffer_index])
            buffer_index += 1 
            if buffer_index > buffer_len:
                buffer_index = 0
    finally:
        sys.exit(0)


def process_samples(samples):
    global udp_buffer
    energy_norm = np.sum(np.square(np.abs(samples)))/len(samples)
    print(energy_norm)
    process_udp(samples, energy_norm)
    return energy_norm


def process_udp(samples, energy_norm):
    data = {
        "frequencies": f,
        "samples": samples,
        "energy_norm": energy_norm,
        "parameters": {
            "nfft": nfft,
            "sdr_freq": sdr.center_freq,
            "energy_thresh": energy_thresh_buffer/buffer_len,
            "extra_threshold": extra_threshold,
        }
    }
    data_bytes = pickle.dumps(data)
    udp_buffer.append(data_bytes)


def mqtt_thread():
    global buffer_index
    while True:
        buffer = energy_buffer.copy()
        if buffer[0][1] == buffer.maxlen:
            sum_energy_buffer = sum([x[0] for x in buffer])
            msg = f"Energy: {sum_energy_buffer:.6f} Detected intrusion" if sum_energy_buffer > energy_thresh_buffer else "No intrusion detected"
            publish_mqtt(msg)
            print(msg)
            
            


def publish_mqtt(msg):
    time.sleep(.1)
    if client:
        try:
            result = client.publish(topic, msg)
        except Exception as e:
            print(e)
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
    mqtt_thread_instance = threading.Thread(target=mqtt_thread)
    mqtt_thread_instance.daemon = True
    udp_thread_instance.daemon = True
    streaming_task_instance = asyncio.create_task(processing_task(udp_thread_instance,mqtt_thread_instance))
    await streaming_task_instance


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
