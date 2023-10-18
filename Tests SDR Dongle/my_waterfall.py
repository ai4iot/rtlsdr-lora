import matplotlib.pyplot as plt
from rtlsdr import *
import time

sdr = RtlSdr()

# Configure device
sdr.sample_rate = 2.4e6
sdr.center_freq = 434e6
sdr.gain = 0

# Define the capture time (5 seconds)
capture_time = 5  # seconds
sample_rate = sdr.sample_rate
num_samples = int(capture_time * sample_rate)

# Initialize an array to store samples
samples = []

try:
    # Start capturing samples
    #sdr.reset_buffer()
    while len(samples) < num_samples:
        remaining_samples = num_samples - len(samples)
        to_capture = min(remaining_samples, 1024)
        samples.extend(sdr.read_samples(to_capture))

    # Close the SDR device
    sdr.close()

    # Estimate and plot the PSD using Matplotlib
    plt.psd(samples, NFFT=1024, Fs=sample_rate / 1e6, Fc=sdr.center_freq / 1e6)
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Relative power (dB)')

    # Save the waterfall plot as an image
    plt.savefig("waterfall_plot.png")
    plt.show()

except KeyboardInterrupt:
    print("Capture interrupted")

# Close the SDR device if not closed
sdr.close()
