"""HackFlow Application Entry Point."""

import os
from dotenv import load_dotenv

load_dotenv()

from hackflow import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"

    app.run(host=host, port=port, debug=debug)
