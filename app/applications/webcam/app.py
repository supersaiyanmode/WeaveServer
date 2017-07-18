import logging

from app.core.base_app import BaseApp, BaseCommandsListener
from app.core.base_app import BaseWebSocket

logger = logging.getLogger(__name__)


class WebcamCommandListener(BaseCommandsListener):
    COMMANDS = [
        {
            "name": "Click!",
            "cmd": "click"
        }
    ]

    def __init__(self, app):
        self.app = app

    def on_command(self, command):
        func = getattr(self.app, "handle_" + command.lower(), None)
        if func is None:
            return None
        func()
        return "OK"

    def list_commands(self):
        return self.COMMANDS


class WebcamSocket(BaseWebSocket):
    def __init__(self, app, socketio):
        self.app = app
        super().__init__("/app/webcam", socketio)

    def on_image(self, data):
        logger.info("Received image!")

    def notify_click(self):
        self.reply_all("click", {})

class WebcamApp(BaseApp):
    ICON = "fa-camera"
    NAME = "Webcam"
    DESCRIPTION = "Click photos from webcam."

    def __init__(self, service, socketio):
        self.socket = WebcamSocket(self, socketio)
        self.listener = WebcamCommandListener(self)
        super().__init__(self.socket, self.listener)

    def html(self):
        with open(self.get_file("static/index.html")) as inp:
            return inp.read()

    def on_command(self, command):
        self.listener.on_command(command)

    def list_commands(self):
        self.listener.list_commands()

    def handle_click(self):
        self.socket.notify_click()

