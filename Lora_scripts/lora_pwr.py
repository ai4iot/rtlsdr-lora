import matplotlib.pyplot as plt
import numpy as np
from rtlsdr import RtlSdr
import seaborn as sns
import pandas as pd
import time

sdr = RtlSdr()
# configure device
sample_rate = .25e6
sdr.sample_rate = sample_rate
sdr.center_freq = 868e6
sdr.gain = 4
NFFT = 512



while True:
    samples = sdr.read_samples(2*1024)
    start_time = time.time()
    pxx, f = plt.psd(samples, NFFT=NFFT, Fs=sdr.sample_rate / 1e6, Fc=sdr.center_freq / 1e6,scale_by_freq=False)
    end_time = time.time()
    pxx = 10 * np.log10(pxx)
    elapsed_time = end_time - start_time
    print(f"Time taken for data collection and processing: {elapsed_time:.2f} seconds")
    # Integrate to calculate power
    power_result = np.trapz(10**(pxx / 10), f)  # Integrate in linear scale
    # Create a DataFrame with the data
    df = pd.DataFrame({'Frequency (MHz)': f, 'Relative power (dB)': pxx})

    # Use Seaborn to plot the data
    sns.set(style="darkgrid")
    sns.lineplot(x='Frequency (MHz)', y='Relative power (dB)', data=df)
    # Add a text label with the integrated power
    plt.text(0.5, 0.9, f'Total Power: {power_result:.5f} (linear scale)', transform=plt.gca().transAxes, fontsize=12)

    # Show the plot
    plt.show()

# Close the RTL-SDR device
sdr.close()


