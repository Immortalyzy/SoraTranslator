# run_server.py
import os, socket, sys, time
from waitress import serve
from app import create_app  # your Flask factory or app


def find_free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("SORA_BACKEND_PORT") or find_free_port())
    # Print the port so Electron can read it
    print(f"PORT={port}", flush=True)
    serve(app, host="127.0.0.1", port=port, threads=8)
