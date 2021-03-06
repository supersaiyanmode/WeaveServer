import logging
from threading import Event, Thread

from pywebostv.connection import WebOSClient
from pywebostv.controls import MediaControl, SystemControl
from pywebostv.controls import ApplicationControl, InputControl

from app.core.netutils import get_mac_address
from app.core.rpc import ServerAPI, ArgParameter, RPCServer


logger = logging.getLogger(__name__)


def get_apis(client):
    media = MediaControl(client)
    system = SystemControl(client)
    app = ApplicationControl(client)
    inp = InputControl(client)

    return [
        ServerAPI("mute", "Mute the TV", [
            ArgParameter("state", "True to mute, False to unmute", bool)
        ], media.mute),
        ServerAPI("volume_up", "Increase Volume", [], media.volume_up),
        ServerAPI("volume_down", "Decrease Volume", [], media.volume_down),
        ServerAPI("set_volum", "Set Volume", [
            ArgParameter("level", "Volume Level", int)
        ], media.set_volume),
        ServerAPI("play", "Play", [], media.play),
        ServerAPI("pause", "Pause", [], media.pause),
        ServerAPI("rewind", "Rewind", [], media.rewind),
        ServerAPI("fast_forward", "Fast Forward", [], media.fast_forward),


        ServerAPI("power_off", "Power off TV", [], system.power_off),
        ServerAPI("notify", "Send notification", [
            ArgParameter("text", "Text to notify", str)
        ], system.notify),


        ServerAPI("type", "Send text input", [
            ArgParameter("text", "Text to insert", str)
        ], inp.type),
        ServerAPI("delete", "Delete text", [
            ArgParameter("count", "No of characters to delete", int)
        ], inp.delete),
        ServerAPI("enter", "Press Enter", [], inp.enter),
    ]


class WebOSTV(object):
    def __init__(self, service, mac, client):
        store = {'client_key': 'c2a6e6a1a8ebf46ccddaabaf7c15bad6'}
        client.connect()
        list(client.register(store))

        self.mac = mac
        apis = get_apis(client)
        self.rpc = RPCServer("LG TV Commands", "Remote control for LG TVs.",
                             apis, service)

    def start(self):
        self.rpc.start()

    def stop(self):
        self.rpc.stop()


class WebOsScanner(object):
    SCAN_INTERVAL = 300

    def __init__(self, service):
        self.service = service
        self.shutdown = Event()
        self.scanner_thread = Thread(target=self.run)
        self.discovered_clients = {}
        self.store = {}

    def start(self):
        self.scan()
        self.scanner_thread.start()

    def stop(self):
        self.shutdown.set()
        self.scanner_thread.join()

    def run(self):
        while not self.shutdown.is_set():
            self.scan()
            self.shutdown.wait(timeout=self.SCAN_INTERVAL)

    def scan(self):
        new_clients = {}
        for client in WebOSClient.discover():
            logger.info("Found an LG Web OS TV at: %s", client.url)
            mac = get_mac_address(client.host)
            if mac not in self.discovered_clients:
                webos_tv = WebOSTV(self.service, mac, client)
                new_clients[mac] = webos_tv
                webos_tv.start()

        for key in set(self.discovered_clients.keys()) - set(new_clients):
            self.discovered_clients.pop(key)

        self.discovered_clients.update(new_clients)
