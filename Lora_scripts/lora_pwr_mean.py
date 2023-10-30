import matplotlib.pyplot as plt
import numpy as np
from rtlsdr import RtlSdr
import seaborn as sns
import pandas as pd

sdr = RtlSdr()
# configure device
sample_rate = .25e6
sdr.sample_rate = sample_rate
sdr.center_freq = 868e6
sdr.gain = 4
NFFT = 512
# Create a 2D array to store frequency values in each iteration
num_iterations = 5
power_matrix = np.zeros((num_iterations, NFFT))

for freq_iteration in range(num_iterations):
    samples = sdr.read_samples(72*1024)
    pxx, f = plt.psd(samples, NFFT=NFFT, Fs=sdr.sample_rate / 1e6, Fc=sdr.center_freq / 1e6)
    plt.close()
    pxx = 10 * np.log10(pxx)

    # Store frequency values in the matrix
    power_matrix[freq_iteration, :] = pxx

sdr.close()

# Calculate the mean frequency values
mean_power = np.mean(power_matrix, axis=0)
frequencies = f  # Renamed for clarity

# Integrate to calculate power
power_result = np.trapz(10**(mean_power / 10), frequencies)  # Integrate in linear scale

# Create a DataFrame with the data
df = pd.DataFrame({'Frequency (MHz)': frequencies, 'Relative power (dB)': mean_power})

# Use Seaborn to plot the data
sns.set(style="darkgrid")
sns.lineplot(x='Frequency (MHz)', y='Relative power (dB)', data=df)
# Add a text label with the integrated power
plt.text(0.5, 0.9, f'Total Power: {power_result:.5f} (linear scale)', transform=plt.gca().transAxes, fontsize=12)

plt.show()
