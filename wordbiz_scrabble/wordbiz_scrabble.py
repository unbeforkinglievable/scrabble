#!/usr/bin/python

import json
import time
import socket
import logging
import argparse
import threading

import sys
import traceback

DEFAULT_HOST = '50.97.175.138'
DEFAULT_PORT = 1330

LOG_FORMAT = '%(levelname)s [%(filename)s:%(lineno)d:%(funcName)s] %(message)s'

DESCRIPTION = '''
Backend for a client that connects to the ISC.RO servers
'''

class Application(threading.Thread):
    def __init__(self, name, **kwargs):
        kwargs['name'] = name
        super(Application, self).__init__(**kwargs)
        self._running = threading.Event()
    def init_action(self):
        raise NotImplementedError('Implement me!')
    def mainloop_action(self):
        raise NotImplementedError('Implement me!')
    def cleanup_action(self):
        raise NotImplementedError('Implement me!')
    def run(self):
        self._running.set()
        self.init_action()
        while self._running.isSet():
            self.mainloop_action()
        self.cleanup_action()
    def stop(self):
        self._running.clear()

class WordbizApplication(Application):
    def __init__(self, client):
        super(WordbizApplication, self).__init__('WordbizApp')
        self._client = client
    def init_action(self):
        pass
    def cleanup_action(self):
        pass
    def mainloop_action(self):
        if not self._client._connected.isSet():
            logging.error('not connected; attempting to connect')
            self._client.connect()
            time.sleep(1.0)
            return
        if not self._client._loggged_in.isSet():
            logging.error('not logged in; attempting to log-in')
            self._client.login()
            time.sleep(1.0)
            return
        logging.info('Successfully logged in')
        time.sleep(1.0)
        
class WordbizClient(object):
    def __init__(self, config):
        self._config = config
        self._connected = threading.Event()
        self._logged_in = threading.Event()
        self._sock = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, a, b, c):
        self.disconnect()

    def connect(self):
        logging.debug('connecting...')
        if self._connected.isSet():
            raise RuntimeError('Already connected!')
        
        host = self._config.get('host', DEFAULT_HOST)
        port = self._config.get('port', DEFAULT_PORT)
        logging.debug('target: %s:%d' % (host, port))
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.settimeout(0.01)
            self._sock.connect((host, port))
            self._connected.set()
            logging.info('Connected to "%s:%d"' % (host, port))
        except:
            a,b,c = sys.exc_info()
            logging.error(''.join(traceback.format_exception(a,b,c)))
            try:
                self._sock.close()
            except:
                pass
            self._connected.clear()
        
    def disconnect(self):
        if self._logged_in.isSet():
            try:
                self.logout()
            except:
                pass
        
        self._connected.clear()
        self._logged_in.clear()
        try:
            self._sock.close()
        except:
            pass
        self._sock = None

    def login(self):
        if self._logged_in.isSet():
            raise RuntimeError('Already logged in!')
        
        username = self._config['username']
        password = self._config['password']

        reply = self._send_request('LOGIN %s %s 1871' % (username, password), validate = True)
        if reply is None:
            raise RuntimeError('Failed to get a reply...')
        logging.info('Response: %s' % str(reply))
        

    def logout(self):
        if not self._logged_in.isSet():
            logging.error('Not logged it; cannot log out')
            return
        self._logged_in.clear()
        reply = self._send_requst('LOGOUT', validate = True)
        if reply is None:
            raise RuntimeError('Failed to get a reply...')
        logging.info('Response: %s' % str(reply))

    def _send_request(self, request, validate = False):
        if validate:
            request += ' ?'
        request = '0 %s' % request
        request = '\0%c%s' %(len(request), request)
        logging.info('>>> %s' % str(request))
        try:
            self._sock.send(request)
            pass
        except:
            self.disconnect()
            return
        
        response = None
        if validate:
            try:
                response = self._sock.recv(4096)
            except:
                pass
        return response
                
            
    def seek(self):
        raise NotImplementedError()

    def unseek(self):
        raise NotImplementedError()

    def history(self, username=None):
        raise NotImplementedError()

    def finger(self, username=None):
        raise NotImplementedError()

def run_app(config_file):
    # open/parse the config file
    with open(config_file,'rb') as f:
        config = json.loads(f.read())

    with WordbizClient(config) as client:
        app = WordbizApplication(client)
        app.start()
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            logging.info('Bye')
        except:
            raise
        finally:
            app.stop()
    
def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('-c','--config',type=str,required=True,
                        help='Path to config file')
    parser.add_argument('--verbose',action='store_true',default=False,
                        help='Enable debugging log statements')
    args = parser.parse_args()

    logging.basicConfig(format=LOG_FORMAT)
    logging.getLogger().setLevel('DEBUG' if args.verbose else 'INFO')
    
    run_app(args.config)

if __name__ == '__main__':
    main()
