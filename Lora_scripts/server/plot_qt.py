import sys
import socket
import pickle
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QFrame
from PyQt5.QtCore import pyqtSignal, QObject
import pyqtgraph as pg
import threading  # Import the threading module
from collections import deque

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
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.plot_frame = QFrame()  # Create a frame for the plot
        layout.addWidget(self.plot_frame)
        self.plot_widget = pg.PlotWidget(background='w')
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.plot_widget)
        self.plot_frame.setLayout(plot_layout)

        self.label_value = QLabel()  # Create a label for displaying power
        layout.addWidget(self.label_value)
        data_receiver.data_received.connect(self.update_plot)

        self.f = deque(maxlen=256)  
        self.pxx = deque(maxlen=265)
        self.pen = pg.mkPen('b', width=2)
        self.curve = self.plot_widget.plot(pen=self.pen)
        self.plot_widget.setLabel('left', 'Power (dBm)')
        self.plot_widget.setLabel('bottom', 'Frequency (MHz)')
        self.plot_widget.setYRange(-75, -20)
        

    def update_plot(self, data):
        new_data = pickle.loads(data)
        self.pxx = deque(new_data["pxx"])
        self.f = deque(new_data["frequencies"])
        self.f.rotate(128)
        self.pxx.rotate(128)
        pwr = new_data["power_result"]
        self.plot_widget.clear()
        self.plot_widget.plot(self.f, self.pxx, pen=self.pen)  # Set the line color to blue
        self.label_value.setText(f"Power: {1e6*pwr:.5f}")
        self.label_value.setStyleSheet(f"font-size: 20pt; color: {'green' if pwr > 0 else 'red'}")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    data_receiver = DataReceiver()
    data_receiver_thread = threading.Thread(target=data_receiver.start_listening)  # Use threading
    data_receiver_thread.daemon = True  # Set the thread as a daemon to exit with the main program
    data_receiver_thread.start()

    mainWin = QMainWindow()
    mainWin.setGeometry(100, 100, 800, 600)

    central_widget = PlotWidget(data_receiver)
    mainWin.setCentralWidget(central_widget)

    mainWin.show()
    sys.exit(app.exec_())
