import gc
import json
import re
import time

try:
    import usocket as socket
except:
    import socket


class WebServer:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('', 80))
        self.s.listen(5)

    def check_connections(self):
        while True:
            try:
                print('Waiting...')
                conn, addr = self.s.accept()
                conn.settimeout(3.0)
                print(f'Got a connection from {str(addr)}')
                request = conn.recv(1024)
                conn.settimeout(3.0)

                # Serve index page on load
                if re.search('GET / HTTP', str(request)):
                    conn.send('HTTP/1.1 200 OK\n')
                    conn.send('Content-Type: text/html\n')
                    conn.send('Connection: close\n\n')
                    conn.sendall(open('../index.html', 'r').read())

                # Receive new configuration settings
                elif re.search('POST /config HTTP', str(request)):
                    conn.send('HTTP/1.1 200 OK\n')
                    conn.send('Content-Type: application/json\n')
                    conn.send('Connection: close\n\n')
                    conn.sendall(json.dumps({'message': 'hello'}))

                conn.close()
                gc.collect()
                time.sleep(0.5)
            except OSError as e:
                conn.close()
                print('Connection closed')
