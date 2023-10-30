import sys
import asyncio
from rtlsdr import RtlSdr
import numpy as np
from scipy.signal import welch
from paho_util import *
import time
from matplotlib import pyplot as plt

### SDR and fft config ###
sdr = RtlSdr()
sample_rate = 0.25e6
sdr.sample_rate = sample_rate
sdr.center_freq = 868e6
sdr.gain = 4
NFFT = 256
collected_samples = 15 * 1024
f = np.fft.fftfreq(NFFT, 1 / sample_rate) / 1e6
f += sdr.center_freq / 1e6
pxx = np.zeros(NFFT)

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
    
async def streaming_task( pxx_queue):
    buffer = []
    samples_collected = 0

    async for samples in sdr.stream(num_samples_or_bytes=15 * 1024):
        buffer.extend(samples)
        samples_collected += len(samples)
        if samples_collected >= collected_samples:
            await process_samples(buffer, pxx_queue)
            buffer = []
            samples_collected = 0

async def process_samples( buffer, pxx_queue):
    _, pxx_data = welch(x=buffer, fs=sdr.center_freq, nperseg=NFFT, scaling='spectrum', return_onesided=False)
    pxx_data = 10 * np.log10(pxx_data)
    power_result = np.trapz(10**(pxx_data / 10), f)  # Integrate in linear scale
    print(power_result)
    #label.setText(f'Power Result: {power_result:.2f} dB')
    await pxx_queue.put((pxx_data, power_result))

async def update_pxx( pxx_queue):
    while True:
        pxx_data, _ = await pxx_queue.get()
        pxx[:] = pxx_data

def publish_mqtt(info):
    while True:
        time.sleep(1)
        msg = info
        result = client.publish(topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
async def main():
    pxx_queue = asyncio.Queue()
    streaming_task_instance = asyncio.create_task(streaming_task(pxx_queue))
    update_pxx_task = asyncio.create_task(update_pxx(pxx_queue))
    await asyncio.gather(streaming_task_instance, update_pxx_task)  # Wait for all tasks to complete
    sdr.close()

if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
