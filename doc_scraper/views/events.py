from flask import request
from flask_socketio import join_room

from doc_scraper.extensions import socketio
from doc_scraper.settings import INFO_NAMESPACE
from doc_scraper.logger import LOGGER


@socketio.on("join", namespace=INFO_NAMESPACE)
def join(message):
    join_room(message['room'])
    LOGGER.debug('%s joined room %s in namespace %s',
                 request.sid,
                 message['room'],
                 request.namespace)
