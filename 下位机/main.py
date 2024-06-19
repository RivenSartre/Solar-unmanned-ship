import ads1015
import ir2104
import time
import _thread
from communicate import uart
from mppt import MPPT
from pyb import UART, LED, I2C
from pid import PID

import ppm, motor
ppm = ppm.Decoder()
motor = motor.Motor()
# while True:
# 	value = ppm.get_channel_value(2)
# 	motor.setPwm(0, motor.limit(value/10, 70, 30))
# 	motor.setPwm(1, motor.limit(value/10, 70, 30))

class config:
	board_mppt = 0x01
	board_dcdc1 = 0x02
	flag_motor_init = False
	expect_dcdc_voltage = 12.1

# ir2104 控制MOS开关
ir = ir2104.IR2104(pulse_default=50)
ir.disable()

# ads1015 采样电压电流
# i2c 1 - MPPT
i2c_1 = I2C(1, I2C.MASTER)
i2c_1.init(I2C.MASTER, baudrate=100000)
adc_mppt = ads1015.ADC_MPPT(i2c_1)

# i2c 2 - DCDC
i2c_2 = I2C(3, I2C.MASTER)
i2c_2.init(I2C.MASTER, baudrate=100000)
adc_dcdc = ads1015.ADC_DCDC(i2c_2)

uart = uart(UART(2, 500000), adc_mppt, adc_dcdc, ir)
led = LED(1)

pid = PID(p=0.08, i=8, d=0, imax=40)
mppt = MPPT(ir, 20)  # 对输入电压 输入电流进行滑动串口滤波


def show():
	global ir, adc_dcdc, adc_mppt, mppt
	time_last = time.ticks_ms()
	uart.send_text("系统上电成功，初始化中...")
	# time.sleep(2)
	# flag_dcdc_initOK = adc_dcdc.acs_clib()
	# flag_mppt_initOK = adc_mppt.acs_clib()
	# flag_mppt_initOK = True
	# if flag_mppt_initOK and flag_dcdc_initOK:
	# 	uart.send_text("中点电压校准成功")
	# else:
	# 	uart.send_text("中点电压校准失败，请复位后继续")
	# 	return 0

	cnt_heart = 0
	mppt_ui, mppt_ii, mppt_uo, mppt_io = 0, 0, 0, 0
	dcdc_ui, dcdc_ii, dcdc_uo, dcdc_io = 0, 0, 0, 0
	mppt_power = 0
	dcdc_power = 0
	while True:
		uart.run(0)
		rc_data, rc_data_100 = ppm.get_channels()
		thr = rc_data[2]/10
		yaw = rc_data[3]/10

		if not uart.flag_motor and rc_data[4] > 600:
			uart.flag_motor = True
		elif uart.flag_motor and rc_data[4] < 400:
			uart.flag_motor = False

		if time.ticks_ms() - time_last >= 50:
			cnt_heart += 1
			cnt_heart %= 10
			if cnt_heart == 0:
				uart.send_heart()
			try:
				mppt_ui, mppt_ii, mppt_uo = adc_mppt.read_voltage(), adc_mppt.read_current(), adc_mppt.read_voltage(2)
				dcdc_ui, dcdc_ii, dcdc_uo = adc_dcdc.read_voltage(), adc_dcdc.read_current(), adc_dcdc.read_voltage(2)
				pass
			except Exception as e:
				continue

			# MPPT
			mppt_power = mppt_ui * mppt_ii
			if mppt_uo > 0.01:
				mppt_io = mppt_power / mppt_uo

			mppt.run(mppt_ui, mppt_ii, uart.flag_mppt)

			# DCDC
			dcdc_power = dcdc_ui * dcdc_ii 
			if dcdc_uo > 0.01:
				dcdc_io = dcdc_power / dcdc_uo
			if dcdc_ui and uart.flag_dcdc:
				error = config.expect_dcdc_voltage - dcdc_uo
				dcdc_pluse_pid = pid.get_pid(error, 1)
				ir.set_pulse(config.board_dcdc1, 50 + dcdc_pluse_pid)
				if dcdc_uo >= 11.5 and not config.flag_motor_init:
					config.flag_motor_init = True
					motor.setDefault()

			else:
				pass
			uart.send_circuit(config.board_mppt, mppt_ui, mppt_ii, mppt_uo, mppt_io)
			uart.send_circuit(config.board_dcdc1, dcdc_ui, dcdc_ii, dcdc_uo, dcdc_io)
			uart.send_pwm(0, ir.pulse_now[0])
			uart.send_pwm(1, ir.pulse_now[1])
			uart.send_rc(rc_data_100)

		if uart.flag_clibRC:
			uart.flag_clibRC = False
			if uart.flag_mppt and uart.flag_dcdc:
				uart.send_text("系统运行中暂无法校准遥控", 'red')
			else:	
				uart.send_text("开始校准PPM信号，时间5s。")
				ppm.clib()
				uart.send_text("PPM信号校准结束，请观察遥控器数据是否正常，若不正常请重新校准")

		if uart.flag_dcdc:
			ir.enable(2)
		else:
			uart.flag_motor = False
			ir.disable(2)

		if uart.flag_mppt:
			ir.enable(1)
		else:
			ir.disable(1)

		if uart.flag_motor and config.flag_motor_init:
			thr -= 50
			yaw -= 50
			if thr >= 5:
				value_left = thr + yaw
				value_right = thr - yaw
			elif thr <= -5:
				value_left = thr - yaw
				value_right = thr + yaw
			else:
				value_left = yaw
				value_right = -yaw
			value_left /= 2
			value_right /= 2
			motor.setPwm(1, motor.limit(value_left+50, 90, 10)) # left
			motor.setPwm(0, motor.limit(100-value_right-50, 90, 10))	# right
		else:
			ir.disable(1)
			motor.setPwm(1, 50)
			motor.setPwm(0, 50)



def test():
	global ir
	try:
		# ir.enable(2)
		show()
	except Exception as e:
		ir.disable()
		print(e)
		print("error")
	ir.disable()


ir.disable()

show()