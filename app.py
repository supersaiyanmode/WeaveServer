import socketio

from app.main import create_app


if __name__ == '__main__':
    flask_app, sock_app = create_app()

    port = flask_app.config["PORT"]

    sock_app.run(flask_app, host="", debug=True, use_reloader=False)

