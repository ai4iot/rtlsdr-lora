
from matplotlib import pyplot as plt
import numpy as np
from scipy import signal
from filter import ellipFilter
from scipy.signal import welch
import pickle
H = np.array([
    [1.0000, 0.3889, 1.0000, 1.0000, 0.2587, 0.9653],
    [1.0000, -0.3889, 1.0000, 1.0000, -0.2587, 0.9653],
    [1.0000, 0.8198, 1.0000, 1.0000, 0.1187, 0.9090],
    [1.0000, -0.8198, 1.0000, 1.0000, -0.1187, 0.9090],
    [1.0000, 0.3332, 1.0000, 1.0000, 0.2987, 0.9930],
    [1.0000, -0.3332, 1.0000, 1.0000, -0.2987, 0.9930]
])

k=[0.8415, 0.8415, 0.7057, 0.7057, 0.1745, 0.1745, 1.0000]

# Aplicar el filtro
f = open('/home/edub/Nextcloud/Documents/CEPSA/raspi-sdr/Lora_scripts/filter/cap3.pckl', 'rb')
x = pickle.load(f)
f.close()
xR = x.real
E = 10
x_expanded = np.zeros(len(xR) * E)  
x_expanded[::E] = xR  

filtered_signal = x_expanded
#b, a = ellipFilter()
# Filtrar las muestras expandidas con el filtro elíptico
for i in range(6):
    filtered_signal = signal.lfilter(H[i, 1:3], H[i, 4:6], filtered_signal)
    #filtered_signal = filtered_signal * (k[i]/k[i+3])

#filtered_signal_processed = [x for x in filtered_signal if (np.isfinite(x) and (np.absolute(x) < 1000))]
_, pxx = welch(x=filtered_signal, fs=868e6, nperseg=1024, scaling='spectrum', return_onesided=False)
plt.plot(pxx)
plt.show()