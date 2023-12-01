from scipy import signal
import matplotlib.pyplot as plt
import numpy as np

def ellipFilter():
    # Especificación del filtro
    fs = 96000  # Frecuencia de muestreo
    fstop1 = 21300  # Frecuencia de detención 1
    fpass1 = 21700  # Frecuencia de paso 1
    fpass2 = 26300  # Frecuencia de paso 2
    fstop2 = 26700  # Frecuencia de detención 2
    astop1 = 40  # Atenuación en la banda de detención 1 (dB)
    apass = 1  # Rizado en la banda de paso (dB)
    astop2 = 40  # Atenuación en la banda de detención 2 (dB)

    # Diseño del filtro elíptico
    nyq = 0.5 * fs
    low = fstop1 / nyq
    high = fstop2 / nyq
    b, a = signal.ellip(6, apass, astop1, [low, high], btype='band', output='ba')
    return b, a

# Graficar la respuesta en frecuencia del filtro
#w, h = signal.freqz(b, a, worN=8000)
#frequencies = (fs * 0.5 / np.pi) * w
#plt.figure()
#plt.plot(frequencies, 20 * np.log10(abs(h)), 'b')
#plt.title('Respuesta en frecuencia del filtro elíptico de paso de banda')
#plt.xlabel('Frecuencia [Hz]')
#plt.ylabel('Ganancia [dB]')
#plt.grid()
#plt.show()




