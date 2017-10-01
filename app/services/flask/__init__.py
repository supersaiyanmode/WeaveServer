from .service import FlaskServer

__disabled_meta__ = {
    "name": "Flask Web Server",
    "class": FlaskServer,
    "deps": ["logging", "messaging"],
    "config": [
        {
            "name": "flask_config",
            "loaders": [
                {"path": "flask_config.py", "type": "pyconfig"}
            ]
        }
    ]
}