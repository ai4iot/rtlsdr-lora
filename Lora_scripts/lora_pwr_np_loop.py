import matplotlib.pyplot as plt
import numpy as np
from rtlsdr import RtlSdr
import seaborn as sns
import pandas as pd
import time
from matplotlib.animation import FuncAnimation
from scipy.signal import welch

sdr = RtlSdr()

# Configure device
sample_rate = 0.25e6
sdr.sample_rate = sample_rate
sdr.center_freq = 868e6
sdr.gain = 4
NFFT = 256
f = np.fft.fftfreq(NFFT, 1 / sample_rate) / 1e6
f += sdr.center_freq / 1e6

# Initialize the plot
fig, ax = plt.subplots()
ax.set_xlabel('Frequency (MHz)')
ax.set_ylabel('Relative power (dB)')

# Define empty data for the initial plot
frequencies = np.fft.fftfreq(NFFT, 1 / sample_rate) / 1e6
frequencies += sdr.center_freq / 1e6
power_data = np.zeros(NFFT)
text = ax.text(0.5, 0.9, '', transform=ax.transAxes, fontsize=12)

def update(frame):
    start_time = time.time()
    samples = sdr.read_samples(15*1024)
    _, pxx = welch(x=samples, fs=sdr.center_freq, nfft=NFFT,scaling=('spectrum'), return_onesided=False)
    pxx = 10 * np.log10(pxx)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken for data collection and processing: {elapsed_time:.5f} seconds")
    # Integrate to calculate power
    power_result = np.trapz(10**(pxx / 10), f)  # Integrate in linear scale    
    text.set_text(f'Total Power: {power_result:.5f} (linear scale)')
    ax.clear()
    ax.set_ylim(-70, -10)
    ax.plot(f, pxx)

# Create an animation
ani = FuncAnimation(fig, update, interval=50, repeat=True,)

# Show the interactive plot
plt.show()

# Close the RTL-SDR device
sdr.close()
