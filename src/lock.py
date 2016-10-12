# coding: utf-8
import requests


class RPiLock(object):
    """RPiLock class, a representation of the physical lock."""
    def __init__(self, user, server, port=80, model='motorized'):
        """RPiLock instance with socketio connection."""
        import pigpio
        self.user = user
        self.server, self.port = server, port
        self.model = model
        self.serial = self.get_serial()
        self.lock_id = self.get_lock_id()
        self.pi = pigpio.pi()
        self.avail_actions = {
            'unlock': 600,
            'lock': 2400,
        }

    def get_serial(self):
        """
        Get serial number on RPi, this need to be updated whenever new RPI
        model comes out.
        """
        from io import open
        serial = None
        with open('/proc/cpuinfo', 'r') as fh:
            for line in fh.readlines():
                if 'Serial' in line[:6]:
                    serial = line[10:26]
        if not serial:
            raise IOError('Serial not found, make sure this is a RPi client')
        return serial

    def get_lock_id(self):
        req_url = 'http://{}:{}/api/locks/'.format(self.server, self.port)
        all_locks = requests.get(
            req_url,
            auth=requests.auth.HTTPBasicAuth(
                self.user.username,
                self.user.password
            )
        ).json()
        for lock in all_locks:
            if lock['serial'] == self.serial:
                return lock['pk']

    def update_serverside_status(self, data):
        """Update lock status on central server."""
        req_url = 'http://{}:{}/api/locks/{}'.format(
            self.server, self.port, self.lock_id
        )
        return requests.post(req_url, json=data)

    def control_motorized(self, action, pin_num=18):
        """
        Output approriate motor control signal and pulswidth to the GPIO pins.
        """
        pulsewidth = self.avail_actions.get(action, None)
        if not pulsewidth:
            raise ValueError('Action not permitted')
        self.pi.set_servo_pulsewidth(pin_num, pulsewidth)
        return self.pi.get_servo_pulsewidth(pin_num)

    def control_electromagnetic(self, action):
        pass

    def handle_io_event(self, data):
        """Handling socketio event coming from server."""
        getattr(
            self,
            'control_{}'.format(self.model)
        )(data['action'])
        # self.update_serverside_status(data)

    def listen_for_io_signal(self):
        """Establish a never-ending connection and listen to signal."""
        from socketIO_client import SocketIO
        self.io_client = SocketIO(self.server, self.port)
        self.io_client.emit('listening', {'serial': self.serial})
        self.io_client.on('unlock', self.handle_io_event)
        self.io_client.on('lock', self.handle_io_event)
        print('Now listening to central server')
        self.io_client.wait()
