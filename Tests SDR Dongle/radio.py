import matplotlib.pyplot as plt
import numpy as np
from rtlsdr import *
import secrets
from scipy.signal import periodogram
from tqdm import tqdm

sdr = RtlSdr()
start_freq = 96e6
end_freq = 201.6e6
# configure device
sample_rate = 2.4e6
sdr.sample_rate = sample_rate
  
sdr.gain = 4
NFFT = 512 
power = []
freqs = []
frequencies_sweep = np.linspace(start_freq, end_freq, int((end_freq - start_freq) / sample_rate) + 1)
progress_bar = tqdm(frequencies_sweep, desc="Sweeping Frequencies", unit="MHz")
for freq in progress_bar:
    sdr.center_freq = freq
    # Aumenta el número de muestras para capturar un rango más amplio
    samples = sdr.read_samples(4 * 256 * 1024)  
    pxx, f = plt.psd(samples, NFFT=NFFT, Fs=sdr.sample_rate/1e6, Fc=sdr.center_freq/1e6)
    pxx = 10*np.log10(pxx)
    power = np.concatenate((power, pxx), axis=None)
    freqs = np.concatenate((freqs, f), axis=None)
progress_bar.close()    
sdr.close()

# Estimate and plot the PSD using Matplotlib
plt.figure(figsize=(15, 6))
plt.plot(freqs, power)
plt.xlabel('Frequency (MHz)')
plt.ylabel('Relative power (dB)')
plt.savefig(f"fig_{secrets.choice(range(1, 10000))}_radio.pdf")
#plt.show()
