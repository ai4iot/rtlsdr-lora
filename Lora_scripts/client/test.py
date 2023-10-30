import time
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Crear un objeto de figura
fig = make_subplots(rows=1, cols=1)
trace = go.Scatter(x=[0], y=[0], mode="lines", name="Espectro Electromagnético")

# Agregar el trazo a la figura
fig.add_trace(trace)

# Configurar el diseño
fig.update_layout(
    title="Espectro Electromagnético en Tiempo Real",
    xaxis=dict(title="Frecuencia (Hz)"),
    yaxis=dict(title="Intensidad"),
)

# Función para actualizar los datos del espectro
def update_spectrum():
    # Simula la generación de datos de espectro electromagnético
    freq = np.linspace(0, 1000, 100)
    intensity = np.random.rand(100)
    return freq, intensity

# Bucle para actualizar el espectro continuamente
fig.show()
while True:
    freq, intensity = update_spectrum()
    fig.data[0].x = freq
    fig.data[0].y = intensity
    time.sleep(1)  # Actualiza cada segundo

# Para mostrar el gráfico en una ventana emergente

