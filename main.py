import time
import gc
from libraries.Sim800.sim800 import sim800
from src.Scale import Scale
from src.WebServer import WebServer
import ujson
import _thread
import network
from machine import Timer
import os


class Config:
    def __init__(self):
        with open('configuration.json') as c:
            config = ujson.load(c)

            self.warning_level = config['warning_level']
            self.tank_type = config['tank_type']
            self.recipients = config['recipients']
            self.notify_ext = config['notify_ext']
            self.ext_recipient_number = config['ext_recipient_number']
            self.ext_recipient_message = config['ext_recipient_message']
            self.warning_sent = False
            self.last_warning_sent = False
            self.power_saving_mode = config['power_saving_mode']
            self.wifi_name = config['wifi_name']
            self.wifi_password = config['wifi_password']
            self.use_custom_weight = config['use_custom_weight']
            self.custom_tare_weight = config['custom_tare_weight']
            self.custom_gas_weight = config['custom_gas_weight']

    def save(self):
        with open('configuration.json', 'w') as c:
            c.write(ujson.dumps(self.__dict__))

    def update(self, config):
        self.warning_level = config['warning_level']
        self.tank_type = config['tank_type']
        self.recipients = config['recipients']
        self.notify_ext = config['notify_ext']
        self.ext_recipient_number = config['ext_recipient_number']
        self.ext_recipient_message = config['ext_recipient_message']
        self.power_saving_mode = config['power_saving_mode']
        self.wifi_name = config['wifi_name']
        self.wifi_password = config['wifi_password']
        self.use_custom_weight = config['use_custom_weight']
        self.custom_tare_weight = config['custom_tare_weight']
        self.custom_gas_weight = config['custom_gas_weight']
        self.save()


class ProcessedData:
    def __init__(self):
        self.readings = []
        self.days_before_empty = 0
        self.avg_use = 0

    def analyze(self):
        sum = 0
        count = 0
        for i in range(len(self.readings) - 1):
            diff = self.readings[i] - self.readings[i + 1]
            if diff > 0:
                sum += diff
                count += 1

        self.avg_use = sum / count

        self.days_before_empty = 0
        temp = tank_level
        while temp >= 0:
            temp -= self.avg_use
            self.days_before_empty += 1


class TestMode:
    def __init__(self):
        self.on = False
        self.gas_level = 100.0


test = TestMode()
config = Config()
proc_data = ProcessedData()

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect("Hakdog 2.4", "SiopaoSiomai1234_")


# station = network.WLAN(network.AP_IF)
# station.active(True)

# if machine.reset_cause() != machine.SOFT_RESET:
# station.config(essid=config.wifi_name, password=config.wifi_password, authmode=network.AUTH_WPA_WPA2_PSK, channel=1)

# station.active()
while not wifi.isconnected():
    pass

print('Connection Successful')
print(wifi.ifconfig())

sim = sim800(1)
scale = Scale(config, test)
server = WebServer()


def monitor_weight():
    sim.light_sleep()
    time.sleep_ms(1000)

    while True:
        # if scale.curr_weight < 0.0:
        #     scale.scale.tare()

        scale.raw = scale.scale.read_average()
        prv_weight = scale.curr_weight
        scale.curr_weight = scale.read()
        scale.curr_level = round(scale.gas_level(), 2)

        # print(f'Raw: {scale.raw}')
        # print(f'Prev Weight: {prv_weight}')
        # print(f'Weight: {scale.curr_weight}')
        # print(f'Level: {scale.curr_level}')

        curr_level = scale.curr_level

        # No tank and test mode is off
        if not scale.has_tank() and not test.on:
            config.warning_sent = False
            config.last_warning_sent = False
            continue

        if config.warning_level >= curr_level > -1.0 and not config.warning_sent and curr_level < 101.0 and scale.curr_weight <= prv_weight and False:
            sim.wake()
            if len("".join(config.recipients)) > 0:
                config.warning_sent = True
                for i in range(0, len(config.recipients)):
                    sim.send_sms(config.recipients[i], f"Your tank is about run out!\n\n{curr_level}% remaining")

            if config.notify_ext is True:
                config.warning_sent = True
                sim.send_sms(config.ext_recipient_number, config.ext_recipient_message)

            time.sleep_ms(1000)
            sim.light_sleep()

        if 5.0 >= curr_level > -1.0 and not config.last_warning_sent and curr_level < 101.0 and False:
            config.last_warning_sent = True
            sim.wake()
            for i in range(0, len(config.recipients)):
                sim.send_sms(config.recipients[i], f"You are almost out of gas!\n\n{curr_level}% remaining.")

            sim.light_sleep()

        gc.collect()
        time.sleep_ms(1500)


def check_connections():
    while True:
        try:
            time.sleep(1)
            server.check_connections(sim, scale, config, test, wifi, proc_data)
        except Exception:
            pass
        gc.collect()


days = 15
tank_level = 100.0
hour = 0

with open('readings.csv', 'r') as file:
    proc_data.readings.extend([float(x.strip("\r\n")) for x in file.readlines()])


def collect_reading():
    global hour
    hour = hour + 1

    if hour is 24:
        level = scale.curr_level

        if 0 <= level <= 100:
            if len(proc_data.readings) is 31:
                proc_data.readings.pop(0)
                proc_data.readings.append(level)
            else:
                proc_data.readings.append(level)

        hour = 0

        proc_data.analyze()
        with open('readings.csv', 'w') as file:
            file.write("\r\n".join([str(x) for x in proc_data.readings]))


_thread.start_new_thread(monitor_weight, ())
_thread.start_new_thread(check_connections, ())

timer = Timer(1)
# 86400000
# 3600000
timer.init(period=3600000, mode=Timer.PERIODIC, callback=lambda t: collect_reading())
