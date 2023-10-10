from rtlsdr import RtlSdr

sdr = RtlSdr()

# configure device
sdr.sample_rate = 2.048e6  
sdr.center_freq = 70e6     
sdr.freq_correction = 60   
sdr.gain = 'auto'

print(sdr.read_samples(512))