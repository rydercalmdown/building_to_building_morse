import os
import time
import logging
import threading
import morse_talk as mtalk
from flask import Flask, jsonify, render_template, request
from dmx_controller import DmxController


class MorseTransmitter():
    """Class for encoding and transmitting messages in morse"""

    RGB_ON = [100, 100, 100]
    RGB_OFF = [0, 0, 0]

    def __init__(self):
        """Instantiates the class"""
        self.message = ''
        self.time_unit_dur = 0.2
        self._setup_dmx_controller()

    def __del__(self):
        """Deletes the instance"""
        try:
            self.dmx.terminate()
        except Exception:
            pass

    def _flask_master_thread(self):
        """Flask master thread"""
        self.flask_app = Flask(__name__)

        @self.flask_app.route("/")
        def main():
            return render_template('index.html')

        @self.flask_app.route("/transmit/", methods=['POST'])
        def transmit():
            message = str(request.form.get('msg')).strip().lower()
            logging.info('got {}'.format(message))
            self.send_message(message)
            return jsonify({'status': 'sent'})

        self.flask_app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)

    def _start_flask(self):
        """Starts the flask application in a daemon thread"""
        logging.info('Starting flask thread')
        self.flask_thread = threading.Thread(name='flask_thread', target=self._flask_master_thread)
        self.flask_thread.setDaemon(True)
        self.flask_thread.start()

    def _setup_dmx_controller(self):
        """Sets up the DMX controller"""
        self.dmx = DmxController()
        self.dmx.run()

    def _play_morse_binary(self, callback):
        """Plays morse using binary"""
        logging.info('Transmitting message')
        msg_bin = mtalk.encode(self.message, encoding_type='binary')
        for c in msg_bin:
            if int(c) == 1:
                callback(True)
            else:
                callback(False)
            time.sleep(self.time_unit_dur)
        callback(False)

    def callback_dmx_fixture(self, fixture_on):
        """Callback for turning the DMX fixture on and off"""
        fixtures = [0, 1]
        if fixture_on:
            for f in fixtures:
                self.dmx.set_fixture_colour(f, self.RGB_ON)
            return
        for f in fixtures:
            self.dmx.set_fixture_colour(f, self.RGB_OFF)

    def send_message(self, message):
        self.message = message
        self._play_morse_binary(self.callback_dmx_fixture)

    def run(self):
        """Start the controller"""
        logging.getLogger().setLevel(logging.INFO)
        try:
            logging.info('Running controller')
            logging.info('Starting Flask')
            self._start_flask()
            while True:
                pass
        except KeyboardInterrupt:
            logging.info('Exiting')
            self._shutdown()


if __name__ == '__main__':
    mt = MorseTransmitter()
    mt.run()
