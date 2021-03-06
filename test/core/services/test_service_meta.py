from threading import Event, Thread

import pytest

from app.core.messaging import Receiver, Sender, SchemaValidationFailed
from app.core.services import EventDrivenService, BaseService, StatusService
from app.services.messaging import MessageService

from app.core.logger import configure_logging


configure_logging()


CONFIG = {
    "redis_config": {
        "USE_FAKE_REDIS": True
    },
    "queues": {
        "custom_queues": [
            {
                "queue_name": "/root/services",
                "queue_type": "keyedsticky",
                "request_schema": {
                    "type": "object"
                }
            }
        ]
    }
}


class Service(EventDrivenService, StatusService, BaseService):
    def on_service_start(self, *args, **kwargs):
        super().on_service_start(*args, **kwargs)
        self.value_event = Event()
        params = {
            "arg1": {"type": "string"}
        }
        self.express_capability("test", "testdesc", params, self.handle)
        self.event = self.express_event("event", "event-desc", params)

    def get_component_name(self):
        return "test"

    def handle(self, arg1):
        self.value = arg1
        self.value_event.set()

    def get_value(self):
        self.value_event.wait()
        return self.value


class TestEventDrivenService(object):
    @classmethod
    def setup_class(cls):
        event = Event()
        cls.message_service = MessageService(CONFIG)
        cls.message_service.notify_start = lambda: event.set()
        cls.message_service_thread = Thread(
            target=cls.message_service.on_service_start)
        cls.message_service_thread.start()
        event.wait()
        cls.service = Service()
        cls.service.on_service_start()

    @classmethod
    def teardown_class(cls):
        cls.message_service.on_service_stop()
        cls.message_service_thread.join()
        cls.service.on_service_stop()

    def test_bad_express_capability(self):
        with pytest.raises(TypeError):
            params = {"arg2": {"type": "string"}}
            self.service.express_capability("", "", params, self.service.handle)

    def test_express_simple_capability_with_bad_schema(self):
        receiver = Receiver("/services/test/capabilities")
        receiver.start()
        obj = receiver.receive()

        assert len(obj.task) == 1
        value = next(iter(obj.task.values()))
        value.pop("id")
        queue = value.pop("queue")
        assert value == {
            "name": "test",
            "description": "testdesc",
            "params": {"arg1": {"type": "string"}},
        }

        sender = Sender(queue)
        sender.start()
        with pytest.raises(SchemaValidationFailed):
            sender.send({"arg2": "new-value"})

    def test_service_registration(self):
        receiver = Receiver("/root/services")
        receiver.start()
        obj = receiver.receive().task

        assert obj == {"/services/test/": {}}

    def test_express_simple_capability_with_correct_schema(self):
        receiver = Receiver("/services/test/capabilities")
        receiver.start()
        obj = receiver.receive()

        assert len(obj.task) == 1
        value = next(iter(obj.task.values()))
        value.pop("id")
        queue = value.pop("queue")
        assert value == {
            "name": "test",
            "description": "testdesc",
            "params": {"arg1": {"type": "string"}},
        }

        sender = Sender(queue)
        sender.start()
        sender.send({"arg1": "new-value"})

        assert self.service.get_value() == "new-value"

    def test_express_event(self):
        receiver = Receiver("/services/test/events")
        receiver.start()
        obj = receiver.receive()

        assert len(obj.task) == 1
        value = next(iter(obj.task.values()))
        value.pop("id")
        queue = value.pop("queue")
        assert value == {
            "name": "event",
            "description": "event-desc",
            "params": {"arg1": {"type": "string"}}
        }

        event_receiver = Receiver(queue)
        event_receiver.start()

        self.service.event.fire(arg1="blah")

        obj = event_receiver.receive().task
        assert obj == {"arg1": "blah"}

    def test_update_status(self):
        receiver = Receiver("/services/test/status")
        receiver.start()

        self.service.update_status("test-status")

        receiver.receive().task == "test-status"
