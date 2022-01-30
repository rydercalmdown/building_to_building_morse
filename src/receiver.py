import os
import time
import logging
import threading
from rtsparty import Stream
from PIL import Image, ImageStat
import morse_talk as mtalk
from signal_calibrator import SignalCalibrator
import cv2


class MorseReceiver():
    """Module for receiving morse code"""

    DOT = 0
    DASH = 1
    INTRACHARACTER_BREAK = 2
    INTERCHARACTER_BREAK = 3
    INTERWORD_BREAK = 4
    EXTENDED_BREAK = 5


    def __init__(self):
        """Instantiate the module"""
        logging.getLogger().setLevel(logging.INFO)
        self._setup_stream()
        self.crop_coordinates = {'x1': 0, 'y1': 0, 'x2': 0, 'y2': 0}
        self.binary = 0
        self.time_unit_dur = 0.5
        self.running_character = ''
        self.running_message = ''

    def _setup_stream(self):
        """Set up the stream to the camera"""
        logging.info('Starting stream')
        self.stream = Stream(os.environ.get('STREAM_URL'))

    def _convert_np_to_img(self, frame):
        """Converts np to rgb image"""
        return Image.fromarray(frame, 'RGB')

    def _crop_frame(self, frame):
        """Returns a cropped frame via calibrated coordinates"""
        return frame.crop((
            self.crop_coordinates['x1'],
            self.crop_coordinates['y1'],
            self.crop_coordinates['x2'],
            self.crop_coordinates['y2']))

    def _convert_to_greyscale(self, image):
        """Returns a greyscale converted image"""
        return image.copy().convert('L')

    def _get_average_brightness(self, image):
        """Returns the average brightness of the image"""
        image = self._convert_to_greyscale(image)
        stat = ImageStat.Stat(image)
        return stat.mean[0]

    def _convert_8_bit_to_bin(self, brightness_8_bit):
        """Converts 8 bit brightness values to binary values"""
        return int(brightness_8_bit > 127)

    def _process_frame(self):
        """Processes each individual frame"""
        frame = self.stream.get_frame()
        while self.stream.is_frame_empty(frame):
            frame = self.stream.get_frame()
        frame_rgb = self._convert_np_to_img(frame)
        frame_rgb = self._crop_frame(frame_rgb)

    def _decode_pulse(self, pulse_duration_seconds):
        """Attempts to decode a pulse into a dot or dash"""
        acceptable_deviation_seconds = 0.15
        upper_boundary = (self.time_unit_dur * 1) + acceptable_deviation_seconds
        lower_boundary = (self.time_unit_dur * 1) - acceptable_deviation_seconds
        if upper_boundary > pulse_duration_seconds > lower_boundary:
            logging.debug('Detected "."')
            return self.DOT
        upper_boundary = (self.time_unit_dur * 3) + acceptable_deviation_seconds
        lower_boundary = (self.time_unit_dur * 3) - acceptable_deviation_seconds
        if upper_boundary > pulse_duration_seconds > lower_boundary:
            logging.debug('Detected "-"')
            return self.DASH
        return None

    def _decode_break(self, break_duration_seconds):
        """Attempts to decode a break into an intra-character, inter-character, or inter-word break"""
        acceptable_deviation_seconds = 0.1
        upper_boundary = (self.time_unit_dur * 1) + acceptable_deviation_seconds
        lower_boundary = (self.time_unit_dur * 1) - acceptable_deviation_seconds
        if upper_boundary > break_duration_seconds > lower_boundary:
            logging.debug('Detected intra-character break')
            return self.INTRACHARACTER_BREAK
        acceptable_deviation_seconds = 0.15
        upper_boundary = (self.time_unit_dur * 3) + acceptable_deviation_seconds
        lower_boundary = (self.time_unit_dur * 3) - acceptable_deviation_seconds
        if upper_boundary > break_duration_seconds > lower_boundary:
            logging.debug('Detected inter-character break')
            return self.INTERCHARACTER_BREAK
        acceptable_deviation_seconds = 0.4
        upper_boundary = (self.time_unit_dur * 7) + acceptable_deviation_seconds
        lower_boundary = (self.time_unit_dur * 7) - acceptable_deviation_seconds
        if upper_boundary > break_duration_seconds > lower_boundary:
            logging.debug('Detected inter-word break')
            return self.INTERWORD_BREAK
        return self.EXTENDED_BREAK

    def _interpret_character(self, msg):
        """Interprets a character received from the lights"""
        if msg == self.DOT:
            self.running_character = self.running_character + '.'
            return
        if msg == self.DASH:
            self.running_character = self.running_character + '-'
            return
        if msg == self.INTRACHARACTER_BREAK:
            return
        if msg == self.INTERCHARACTER_BREAK:
            char = mtalk.decode(self.running_character)
            self.running_character = ''
            self.running_message = self.running_message + char
            logging.info(self.running_message)
            return
        if msg == self.INTERWORD_BREAK:
            self.running_character = ''
            self.running_message = self.running_message + ' '
            logging.info(self.running_message)
            return

    def _decode_pulses(self):
        """Decodes timeunits of currently running pipeline"""
        start_time = None
        stop_time = None
        while True:
            start_time = time.time()
            stop_time = None
            while not self.binary:
                """Light is currently off"""
                stop_time = time.time()
            off_duration = stop_time - start_time
            msg = self._decode_break(off_duration)
            self._interpret_character(msg)
            start_time = time.time()
            stop_time = None
            while self.binary:
                """Light is currently on"""
                stop_time = time.time()
            on_duration = stop_time - start_time
            msg = self._decode_pulse(on_duration)
            self._interpret_character(msg)

    def _start_pipeline(self):
        """Starts the pipeline"""
        self.flask_thread = threading.Thread(name='pipeline', target=self._run_pipeline)
        self.flask_thread.start()

    def _run_pipeline(self):
        """Run the signal processing pipeline"""
        logging.info('Starting pipeline')
        while True:
            logging.info('frame')
            fps_start = start_time = time.time()
            frame = self.stream.get_frame()
            if self.stream.is_frame_empty(frame):
                logging.error('empty frame')
                time.sleep(1)
                continue
            image = self._convert_np_to_img(frame)
            image = self._crop_frame(image)
            average = self._get_average_brightness(image)
            self.binary = self._convert_8_bit_to_bin(average)
            self.fps = 1.0 / (time.time() - fps_start)
            time.sleep(0.01)

    def calibrate(self):
        """Allow calibration"""
        logging.info('Calibrating signal')
        frame = self.stream.get_frame()
        while self.stream.is_frame_empty(frame):
            frame = self.stream.get_frame()
        calibrator = SignalCalibrator()
        self.crop_coordinates = calibrator.get_coordinates(frame)
        logging.info(self.crop_coordinates)
        del calibrator
        for i in range(1, 10):
            cv2.destroyAllWindows()
            cv2.waitKey(1)

    def start(self):
        """Starts the application"""
        logging.info('Starting application')
        try:
            self.calibrate()
            self._start_pipeline()
            self._decode_pulses()
        except KeyboardInterrupt:
            logging.info('Exiting')


if __name__ == '__main__':
    mr = MorseReceiver()
    mr.start()
