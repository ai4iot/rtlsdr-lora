import sys
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class LoraSymbolViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Lora Symbol Viewer")

        # Create the central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create the SF input field
        self.sf_label = QLabel("Spreading Factor (SF):")
        layout.addWidget(self.sf_label)
        self.sf_entry = QLineEdit()
        self.sf_entry.setText("7")  # Set default value
        layout.addWidget(self.sf_entry)

        # Create the fs input field
        self.fs_label = QLabel("Frequency (fs):")
        layout.addWidget(self.fs_label)
        self.fs_entry = QLineEdit()
        self.fs_entry.setText("868")  # Set default value
        layout.addWidget(self.fs_entry)

        # Create the bw input field
        self.bw_label = QLabel("Bandwidth (bw):")
        layout.addWidget(self.bw_label)
        self.bw_entry = QLineEdit()
        self.bw_entry.setText("125")  # Set default value
        layout.addWidget(self.bw_entry)

        # Create the data input field
        self.data_label = QLabel("Symbol number to display:")
        layout.addWidget(self.data_label)
        self.data_entry = QLineEdit()
        self.data_entry.setText("20")  # Set default value
        layout.addWidget(self.data_entry)

        # Create the update button
        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.update_plot)
        layout.addWidget(self.update_button)

        # Create the plot
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.fig.suptitle('Lora Symbol')
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
    

    def update_plot(self):
        SF = int(self.sf_entry.text())
        bw = float(self.bw_entry.text()) * 1e3
        fs = float(self.fs_entry.text()) * 1e6
        k = int(self.data_entry.text())

        num_symbols = 2 ** SF  # Cálculo del número total de símbolos disponibles
        self.sf_label.setText(f"Spreading Factor (SF): {SF} - Total Symbols: {num_symbols}")

        num_samples = num_symbols  # Utilizar el número total de símbolos en lugar de 2**SF

        frequencies = np.arange(fs - bw / 2, fs + bw / 2, bw / num_symbols)
        lora_symbol = np.zeros(num_samples, dtype=complex)
        k_values = np.zeros(num_samples, dtype=int)
        for n in range(num_samples):
            if k >= num_symbols:
                k -= num_symbols
            k += 1
            lora_symbol[n] = (1 / np.sqrt(num_symbols)) * np.exp(1j * 2 * np.pi * k * (k / (num_symbols * 2)))
            k_values[n] = frequencies[k - 1]

        self.ax1.clear()
        self.ax1.plot(range(num_samples), k_values / 1e6)
        self.ax1.set_xlabel('N sample')
        self.ax1.set_ylabel('F(MHz)')
        self.ax1.margins(0.1)  # Add padding to the plot

        self.ax2.clear()
        self.ax2.plot(range(num_samples), np.real(lora_symbol), label='Real')
        self.ax2.plot(range(num_samples), np.imag(lora_symbol), label='Imaginary')
        self.ax2.set_xlabel('N sample')
        self.ax2.set_ylabel('Amplitude')
        self.ax2.legend()
        self.ax2.margins(0.1)  # Add padding to the plot

        self.fig.tight_layout(pad=3.0)  # Add padding to the figure
        self.canvas.draw()

def run_app():
    app = QApplication(sys.argv)
    window = LoraSymbolViewer()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()
