import secrets
import numpy as np
import matplotlib.pyplot as plt
from rtlsdr import *

# Configuración inicial del dispositivo RTL-SDR
sdr = RtlSdr()
sdr.sample_rate = 2.4e6
sdr.gain = 4

# Parámetros del barrido en frecuencia
start_freq = 40e6
end_freq = 800e6
num_steps = 100  # Número de puntos en el barrido

# Inicializa arrays para almacenar los datos de frecuencia y PSD
frequencies = np.linspace(start_freq, end_freq, num_steps)
psd_data = []

# Realiza el barrido en frecuencia
for freq in frequencies:
    sdr.center_freq = freq
    samples = sdr.read_samples(256*1024)
    p, psd_values = plt.psd(samples, NFFT=1024, Fs=sdr.sample_rate/1e6, Fc=freq/1e6)
    psd_data.append(p)


# Convierte los datos de PSD en un arreglo 2D
psd_data = np.array(psd_data)

# Plotea los datos
plt.figure(figsize=(10, 6))
plt.imshow(10 * np.log10(psd_data), aspect='auto', cmap='viridis', extent=[start_freq/1e6, end_freq/1e6, 0, num_steps])
plt.colorbar(label='Relative power (dB)')
plt.xlabel('Frequency (MHz)')
plt.ylabel('Time Steps')
plt.title('PSD vs Frequency')
plt.show()
plt.savefig(f"pwr_fig_{secrets.choice(range(1,10000))}.png")
# Cierra el dispositivo SDR
sdr.close()
