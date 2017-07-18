

class RoutesManager(object):
    """
    Used to dynamically add/remove routes from the flask app
    """

    def __init__(self, app):
        self.app = app

    def register(self, url, handler):
        self.app.add_url_name(url, handler)

    def unregister(self, url):
        pass
