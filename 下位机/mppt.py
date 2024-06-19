class MPPT(object):
	def __init__(self, ir, n):
		self.ir = ir
		self.u_prev = 0
		self.p_prev = 0
		self.n = n
		self.pwm = ir.pulse_now[self.ir.id_mppt-1]
		self.pwm_step = 0.01
		self.k_thre = 2

		self.u_average = [0 for i in range(self.n)]
		self.i_average = [0 for i in range(self.n)]
		self.cnt = 0
	def run(self, u, i, flag):
		if not flag:
			self.pwm = self.ir.set_pulse(self.ir.id_mppt, self.ir.pulse_default)
			return 0
		self.u_average[self.cnt] = u
		self.i_average[self.cnt] = i
		self.cnt += 1
		self.cnt %= self.n
		u = sum(self.u_average) / self.n
		i = sum(self.i_average) / self.n
		p = u * i
		delta_p = p - self.p_prev
		delta_u = u - self.u_prev
		k = 1
		if delta_u and delta_p:
			k = abs(delta_p / delta_u)
			if k < self.k_thre:
				k = 0
		if p > self.p_prev and u > self.u_prev:
			self.pwm -= self.pwm_step * k
		elif p > self.p_prev and u < self.u_prev:
			self.pwm += self.pwm_step * k
		elif p < self.p_prev and u > self.u_prev:
			self.pwm += self.pwm_step * k
		elif p < self.p_prev and u < self.u_prev:
			self.pwm -= self.pwm_step * k
		else:
			self.pwm = self.pwm
		self.pwm = self.ir.set_pulse(self.ir.id_mppt, self.pwm)
		self.p_prev = p
		self.u_prev = u
		return self.pwm