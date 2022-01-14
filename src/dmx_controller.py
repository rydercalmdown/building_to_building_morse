import os
import logging
import threading
import time
import array
from ola.ClientWrapper import ClientWrapper


class DmxController:
    """Controller for OLA DMX modules"""

    def __init__(self, universe=0, width=3):
        """Setup"""
        self.universe = universe
        self.wrapper = ClientWrapper()
        self.client = self.wrapper.Client()
        self.channels = [0] * 512
        self.fixture_channel_width = width
        self.tick_interval = 25
        self.dmx_thread_should_run = True

    def _get_fixture_channels(self, fixture_id):
        """Returns the channel IDs of the fixture"""
        start = int((fixture_id * self.fixture_channel_width))
        return {
            'r': start,
            'g': start + 1,
            'b': start + 2,
        }

    def _callback_dmx_sent(self, state):
        """Callback for DMX sent to controller"""
        if not state.Succeeded():
            self.wrapper.Stop()

    def set_fixture_colour(self, fixture_id, rgb):
        """Sets the colour on a fixture"""
        fixture_channels = self._get_fixture_channels(fixture_id)
        self.channels[fixture_channels['r']] = rgb[0]
        self.channels[fixture_channels['g']] = rgb[1]
        self.channels[fixture_channels['b']] = rgb[2]

    def _send_dmx_frame(self):
        """Updates the fixtures"""
        logging.debug('Sending frame')
        self.wrapper.AddEvent(self.tick_interval, self._send_dmx_frame)
        self.client.SendDmx(
            self.universe,
            array.array('B', self.channels),
            self._callback_dmx_sent)

    def _dmx_thread_master(self):
        """Thread for running DMX frames by hand"""
        while self.dmx_thread_should_run:
            self.client.SendDmx(
            self.universe,
            array.array('B', self.channels),
            self._callback_dmx_sent)
            time.sleep(self.tick_interval / 1000)
        logging.info('DMX master thread shutting down')

    def run(self):
        """Run the module"""
        self.dmx_thread = threading.Thread(name='dmx_thread', target=self._dmx_thread_master)
        self.dmx_thread.start()

    def terminate(self):
        """Terminates the module"""
        self.dmx_thread_should_run = False


if __name__ == '__main__':
    try:
        dc = DmxController()
        dc.run()
    except KeyboardInterrupt:
        print('Exiting')
