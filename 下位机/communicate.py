from pyb import UART
import time
class BasicInfo:
    ADDRESS_UPPER = 0x01  # 上位机
    ADDRESS_LOWER = 0x01  # 下位机
    DATA_HEAD = 0XAA  # 帧头
    DATA_END = 0XBB  # 帧尾
    CHECK = False  # 是否进行校验
class ReceiveFlag(object):
    uart_buf = []
    _data_len = 0
    _data_cnt = 0
    state = 0
    _tmp_i = 0
class Protocol:
    def __init__(self, uart, basic_info=BasicInfo()):
        super(Protocol, self).__init__()
        self.receive_flag = ReceiveFlag()
        self.uart = uart
        self.buffer = []
        self.add_upper = basic_info.ADDRESS_UPPER
        self.add_lower = basic_info.ADDRESS_LOWER
        self.data_head = basic_info.DATA_HEAD
        self.data_end = basic_info.DATA_END
        self.check = basic_info.CHECK
        self.BYTE1 = lambda x: (int(x) >> 8) & 0xff
        self.BYTE2 = lambda x: (int(x) >> 0) & 0xff
        self.bin16ToInt = lambda x: x if x < 0x8000 else x - 0x10000
        self.bin32ToInt = lambda x: x if x < 0x80000000 else x - 0x100000000
    def run(self, n):
        i = 0
        Buffer_size = self.uart.any()
        while i < Buffer_size:
            self.receive_prepare(self.uart.readchar())
            i = i + 1
    def receive_prepare(self, data):
        if self.receive_flag.state == 0:
            self.receive_flag.uart_buf = []  # 清空缓冲区，准备下次接收数据
            if data == self.data_head:  # 帧头
                self.receive_flag.uart_buf.append(data)  # 0
                self.receive_flag.state = 1
            else:
                self.receive_flag.state = -1
        elif self.receive_flag.state == 1:  # 上位机地址
            if data == self.add_upper:
                self.receive_flag.uart_buf.append(data)  # 1
                self.receive_flag.state = 2
            else:
                self.receive_flag.state = -1

        elif self.receive_flag.state == 2:  # 下位机地址
            if data == self.add_lower:
                self.receive_flag.uart_buf.append(data)  # 2
                self.receive_flag.state = 3
            else:
                self.receive_flag.state = -1
        elif self.receive_flag.state == 3:  # 功能字
            if data < 0xFF:
                self.receive_flag.state = 4
                self.receive_flag.uart_buf.append(data)  # 3 功能
            else:
                self.receive_flag.state = -1
        elif self.receive_flag.state == 4:  # 数据个数
            if data < 0xFF:
                self.receive_flag.state = 5
                self.receive_flag.uart_buf.append(data - 7)  # 4 数据个数
                self.receive_flag._data_len = data - 7
            else:
                self.receive_flag.state = -1
        elif self.receive_flag.state == 5:  # 数据
            self.receive_flag._tmp_i += 1
            self.receive_flag.uart_buf.append(data)
            if self.receive_flag._tmp_i == self.receive_flag._data_len:
                self.receive_flag._tmp_i = 0
                self.receive_flag.state = 6
        elif self.receive_flag.state == 6:  # 校验位
            self.receive_flag.state = 7
            self.receive_flag.uart_buf.append(data)
        elif self.receive_flag.state == 7:  # 帧尾
            if data == self.data_end:  # 帧头
                self.receive_flag.uart_buf.append(data)  # 0
                self.receive_analyse(self.receive_flag.uart_buf)
                self.receive_flag.uart_buf = []  # 清空缓冲区，准备下次接收数据
            self.receive_flag.state = 0
        else:
            self.receive_flag.state = 0
        if self.receive_flag.state == -1:
            #  接受错误
            self.receive_flag.state = 0
    def receive_analyse(self, data_buf):
        func, length = data_buf[3:5]
        data_s = data_buf[-2]
        tmp_s = 0
        if self.check:
            for i in range(length):
                tmp_s += data_buf[i + 5]
            if tmp_s % 256 == data_s:
                self.receive_error = 0
            else:
                return None
        data = []
        for i in range(length // 2):
            data.append(self.bin16ToInt((data_buf[i * 2 + 5] << 8) | data_buf[i * 2 + 6]) / 100)
        self.receive(func, data)
    def send_bytes(self, d):
        self.uart.write(d)

    def _send(self, func, values):
        length = len(values) * 2 + 7
        data = [
            self.data_head,
            self.add_upper,
            self.add_lower,
            func,
            length
        ]
        s = 0
        for value in values:
            b1, b2 = self.BYTE1(value * 100), self.BYTE2(value * 100)
            data.append(b1)
            data.append(b2)
            s += b1 + b2
        s %= 256
        data.append(s)
        data.append(self.data_end)
        self.send_bytes(bytes(data))
        return data
    def receive(self, func, data):
        pass

class uart(Protocol):
    def __init__(self, u, adc_mppt, adc_dcdc, ir):
        super().__init__(u)
        self.adc_mppt = adc_mppt
        self.adc_dcdc = adc_dcdc
        self.ir = ir 
        self.flag_mppt = False
        self.flag_dcdc = True
        self.flag_clibRC = False
        self.flag_motor = False


    def receive(self, func, data):
        if func == 0xB1:
            self.flag_motor = True
            self.send_text("电机开始运行")
        
        elif func == 0xB2:
            self.flag_motor = False
            self.send_text("电机暂停运行")
        
        elif func == 0xB3:
            if self.flag_dcdc and self.flag_mppt:
                self.send_text("系统运行中，请暂停运行后校准电压", 'red')
            else:
                mppt_half_vcc = self.adc_mppt.acs_clib()
                dcdc_half_vcc = self.adc_dcdc.acs_clib()
                if mppt_half_vcc and mppt_half_vcc:
                    self.send_text("电压校准, mppt_half_vcc:{} dcdcc_half_vcc:{}".format(mppt_half_vcc, dcdc_half_vcc))
                else:
                    self.send_text("电压校准失败，请检查是否连接电源或电源电压不符。", 'red')
        
        elif func == 0xB4:
            self.send_parameter()
        
        elif func == 0xB5:
            if data[0]:
                self.flag_mppt = True
                self.send_text("MPPT Working.")
            else:
                self.flag_mppt = False
                self.send_text("MPPT Stop.")
        
        elif func == 0xB6:
            self.flag_clibRC = True
        
        elif func == 0xB7:
            if data[0]:
                self.flag_dcdc = True
                self.send_text("DCDC Worgking")
            else:
                self.flag_dcdc = False
                self.send_text("DCDC Stop.")
        
        else:
            self.send_text("未定义命令..")

        if func > 0xB0:
            self._send(func, [0x00, 0x00])


    def send_circuit(self, source, vin, iin, uo, io):
        # source : for example: PV:0x01
        return self._send(0x01, [source, vin, iin, uo, io])
    def send_buttery(self, v, soc):
        return self._send(0x01, [0x04, v, soc])
    def send_pwm(self, index, pwm):
        # 0x02
        return self._send(0x02, [index, pwm])
    def send_parameter(self):
        # 0x03
        self.send_text("参数读取功能开发中...")
    def send_rc(self, rc_data):
        self._send(0x04, rc_data)
    def send_text(self, content, color='green'):
        content_bytes = bytes(content + '//' + color, 'utf-8')
        return self._send(0xA1, content_bytes)
    def send_heart(self):
        return self._send(0x05, [0])