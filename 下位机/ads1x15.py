import utime as time
_REGISTER_MASK = const(0x03)
_REGISTER_CONVERT = const(0x00)
_REGISTER_CONFIG = const(0x01)
_REGISTER_LOWTHRESH = const(0x02)
_REGISTER_HITHRESH = const(0x03)
_OS_MASK = const(0x8000)
_OS_SINGLE = const(0x8000)  
_OS_BUSY = const(0x0000)  
_OS_NOTBUSY = const(0x8000)  
_MUX_MASK = const(0x7000)
_MUX_DIFF_0_1 = const(0x0000)  
_MUX_DIFF_0_3 = const(0x1000)  
_MUX_DIFF_1_3 = const(0x2000)  
_MUX_DIFF_2_3 = const(0x3000)  
_MUX_SINGLE_0 = const(0x4000)  
_MUX_SINGLE_1 = const(0x5000)  
_MUX_SINGLE_2 = const(0x6000)  
_MUX_SINGLE_3 = const(0x7000)  
_PGA_MASK = const(0x0E00)
_PGA_6_144V = const(0x0000)  
_PGA_4_096V = const(0x0200)  
_PGA_2_048V = const(0x0400)  
_PGA_1_024V = const(0x0600)  
_PGA_0_512V = const(0x0800)  
_PGA_0_256V = const(0x0A00)  
_MODE_MASK = const(0x0100)
_MODE_CONTIN = const(0x0000)  
_MODE_SINGLE = const(0x0100)  
_DR_MASK = const(0x00E0)     
_DR_128SPS = const(0x0000)   
_DR_250SPS = const(0x0020)   
_DR_490SPS = const(0x0040)   
_DR_920SPS = const(0x0060)   
_DR_1600SPS = const(0x0080)  
_DR_2400SPS = const(0x00A0)  
_DR_3300SPS = const(0x00C0)  
_DR_860SPS = const(0x00E0)  
_CMODE_MASK = const(0x0010)
_CMODE_TRAD = const(0x0000)  
_CMODE_WINDOW = const(0x0010)  
_CPOL_MASK = const(0x0008)
_CPOL_ACTVLOW = const(0x0000)  
_CPOL_ACTVHI = const(0x0008)  
_CLAT_MASK = const(0x0004)  
_CLAT_NONLAT = const(0x0000)  
_CLAT_LATCH = const(0x0004)  
_CQUE_MASK = const(0x0003)
_CQUE_1CONV = const(0x0000)  
_CQUE_2CONV = const(0x0001)  
_CQUE_4CONV = const(0x0002)  
_CQUE_NONE = const(0x0003)
_GAINS = (_PGA_6_144V,_PGA_4_096V,_PGA_2_048V,_PGA_1_024V,_PGA_0_512V,_PGA_0_256V)
_GAINS_V = (6.144,4.096,2.048,1.024,0.512,0.256)
_CHANNELS = {(0, None): _MUX_SINGLE_0,(1, None): _MUX_SINGLE_1,(2, None): _MUX_SINGLE_2,(3, None): _MUX_SINGLE_3,(0, 1): _MUX_DIFF_0_1,(0, 3): _MUX_DIFF_0_3,(1, 3): _MUX_DIFF_1_3,(2, 3): _MUX_DIFF_2_3,}
_RATES = (_DR_128SPS,_DR_250SPS,_DR_490SPS,_DR_920SPS,_DR_1600SPS,_DR_2400SPS,_DR_3300SPS,_DR_860SPS)
class ADS1115:
    def __init__(self, i2c, address=0x48, gain=1):
        self.i2c = i2c
        self.address = address
        self.gain = gain
        self.temp2 = bytearray(2)
    def _write_register(self, register, value):
        self.temp2[0] = value >> 8
        self.temp2[1] = value & 0xff
        self.i2c.mem_write(self.temp2, self.address, register, timeout=5)
    def _read_register(self, register):
        self.i2c.mem_read(self.temp2, self.address, register, timeout=5)
        return (self.temp2[0] << 8) | self.temp2[1]
    def raw_to_v(self, raw):
        v_p_b = _GAINS_V[self.gain] / 32767
        return raw * v_p_b
    def set_conv(self, rate=4, channel1=0, channel2=None):
        self.mode = (_CQUE_NONE | _CLAT_NONLAT |
                     _CPOL_ACTVLOW | _CMODE_TRAD | _RATES[rate] |
                     _MODE_SINGLE | _OS_SINGLE | _GAINS[self.gain] |
                     _CHANNELS[(channel1, channel2)])

    def read(self, rate=4, channel1=0, channel2=None):
        self._write_register(_REGISTER_CONFIG, (_CQUE_NONE | _CLAT_NONLAT |
                             _CPOL_ACTVLOW | _CMODE_TRAD | _RATES[rate] |
                             _MODE_SINGLE | _OS_SINGLE | _GAINS[self.gain] |
                             _CHANNELS[(channel1, channel2)]))
        while not self._read_register(_REGISTER_CONFIG) & _OS_NOTBUSY:
            time.sleep_ms(1)
        res = self._read_register(_REGISTER_CONVERT)
        return res if res < 32768 else res - 65536
    def read_rev(self):
        res = self._read_register(_REGISTER_CONVERT)
        self._write_register(_REGISTER_CONFIG, self.mode)
        return res if res < 32768 else res - 65536
    def alert_start(self, rate=4, channel1=0, channel2=None,
                    threshold_high=0x4000, threshold_low=0, latched=False) :
        self._write_register(_REGISTER_LOWTHRESH, threshold_low)
        self._write_register(_REGISTER_HITHRESH, threshold_high)
        self._write_register(_REGISTER_CONFIG, _CQUE_1CONV |
                             _CLAT_LATCH if latched else _CLAT_NONLAT |
                             _CPOL_ACTVLOW | _CMODE_TRAD | _RATES[rate] |
                             _MODE_CONTIN | _GAINS[self.gain] |
                             _CHANNELS[(channel1, channel2)])
    def conversion_start(self, rate=4, channel1=0, channel2=None):
        self._write_register(_REGISTER_LOWTHRESH, 0)
        self._write_register(_REGISTER_HITHRESH, 0x8000)
        self._write_register(_REGISTER_CONFIG, _CQUE_1CONV | _CLAT_NONLAT |
                             _CPOL_ACTVLOW | _CMODE_TRAD | _RATES[rate] |
                             _MODE_CONTIN | _GAINS[self.gain] |
                             _CHANNELS[(channel1, channel2)])
    def alert_read(self):
        res = self._read_register(_REGISTER_CONVERT)
        return res if res < 32768 else res - 65536
class ADS1015(ADS1115):
    def __init__(self, i2c, address=0x48, gain=1):
        super().__init__(i2c, address, gain)
    def raw_to_v(self, raw):
        return super().raw_to_v(raw << 4)
    def read(self, rate=4, channel1=0, channel2=None):
        return super().read(rate, channel1, channel2) >> 4
    def alert_start(self, rate=4, channel1=0, channel2=None, threshold_high=0x400,
        threshold_low=0, latched=False):
        return super().alert_start(rate, channel1, channel2, threshold_high << 4,
            threshold_low << 4, latched)
    def alert_read(self):
        return super().alert_read() >> 4
