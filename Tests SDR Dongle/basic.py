import matplotlib.pyplot as plt
from rtlsdr import *
import secrets

sdr = RtlSdr()

# configure device
sdr.sample_rate = 2.4e6
sdr.center_freq = 433e6
sdr.gain = 4

samples = sdr.read_samples(1024*256*10)
sdr.close()

# Estimate and plot the PSD using Matplotlib
plt.psd(samples, NFFT=1024, Fs=sdr.sample_rate/1e6, Fc=sdr.center_freq/1e6)
plt.xlabel('Frequency (MHz)')
plt.ylabel('Relative power (dB)')
plt.savefig(f"fig_test_{secrets.choice(range(1,10000))}_car.png")
#plt.show()
