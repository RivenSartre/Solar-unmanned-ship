from pyb import Pin, Timer
class IR2104:
	def __init__(self, freq=20*1000, pulse_max=[80, 80, 80], pulse_min=[15, 15, 15], pulse_default=50):
		self.ir2104_mppt_out = Pin('A6')
		self.ir2104_dcdc1_out = Pin('A7')
		self.ir2104_dcdc2_out = Pin('B0')
		self.ir2104_mppt_sd = Pin('B1', Pin.OUT)
		self.ir2104_dcdc1_sd = Pin('B2', Pin.OUT)
		self.ir2104_dcdc2_sd = Pin('B15', Pin.OUT)
		self.ir2104_mppt_relay = Pin('B12', Pin.OUT)
		self.ir2104_dcdc1_relay = Pin('B13', Pin.OUT)
		self.ir2104_dcdc2_relay = Pin('B14', Pin.OUT)
		self.id_mppt = 1
		self.id_dcdc1 = 2
		self.id_dcdc2 = 3
		self.disable()
		self.tim = Timer(3, freq=freq)
		self.channel_mppt = self.tim.channel(1, Timer.PWM, pin=self.ir2104_mppt_out)
		self.channel_dcdc1 = self.tim.channel(2, Timer.PWM, pin=self.ir2104_dcdc1_out)
		self.channel_dcdc2 = self.tim.channel(3, Timer.PWM, pin=self.ir2104_dcdc1_out)
		self.channel = [self.channel_mppt, self.channel_dcdc1, self.channel_dcdc2]
		self.pulse_default = pulse_default
		self.pulse_max = pulse_max
		self.pulse_min = pulse_min
		self.pulse_now = [pulse_default, pulse_default, pulse_default]
		self.set_pulse(1, self.pulse_default)
		self.set_pulse(2, self.pulse_default)
		self.set_pulse(3, self.pulse_default)
	def disable(self, which=None, value=0):
		if which == None:
			self.disable(self.id_mppt)
			self.disable(self.id_dcdc1)
			self.disable(self.id_dcdc1)
		elif which == self.id_mppt:
			self.ir2104_mppt_sd.value(value)
			self.ir2104_mppt_relay.value(value)
		elif which == self.id_dcdc1:
			self.ir2104_dcdc1_sd.value(value)
			self.ir2104_dcdc1_relay.value(value)
		elif which == self.id_dcdc1:
			self.ir2104_dcdc2_sd.value(value)
			self.ir2104_dcdc2_relay.value(value)
		else:
			pass
	def enable(self, which=None):
		self.disable(which, 1)
	def set_pulse(self, which, n):
		which -= 1
		if n <= self.pulse_min[which]:
			n = self.pulse_min[which]
		elif n >= self.pulse_max[which]:
			n = self.pulse_max[which]
		else:
			pass
		self.channel[which].pulse_width_percent(n)
		return n
