"""
Flynn McLean

https://www.elecrow.com/wiki/images/2/20/SIM800_Series_AT_Command_Manual_V1.09.pdf

Library for interfacing with SIM800 in Micropython


"""
import time

import re
from machine import Pin, UART

class sim800:
    def __init__(self, UART_PIN, TX=16, RX=17, BAUD=115200):
        self.UART_PIN = UART_PIN
        self.BAUD = BAUD
        self.gsm = UART(self.UART_PIN, self.BAUD, tx=TX, rx=RX)

    def signal_check(self):
        self.read()
        signal = self.gsm.write('AT+CSQ\r\n')
        return signal

    def is_connected(self):
        self.read()
        conn = self.gsm.write('AT+CREG?\r\n')
        time.sleep_ms(500)
        r = self.read()
        return bool(re.search('CREG: 0,1', r if r else ''))

    def read_sms(self, index=1):
        message = self.gsm.write(f'AT+CMGR={index}\r')
        return message

    def read_all_sms(self):
        messages = self.gsm.write('AT+CMGL"all"\r')
        return messages

    def delete_message(self, index):
        self.gsm.write('AT+CMGD={}'.format(index))

    def delete_all_messages(self):
        self.gsm.write('AT+CMGD="all"')

    def send_sms(self, number: str, message: str):
        no = ''
        self.read()

        if number.startswith('+63'):
            no = number
        elif number.startswith('0') and len(number) == 11:
            no = '+63' + number[1:]

        i = 20
        while not self.is_connected():
            i = i - 1
            if i <= 0:
                break

        if i > 0:
            self.gsm.write('AT+CMGF=1\r')
            time.sleep_ms(1000)
            self.gsm.write(f'AT+CMGS="{no}"\r')
            time.sleep_ms(1000)
            self.gsm.write(message)
            self.gsm.write('\x1a')

    def read(self):
        return self.gsm.read()

    def deep_sleep(self):
        self.reset()
        time.sleep_ms(1000)
        self.min_mode()
        time.sleep_ms(5000)
        self.light_sleep()

    def light_sleep(self):
        self.gsm.write('AT+CSCLK=2\r')

    def min_mode(self):
        self.gsm.write('AT+CFUN=0\r')

    def reset(self):
        self.gsm.write('AT+CFUN=0\r')
        time.sleep_ms(2000)
        self.gsm.write('AT+CFUN=1\r')

    def wake(self):
        self.gsm.write('AT\r')
        time.sleep_ms(500)
        self.gsm.write('AT+CSCLK=0\r')
        time.sleep_ms(500)
        self.gsm.write('AT+CFUN=1\r')