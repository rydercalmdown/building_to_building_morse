import os
import cv2
from pynput import mouse, keyboard


class SignalCalibrator():
    """GUI for allowing the user to identify a point of light"""

    def __init__(self):
        self.mouse_x = None
        self.mouse_y = None
        self.x1 = None
        self.y1 = None
        self.x2 = None
        self.y2 = None
        self.drawing_in_progress = False
        self.drawing_complete = False
        self.window_name = 'default'

    def _on_mouse_move(self, x, y):
        """Callback for mouse movement"""
        logging.debug(f'Mouse Moved to x{x}, y{y}')
        self.mouse_x = x
        self.mouse_y = y

    def _on_mouse_click(self, x, y, button_index, depressed):
        """Callback for mouse click"""
        if not depressed:
            logging.debug(f'Mouse released at x{x}, y{y}, btn {button_index}')
            return False
        logging.debug(f'Mouse depressed at x{x}, y{y}, btn {button_index}')

    def _on_mouse_click_scroll(self, x, y, dx, dy):
        """Callback for mouse scroll"""
        logging.debug('Mouse scroll event')

    def _on_key_depress(self, key):
        """Callback for key depression"""
        logging.debug(f'"{key}" key depressed')
        self.active_key = key

    def _on_key_release(self, key):
        """Callback for key release"""
        logging.debug(f'"{key}" key released')
        self.active_key = key
        if key == keyboard.Key.esc:
            return False

    def _setup_listeners(self):
        """Sets up key and mouse listeners"""
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_depress,
            on_release=self._on_key_release
        )
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )

    def _define_bounding_box(self, event, x, y, flags, params):
        """Callback for defining the bounding box"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing_in_progress = True
            self.x1, self.y1 = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing_in_progress = False
            self.drawing_complete = True
            self.x2, self.y2 = x, y
        # else:
        #     if x and y:
        #         cv2.rectangle(
        #             self.image,
        #             (self.x1, self.y1),
        #             (x,y),
        #             (255, 255, 0),
        #             2)

    def _create_named_window(self):
        """Defines the named window for the process"""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)  
        cv2.setMouseCallback(self.window_name, self._define_bounding_box)
        cv2.setWindowProperty(self.window_name,
            cv2.WND_PROP_FULLSCREEN,
            cv2.WINDOW_FULLSCREEN)
    
    def _get_coordinates_dict(self):
        """Returns a dictionary of coordinates"""
        return {
            'x1': self.x1,
            'y1': self.y1,
            'x2': self.x2,
            'y2': self.y2,
        }

    def get_coordinates(self, image):
        """Draw on particular image, returns coordinates"""
        self.image = image
        self._create_named_window()
        while not self.drawing_complete:
            cv2.imshow(self.window_name, self.image)
            cv2.waitKey(10)
        cv2.destroyAllWindows()
        return self._get_coordinates_dict()
