from hmac import new
import sys
import socket
import numpy as np
import pickle
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject

# Define the UDP server settings
UDP_IP = "192.168.79.119"  # Change this to the IP where you're receiving UDP data
UDP_PORT = 12345

class DataReceiver(QObject):
    data_received = pyqtSignal(bytes)

    def __init__(self):
        super(DataReceiver, self).__init__()
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((UDP_IP, UDP_PORT))

    def start_listening(self):
        while True:
            data, addr = self.udp_socket.recvfrom(4771)
            self.data_received.emit(data)

class PlotWidget(QWidget):
    def __init__(self, data_receiver, parent=None):
        super(PlotWidget, self).__init__(parent)
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.pxx = []
        self.f = []
        self.line, = self.ax.plot([], [])
        data_receiver.data_received.connect(self.update_plot)

    def update_plot(self, data):
        new_data = pickle.loads(data)
        pxx = new_data["pxx"]
        f = new_data["frequencies"]
        pwr = new_data["power_result"]
        print(pxx, f, pwr)
        self.ax.clear()
        self.ax.plot(f, pxx)
        self.ax.set_xlabel("Frequency (MHz)")
        self.ax.set_ylabel("Power (dBm)")
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    data_receiver = DataReceiver()
    data_receiver_thread = QTimer()
    data_receiver_thread.timeout.connect(data_receiver.start_listening)
    data_receiver_thread.start(100)  # Check for data every 100 ms

    mainWin = QMainWindow()
    mainWin.setGeometry(100, 100, 800, 600)

    central_widget = PlotWidget(data_receiver)
    mainWin.setCentralWidget(central_widget)

    mainWin.show()
    sys.exit(app.exec_())
