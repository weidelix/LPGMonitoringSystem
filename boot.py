import network
import gc

print('Booting...')

gc.collect()

ssid = 'Hakdog 2.4'
password = 'SiopaoSiomai1234_'

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)


while not station.isconnected():
    pass

print('Connection Successful')
print(station.ifconfig())
