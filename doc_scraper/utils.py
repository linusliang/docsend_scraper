from PIL import Image, ImageChops

from doc_scraper.errors import ApplicationError
from doc_scraper.extensions import socketio
from doc_scraper.logger import LOGGER
from doc_scraper.settings import INFO_NAMESPACE


def normalize_url(url_or_id):
    if 'docsend.com/view' in url_or_id:
        loc = str.find(url_or_id, "view")
        id_ = url_or_id[loc + 5:]
    elif url_or_id.isalnum():
        id_ = url_or_id
    else:
        raise ApplicationError(f"`{url_or_id}` is not a valid url or id")
    return f'https://docsend.com/view/{id_}', id_


def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((50, 50)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -10)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)


def stage_update(req_id, stage):
    socketio.emit('stage update', {'stage': stage},
                  namespace=INFO_NAMESPACE, room=req_id)
    LOGGER.info("stage updated: %s request: %s", stage, req_id)


def page_update(req_id, page_num):
    socketio.emit('page update', {'page': page_num},
                  namespace=INFO_NAMESPACE, room=req_id)
    LOGGER.info("page updated: %s request: %s", page_num, req_id)
