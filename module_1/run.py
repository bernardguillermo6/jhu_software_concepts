#!/usr/bin/env python3
from app import create_app

app = create_app()  # create Flask app instance

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8080)