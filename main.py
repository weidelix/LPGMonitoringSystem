from src.WebServer import WebServer

if __name__ is '__main__':
    print('Starting web server...')
    server = WebServer()
    server.check_connections()
