import json
import time
import re

import machine
import ujson
import network

try:
    import usocket as socket
except ImportError:
    import socket


class WebServer:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('', 80))
        self.s.listen(5)

    def check_connections(self, sim, scale, config, test, wifi, proc_data):
        try:
            conn, addr = self.s.accept()
            request = conn.recv(1024)

            req = str(request)

            # Serve index page on load
            if re.search('GET / HTTP', req):
                with open('../index.html', 'r') as html:
                    conn.send('HTTP/1.1 200 OK\n')
                    conn.send('Content-Type: text/html\n')
                    conn.send('Connection: close\n\n')
                    conn.sendall(html.read())

            # Receive new configuration settings
            elif re.search('POST /setconfig HTTP', req):
                conn.send('HTTP/1.1 200 OK\n')
                conn.send('Content-Type: application/json\n')
                conn.send('Connection: close\n\n')
                conn.send(ujson.dumps({'status': 'ok'}))
                new_config = ujson.loads(req[req.index('{'): req.rindex('}') + 1])
                if config.wifi_name != new_config['wifi_name'] or config.wifi_password != new_config['wifi_password']:
                    wifi.config(essid=new_config['wifi_name'], password=new_config['wifi_password'], authmode=network.AUTH_WPA_WPA2_PSK)
                    wifi.active(False)
                    time.sleep_ms(1000)
                    wifi.active(True)
                config.update(new_config)
                scale.read_config(config)

            elif re.search('GET /getconfig HTTP', req):
                conn.send('HTTP/1.1 200 OK\n')
                conn.send('Content-Type: application/json\n')
                conn.send('Connection: close\n\n')
                conn.sendall(ujson.dumps(config.__dict__))

            elif re.search('GET /getstat HTTP', req):
                conn.send('HTTP/1.1 200 OK\n')
                conn.send('Content-Type: application/json\n')
                conn.send('Connection: close\n\n')
                conn.sendall(ujson.dumps({
                    "raw": scale.raw,
                    "level": scale.curr_level,
                    "weight": scale.curr_weight,
                    "tare_weight": scale.tank_type["tare_weight"],
                    "gas_weight": scale.tank_type["gas_weight"],
                    "avg_use": proc_data.avg_use,
                    "days_before_empty": proc_data.days_before_empty
                }))
            elif re.search('GET /getcsv HTTP', req):
                conn.send('HTTP/1.1 200 OK\n')
                conn.send('Content-Type: application/json\n')
                conn.send('Connection: close\n\n')
                sdf = ",".join([str(r) for r in proc_data.readings])
                conn.sendall(ujson.dumps({'readings': sdf}))

            elif re.search('GET /calibrate HTTP', req):
                with open('../calibrate.html', 'r') as cal:
                    conn.send('HTTP/1.1 200 OK\n')
                    conn.send('Content-Type: text/html\n')
                    conn.send('Connection: close\n\n')
                    conn.sendall(cal.read())

            elif re.search('GET /settareoffset HTTP', req):
                conn.send('HTTP/1.1 200 OK\n')
                conn.send('Content-Type: application/json\n')
                conn.send('Connection: close\n\n')
                scale.scale.tare(times=15)
                scale.calibration['offset'] = scale.scale.OFFSET
                conn.sendall(ujson.dumps({'offset': scale.calibration['offset']}))

            elif re.search('POST /setknownmass HTTP', req):
                conn.send('HTTP/1.1 200 OK\n')
                conn.send('Content-Type: application/json\n')
                conn.send('Connection: close\n\n')
                conn.send(ujson.dumps({'status': 'ok'}))
                result = ujson.loads(req[req.index('{'): req.rindex('}') + 1])
                cf = scale.scale.read_average()
                km = result['known_mass']
                scale.calibration['known_mass'] = km
                scale.calibration['calibration_factor'] = cf
                scale.calibration['scaling'] = (cf - scale.calibration['offset']) / km
                scale.scale.set_scale(scale.calibration['scaling'])

                with open('../calibration.json', 'w') as cal:
                    cal.write(ujson.dumps(scale.calibration))

                machine.reset()

            elif re.search('GET /resetstate HTTP', req):
                conn.send('HTTP/1.1 200 OK\n')
                conn.send('Content-Type: application/json\n')
                conn.send('Connection: close\n\n')
                config.warning_sent = False
                config.last_warning_sent = False

            conn.close()
        except Exception as e:
            conn.close()
