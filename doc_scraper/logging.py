import logging


LOGGER = logging.getLogger('docsend_scraper')


def setup_logging(debug=False, verbose=False):
    logging.root.setLevel(logging.INFO)
    if debug or verbose:
        LOGGER.setLevel(logging.DEBUG)
    else:
        logging.getLogger('engineio').setLevel(logging.WARN)
        logging.getLogger('socketio').setLevel(logging.WARN)
    logging.basicConfig()
