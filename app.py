"""Entry point for `flask run` / `python app.py`."""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # debug=False so the metrics scheduler starts in this process
    app.run(host="127.0.0.1", port=5000, debug=False)
