from PIL import Image, ImageChops

from doc_scraper.errors import ApplicationError


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
