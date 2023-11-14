# README.md

## Descripción
Este programa es capaz de monitorizar el espectro en la banda LoRa (**868 MHz**). Para ello, se utiliza un receptor SDR (Software Defined Radio) y este software que se encarga de recoger los datos y procesarlos de la forma que nos interesa. Si se detecta más actividad de la esperada, se genera una alerta MQTT. Esto podría significar que están tratando de interferir en la red LoRaWAN mediante un ataque de fuerza bruta.
El programa cuenta con dos scripts:
* Cliente: Ejecuta el programa principal, el cual se encarga de recoger los datos del SDR, procesarlos y generar las alertas MQTT, que se envían al broker. Opcionalmente, se pueden enviar los datos por UDP a un servidor para poder visualizarlos en tiempo real.
* Servidor (Opcional): Se encarga de recibir los datos del cliente y mostrarlos en una interfaz gráfica. Es un `plot` dinámico que se actualiza en tiempo real.

## Parámetros de ejecución
Los parámetros de ejecución se encuentran en el archivo `.env` dentro de la carpeta `Lora_scripts/client/`. Estos son los parámetros que se pueden configurar:
* **SAMPLE_RATE** $\rightarrow$ Frecuencia de muestreo del SDR
* **CENTER_FREQ** $\rightarrow$ Frecuencia central de la banda a monitorizar, en nuestro caso es LoRa (868 MHz)
* **COLLECTED_SAMPLES** $\rightarrow$ Número de muestras que se recogen antes de procesarlas
* **GAIN** $\rightarrow$ Ganancia del SDR
* **NFFT** $\rightarrow$ Número de muestras que se utilizan para calcular la FFT
* **BROKER** $\rightarrow$ Dirección IP del broker MQTT
* **PORT** $\rightarrow$ Puerto del broker MQTT
* **TOPIC** $\rightarrow$ Tópico MQTT donde se publican las alertas
* **CLIENT_ID** $\rightarrow$ Identificador del cliente MQTT
* **USERNAME** $\rightarrow$ Usuario del broker MQTT
* **PASSWORD** $\rightarrow$ Contraseña del broker MQTT
* **UDP_HOST** $\rightarrow$ Dirección IP del servidor UDP al que se envían los datos para visualizarlos en tiempo real
* **UDP_PORT** $\rightarrow$ Puerto del servidor UDP al que se envían los datos para visualizarlos en tiempo real

* **LEN_POWER_BUFFER** $\rightarrow$ Número de muestras de las que se recoge el valor booleano si la potencia instantánea es mayor que el umbral
* **THRESHOLD_COUNT** $\rightarrow$ Número de muestras que deben ser mayores que el umbral para generar una alerta
* **EXTRA_THRESHOLD** $\rightarrow$ Umbral extra que se suma al umbral calculado para generar una alerta

## Instalación
1. Clonar el repositorio
2. Crear un nuevo entorno virtual conda con las dependencias necesarias `conda create --name <env> --file requirements.txt`
3. Configurar los parámetros de la ejecución (.env) dentro de la carpeta `Lora_scripts/client/`
4. Ejecutar el archivo `Lora_scripts/client/run.py` para el cliente y `Lora_scripts/server/plot_qt.py` para el servidor.

## Uso



