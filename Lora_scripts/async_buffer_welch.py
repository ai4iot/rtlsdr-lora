import asyncio
import time
from matplotlib import pyplot as plt
from rtlsdr import RtlSdr
import numpy as np
from scipy.signal import welch

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
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
    start_time = time.time()
    _, pxx = welch(x=buffer, fs=sdr.center_freq, nperseg=NFFT, scaling='spectrum', return_onesided=False)
    pxx = 10 * np.log10(pxx)
    power_result = np.trapz(10**(pxx / 10), f)  # Integrate in linear scale
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken for data collection and processing: {elapsed_time:.5f} seconds, power={power_result:.5f}")

    
async def main():
    streaming_task_instance = asyncio.create_task(streaming_task())
    #plot_task = asyncio.create_task(plot_values())
    await streaming_task_instance
    #await asyncio.gather(streaming_task_instance, plot_task)  # Wait for both tasks to complete

    sdr.close()

if __name__ == "__main__":
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
