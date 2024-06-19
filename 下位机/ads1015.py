import ads1x15
import time
class ADC:
	def __init__(self, i2c, address):
		self.gain = 2 # 2.048v
		self.i2c = i2c
		self.address = address
		self.ads = ads1x15.ADS1015(self.i2c, address=address, gain=self.gain)
		self.half_vcc = 2.5

	def acs_clib(self):
		# 校准acs712 vcc/2
		if self.read_voltage(channel=0) < 12:
			self.half_vcc = 2.5
			return 0
		tmp_voltage = self.read_voltage(channel=1)
		if abs(tmp_voltage - 2.5) < 0.1:
			self.half_vcc = tmp_voltage 
			return self.half_vcc
		else:
			print("Error: ACS712 VCC/2 error.", tmp_voltage, hex(self.address))
			self.half_vcc = 2.5
			return 0
	def read_current(self):
		return 0
	def read_voltage(self, channel=0, org=False):
		return 0
class ADC_MPPT(ADC):
	def __init__(self, i2c):
		super().__init__(i2c, address=0x48)
		self.voltage_relay = 0.08  	# 继电器压降
		self.current_k = 1.65		# acs712 05B 电流增益
		self.half_vcc = 2.552		# acs712 vcc/2
	def read_current(self):
		voltage = self.read_voltage(channel=1)
		current_sensitivity = 185
		current = (voltage - self.half_vcc) * 1000 / current_sensitivity * self.current_k
		return abs(current)
	def read_voltage(self, channel=0, org=False):
		self.ads.set_conv(rate=7, channel1=channel)
		value_adc = self.ads.read_rev()
		value_adc = self.ads.read_rev()
		if org:
			return value_adc
		value_vr2 = value_adc * 2.048 / 32767
		if channel == 0:
			r1 = 110*1000
			r2 = 5.1*1000
		elif channel == 2:
			r1 = 47/2*1000
			r2 = 1*1000
		elif channel == 1:
			r1 = 46.6*1000
			r2 = 110.6*1000
		else:
			r1 = 110*1000
			r2 = 5.1*1000
		i = value_vr2 / r2
		value_voltage = i * (r1 + r2)
		return value_voltage 
class ADC_DCDC(ADC):
	def __init__(self, i2c):
		super().__init__(i2c, address=0x48)
		self.current_k = 1.33		# acs712 05B 电流增益
		self.half_vcc = 2.5		# acs712 vcc/2
	def read_current(self):
		voltage = self.read_voltage(channel=1)
		current_sensitivity = 66
		current = (voltage - self.half_vcc) * 1000 / current_sensitivity * self.current_k
		return abs(current)
	def read_voltage(self, channel=0, org=False):
		self.ads.set_conv(rate=7, channel1=channel)
		value_adc = self.ads.read_rev()
		value_adc = self.ads.read_rev()
		if org:
			return value_adc
		value_vr2 = value_adc * 2.048 / 32767
		if channel == 0:
			r1 = 110/2*1000
			r2 = 5.1*1000
		elif channel == 2:
			r1 = 47*1000
			r2 = 1*1000
		elif channel == 1:
			r1 = 47*1000
			r2 = 110*1000
		else:
			r1 = 110*1000
			r2 = 5.1*1000
		i = value_vr2 / r2
		value_voltage = i * (r1 + r2)
		return value_voltage 