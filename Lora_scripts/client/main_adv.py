import asyncio
from rtlsdr import RtlSdr
import numpy as np
from scipy.signal import welch
import matplotlib.pyplot as plt
import matplotlib.animation as anim


#plt.ion()

fig = plt.figure()
ax = fig.add_subplot(111)

sdr = RtlSdr()

# Configure device
sample_rate = 0.25e6
sdr.sample_rate = sample_rate
sdr.center_freq = 868e6
sdr.gain = 4
NFFT = 256
collected_samples = 15 * 1024
f = np.fft.fftfreq(NFFT, 1 / sample_rate) / 1e6
f += sdr.center_freq / 1e6

# Initialize pxx with zeros to match the dimension
pxx = np.zeros(NFFT)


async def streaming_task(pxx, pxx_queue):
    buffer = []
    samples_collected = 0

    async for samples in sdr.stream(num_samples_or_bytes=15 * 1024):
        buffer.extend(samples)
        samples_collected += len(samples)
        if samples_collected >= collected_samples:
            await process_samples(buffer, pxx_queue)
            buffer = []
            samples_collected = 0

async def process_samples(buffer, pxx_queue):
    _, pxx_data = welch(x=buffer, fs=sdr.center_freq, nperseg=NFFT, scaling='spectrum', return_onesided=False)
    pxx_data = 10 * np.log10(pxx_data)
    power_result = np.trapz(10**(pxx_data / 10), f)  # Integrate in linear scale
    print(power_result)
    await pxx_queue.put((pxx_data, power_result))

async def update_pxx(pxx, pxx_queue):
    while True:
        pxx_data, _ = await pxx_queue.get()
        pxx[:] = pxx_data

async def plot_values(pxx,ax):
    def update(i):
        ax.clear()
        ax.plot(f,pxx)
    a = anim.FuncAnimation(fig, update, interval=200, repeat=True)
    plt.show()
        

async def main():
    pxx_queue = asyncio.Queue()
    streaming_task_instance = asyncio.create_task(streaming_task(pxx, pxx_queue))
    update_pxx_task = asyncio.create_task(update_pxx(pxx, pxx_queue))
    plot_task = asyncio.create_task(plot_values(pxx,ax))
    
    await asyncio.gather(streaming_task_instance, update_pxx_task, plot_task)  # Wait for all tasks to complete

    sdr.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
