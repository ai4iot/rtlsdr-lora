import numpy as np
import matplotlib.pyplot as plt
from matplotlib.mlab import psd
from scipy import signal

SF = 7  # Spreading Factor
BW = 1000  # Bandwidth
Fs = 1000  # Sampling Frequency
SNR = 10
s = 33  # Send symbol "10"
fs = 868e6  # Carrier Frequency
bw = 125e3  # Bandwidth
frequencies = np.arange(fs-bw/2,fs+bw/2,bw/(2**SF))
# Generate a data symbol
num_samples = int((2**SF) * Fs / BW)
k = 120  # add s to k to start (defines the data symbol)
lora_symbol = np.zeros(num_samples, dtype=complex)
k_values = np.zeros(num_samples, dtype=int)
for n in range(num_samples):
    if k >= (2**SF):
        k -= 2**SF
    k += 1
    lora_symbol[n] = (1 / np.sqrt(2**SF)) * np.exp(1j * 2 * np.pi * k * (k / (2**SF * 2)))
    k_values[n] = k


# Add noise
lora_symbol_noisy = np.random.normal(0, np.sqrt(0.5 / (10**(SNR / 10))), num_samples) + \
                        1j * np.random.normal(0, np.sqrt(0.5 / (10**(SNR / 10))), num_samples) + lora_symbol
plt.plot(lora_symbol_noisy)
# Transmit
# Receiver below

# -------Generate the Base Down Chirp------
base_down_chirp = np.zeros(num_samples, dtype=complex)
k = 0
for n in range(num_samples):
    if k >= (2**SF):
        k -= 2**SF
    k += 1
    base_down_chirp[n] = (1 / np.sqrt(2**SF)) * np.exp(-1j * 2 * np.pi * k * (k / (2**SF * 2)))
plt.plot(base_down_chirp)
dechirped = lora_symbol_noisy * base_down_chirp
plt.plot(dechirped)
#dechirped = lora_symbol * base_down_chirp
""" powerSpectrum, freqenciesFound, time, imageAxis = plt.specgram(lora_symbol, Fs=Fs)
plt.show() """
corrs = np.abs(np.fft.fft(dechirped))**2
plt.plot(corrs)
ind = np.argmax(corrs)
ind2 = ind



plt.pause(0.01)

plt.figure(2)
plt.hist(ind2, bins=np.arange(2**SF + 1) - 0.5)

symbol_error_rate = np.sum(ind2 != s + 1) / 100
print("Symbol Error Rate:", symbol_error_rate)
plt.show()
