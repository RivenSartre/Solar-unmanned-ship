import pyb, time
import micropython
micropython.alloc_emergency_exception_buf(100)
class Decoder():
    def __init__(self, pin='A0'):
        self.pin = pin
        self.current_channel = -1
        n = 10
        self.channels = [0] * n # up to 10 channels
        self.timer = pyb.Timer(1, prescaler=83, period=0x3fffffff)
        self.timer.counter(0)
        pyb.ExtInt(pin, pyb.ExtInt.IRQ_RISING, pyb.Pin.PULL_NONE, None)
        self.ext_int = pyb.ExtInt(pin, pyb.ExtInt.IRQ_RISING, pyb.Pin.PULL_NONE, self._callback)
        # self.value_range = [0 for i in range(2*n)] # max / min
        self.value_range = [2267, 1123, 2252, 1108, 2252, 1108, 2252, 1108, 2252, 1107, 2252, 1107, 2252, 1107, 2251, 1106, 0, 0, 0, 0]

    def _callback(self, line) -> None:
        ticks = self.timer.counter()
        if ticks > 5000:
            self.current_channel = 0
        elif self.current_channel > -1:
            self.channels[self.current_channel] = ticks
            self.current_channel += 1
        self.timer.counter(0)
    def get_channel_value(self, channel: int) -> int:
        v =  (self.channels[channel] - self.value_range[channel*2+1]) / (self.value_range[channel*2] - self.value_range[channel*2+1]) * 1000
        if v < 0:
            v = 0
        return int(v)
    def get_channels(self):
        rc = [500] * 8
        rc_100 = [50] * 8
        for i in range(8):
            rc[i] = self.get_channel_value(i)
            rc_100[i] = rc[i] / 10
        return rc, rc_100
    def enable(self):
        self.ext_int.enable()
    def disable(self):
        self.ext_int.disable()
    def clib(self):
        start = time.ticks_ms()
        print("start clib ppm")
        while True:
            for index, value in enumerate(self.channels):
                if value > self.value_range[index*2]:
                    self.value_range[index*2] = value
                if value < self.value_range[index*2+1] or self.value_range[index*2+1] == 0:
                    self.value_range[index*2+1] = value
            if time.ticks_ms() - start > 5000:
                break
        print('end', self.value_range)

