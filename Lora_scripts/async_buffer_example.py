import asyncio
from rtlsdr import RtlSdr

sdr = RtlSdr()
# configure device
sample_rate = .25e6
sdr.sample_rate = sample_rate
sdr.center_freq = 868e6
sdr.gain = 4
NFFT = 512
buffer = []

async def streaming():

    async for samples in sdr.stream(num_samples_or_bytes=1024):
        print(samples)

    # to stop streaming:
    await sdr.stop()

    # done
    sdr.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(streaming())

