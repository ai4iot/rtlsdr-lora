# type: ignore
import signal
import sys
import os
import asyncio
from rtlsdr import RtlSdr
import numpy as np
from scipy.signal import welch
from paho_util import *
import time
import threading
import pickle
import socket
from collections import deque
from dotenv import load_dotenv
from matplotlib import pyplot as plt

load_dotenv()
# Configure device
sdr = None
sample_rate = float(os.getenv("SAMPLE_RATE"))
center_freq = float(os.getenv("CENTER_FREQ"))
gain = int(os.getenv("GAIN"))
NFFT = int(os.getenv("NFFT"))
collected_samples = float(os.getenv("COLLECTED_SAMPLES"))

total_time = 0.0
executions = 0


def handle_sigint(signum, frame):
    global sdr
    print("Received Ctrl+C. Stopping the program and releasing resources...")
    sdr.cancel_read_async()
    sdr.close()
    sys.exit(0)


def sdrConfig(sdr):
    global f
    sdr.sample_rate = sample_rate
    sdr.center_freq = center_freq
    sdr.gain = gain
    f = np.float32((np.fft.fftfreq(NFFT, 1 / sample_rate) / 1e6) + sdr.center_freq / 1e6)
    f = deque(f)
    f.rotate(128)
    f = np.float32(f)


async def processing_task():
    global total_time, executions
    sdr = RtlSdr()
    sdrConfig(sdr)
    signal.signal(signal.SIGINT, handle_sigint)
    pwr = 1
    try:
        async for samples in sdr.stream(num_samples_or_bytes=collected_samples):
            if pwr == 0:
                total_time += time.time() - start_time
                executions += 1
                print(f"Average time taken: {total_time / executions:.5f} seconds")
            pwr = 0
            start_time = time.time()
    finally:
        sys.exit(0)


async def main():
    streaming_task_instance = asyncio.create_task(processing_task())
    await streaming_task_instance


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
