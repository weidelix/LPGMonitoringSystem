import ujson
from libraries.HX711.hx711_gpio import HX711
from machine import Pin, SPI

tank_types = {
    'Generic 11KG': {
        # 'tare_weight': 13.1,
        'tare_weight': 12.3,
        'gas_weight': 11.0
    },
    'EC Gas 11KG': {
        'tare_weight': 5.1,
        'gas_weight': 11.0
    }
}


class Scale:
    def __init__(self, config, test):
        with open('../calibration.json', 'r') as calib:
            self.calibration = ujson.loads(calib.read())

        pin_OUT = Pin(33, Pin.IN, pull=Pin.PULL_DOWN)
        pin_SCK = Pin(32, Pin.OUT)
        # spi_SCK = Pin(14)
        # spi = SPI(1, baudrate=1000000, polarity=0,
        #           phase=0, sck=spi_SCK, mosi=pin_SCK, miso=pin_OUT)

        self.scale = HX711(pin_SCK, pin_OUT)
        self.scale.set_gain(128)
        self.scale.set_time_constant(0.5)

        if config.use_custom_weight is True:
            self.tank_type = {
                'tare_weight': config.custom_tare_weight,
                'gas_weight': config.custom_gas_weight
            }
        else:
            self.tank_type = tank_types[config.tank_type]
        self.test = test

        self.ratio = 100 / self.tank_type['gas_weight']

        if self.calibration['initial_load'] is True:
                print('Initial load...')
                self.calibrate()
        else:
            self.scale.set_offset(self.calibration['offset'])
            self.scale.set_scale(self.calibration['scaling'])

        self.curr_weight = 0
        self.curr_level = 0
        self.raw = 0

    def calibrate(self):
        print('Calibrating...')
        self.calibration['initial_load'] = False,
        print('Setting offset...')
        self.scale.tare()
        self.calibration['offset'] = self.scale.OFFSET
        print(self.scale.OFFSET)

        print(f'Place object with known mass: ', end='')
        self.calibration['known_mass'] = float(input())
        self.calibration['calibration_factor'] = self.scale.read_average()
        self.calibration['scaling'] = (self.calibration['calibration_factor'] - self.calibration['offset']) / self.calibration['known_mass']
        self.scale.set_scale(self.calibration['scaling'])

        with open('../calibration.json', 'w') as cal:
            cal.write(ujson.dumps(self.calibration))
            print('Calibration finished.')

    def gas_weight(self):
        return self.curr_weight - (self.tank_type['tare_weight'])

    def gas_level(self):
        return self.ratio * self.gas_weight()

    def read(self):
        if self.test.on is False:
            return self.scale.get_units()
        else:
            return self.test.gas_level

    def has_tank(self):
        return self.gas_level() >= 0

    def read_config(self, config):
        if config.use_custom_weight is True:
            self.tank_type = {
                'tare_weight': config.custom_tare_weight,
                'gas_weight': config.custom_gas_weight
            }
        else:
            self.tank_type = tank_types[config.tank_type]

        self.ratio = 100 / self.tank_type['gas_weight']
