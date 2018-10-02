from flask import request, render_template, make_response, Blueprint

from doc_scraper.extensions import socketio
from doc_scraper.settings import INFO_NAMESPACE
from doc_scraper.errors import ApplicationError
from doc_scraper.logger import LOGGER
from doc_scraper.slidedeck import SlideDeck
from doc_scraper.settings import IMAGE_DIR


blueprint = Blueprint('main', __name__, template_folder='templates')

@blueprint.route('/savepdf', methods=['POST'])
def savepdf():
    url = request.form['url']
    emailad = request.form['emailad'].encode("ascii")
    emailpass = request.form['emailpass'].encode("ascii")
    req_id = request.form['id']
    id_ = url[25:]
    try:
        slidedeck = SlideDeck(url, emailad, emailpass, IMAGE_DIR)
        pdf = slidedeck.convert_to_pdf(req_id)
        id_ = slidedeck.id_
        response = make_response(pdf.output(dest='S').encode('latin1'))
    except ApplicationError as err:
        LOGGER.error(err.args[0])
        socketio.emit('error update',
                      {'detail': err.args[0]},
                      namespace=INFO_NAMESPACE,
                      room=req_id)
        response = make_response("")
    response.headers.set('Content-Disposition',
                         'attachment', filename=id_ + '.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response


@blueprint.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)
