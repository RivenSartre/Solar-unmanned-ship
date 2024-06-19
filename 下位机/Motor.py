from pyb import Timer,Pin
class Motor():
    # 电机pwm初始化
    def __init__(self):
        timerMotor = Timer(4, freq=50)
        self.motor_a = timerMotor.channel(3, Timer.PWM, pin=Pin('B8'))
        self.motor_b = timerMotor.channel(4, Timer.PWM, pin=Pin('B9'))
        self.motors = [self.motor_a, self.motor_b]
        self.limit = lambda n, n_max, n_min: n_min if (n_max if n > n_max else n) < n_min else (n_max if n > n_max else n)
        self.setPwm = lambda index, value: self.motors[self.limit(index, len(self.motors), 0)].pulse_width_percent(self.limit(value, 100, 0) * 5 / 100 + 5)
        self.setDefault = lambda: [self.setPwm(i, 50) for i in range(len(self.motors))]