from tools import Comm, MyPrecious, ObsType, Scan
from _tools.observation import State


class Pulsar(Scan):
    """
    A drift scan recorded at the DAQ's full sample rate, unfiltered.

    Identical to a Scan -- same states, same calibration and background phases,
    same single declination -- with two differences, both because a pulsar's
    signal lives at frequencies an ordinary scan deliberately throws away:

      * the software filter chain is bypassed for the whole observation, so the
        recorded samples are exactly what the ADC produced, and
      * the data phase records every sample Tars pulls off the serial buffer
        instead of one per communicate() call, so the data rate is the DAQ's
        (~50 Hz per channel) rather than the few-Hz rate a scan uses.

    Calibration and background still go through communicate() at cal_freq,
    exactly as in a scan: those phases measure a level, not a waveform.
    """

    # ~50 Hz samples are 20 ms apart, which two decimals of a second cannot
    # resolve -- consecutive samples would be written with the same timestamp.
    TIMESTAMP_FORMAT = "%.4f"

    FILTERED = False
    RECORDS_EVERY_SAMPLE = True

    # Writing at the acquisition rate means ~8 file appends per sample per
    # channel at the default (unbuffered) setting. Batch them instead; the
    # buffer is flushed on close() and on every state transition's write("*").
    FILE_BUFFER_SIZE = 256

    def __init__(self):
        super().__init__()
        self.obs_type = ObsType.PULSAR

    def set_files(self):
        self.file_a = MyPrecious(self.name + "_a.md1", self.FILE_BUFFER_SIZE)
        self.file_b = MyPrecious(self.name + "_b.md1", self.FILE_BUFFER_SIZE)
        self.file_comp = MyPrecious(self.name + "_comp.md1", self.FILE_BUFFER_SIZE)

    def data_logic(self, data_point) -> Comm:
        # Deliberately does not write: record_sample() is doing the recording,
        # at the full acquisition rate. Writing here as well would duplicate
        # one sample per communicate() call.
        return Comm.NO_ACTION

    def record_sample(self, data_point, timestamp: float) -> None:
        # Gate on exactly what the DATA branch of _communicate_state() gates on,
        # since this bypasses that branch: samples before the scheduled start or
        # after the scheduled end belong to no phase and must not be recorded.
        if self.state is not State.DATA:
            return
        if timestamp < self.start_time or timestamp >= self.end_time:
            return
        self.write_data(data_point)
