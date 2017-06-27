from app.system.updater import check_updates, do_upgrade, run_ansible
from app.views import SimpleBackgroundView
from .base import BaseService, BlockingServiceStart


class UpdaterService(BaseService, BlockingServiceStart):
    def __init__(self, observer=None):
        super().__init__(observer=observer)
        self._view = SimpleBackgroundView("Checking for updates.")
        self._view.args["subtitle"] = "Please wait ..."

    def on_service_start(self):
        values = check_updates()
        for val in values:
            self._view.args["subtitle"] = "Working with {}... ".format(str((val)))
            self.observer()
            do_upgrade([val])
        if values:
            self._view.args["subtitle"] = "Updating system configuration..."
            self.observer()
            run_ansible()

    def view(self):
        return self._view

