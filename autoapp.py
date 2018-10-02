import os

from doc_scraper.app import create_app, socketio
from doc_scraper.settings import IMAGE_DIR

os.makedirs(IMAGE_DIR, exist_ok=True)
app = create_app()


if __name__ == '__main__':
    socketio.run(app, '0.0.0.0')
