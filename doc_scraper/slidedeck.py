import os

from PIL import Image
from fpdf import FPDF
from requests import Session
from bs4 import BeautifulSoup

from doc_scraper.utils import stage_update, page_update
from doc_scraper.logger import LOGGER
from doc_scraper.errors import ApplicationError
from doc_scraper.utils import normalize_url, trim


class SlideDeck():
    def __init__(self, url, email, password, image_dir):
        self.url, self.id_ = normalize_url(url)
        self.session = Session()
        self._setup()
        resp = self.session.get(self.url)
        self.soup = BeautifulSoup(resp.content, features="html.parser")
        self._send_auth(email, password)
        self.image_dir = image_dir

    def convert_to_pdf(self, req_id):
        """Convert the slidedeck to a pdf and return it"""
        try:
            stage_update(req_id, 'processing')
            pdf = self._generate_pdf(req_id)
            stage_update(req_id, 'done')
        except Exception as err:
            raise ApplicationError(str(err))
        return pdf

    def _setup(self):
        """set up the requests.Session"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh;'
                          ' Intel Mac OS X 10_12_6)'
                          ' AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/69.0.3497.100 Safari/537.36'
        }
        self.session.headers = headers

    def _send_auth(self, email, password):
        """Send email and password input if required"""
        email_input_name = 'link_auth_form[email]'
        password_input_name = 'link_auth_form[passcode]'
        auth_flag = False

        # this has extra inputs but doesn't seem to affect the form post
        input_elements = self.soup.find_all('input')
        form = {element['name']: element.get('value') for element in input_elements}

        if email_input_name in form:
            auth_flag = True
            LOGGER.debug("%s: e-mail required", self.url)
            if not email:
                raise ApplicationError("email required")
            form[email_input_name] = email
        if password_input_name in form:
            auth_flag = True
            LOGGER.debug("%s: password required", self.url)
            if not password:
                raise ApplicationError("password required")
            form[email_input_name] = password

        if auth_flag:
            self.soup = BeautifulSoup(self.session.post(self.url, form).content,
                                      features="html.parser")

    def _load_pages(self):
        """Clicks right until no blank pages. check until pages stabilizes"""
        resp = self.session.get(self.url)
        soup = BeautifulSoup(resp.content, features="html.parser")
        for img_data_node in soup.find_all('img', {"class": "preso-view page-view"}):
            resp = self.session.get(img_data_node['data-url'])
            yield resp.json()['imageUrl']

    def _save_pages(self, req_id):
        """Save each page as a png and store the paths in self.images"""
        for page_num, url in enumerate(self._load_pages(), 1):
            image_path = f"{self.image_dir}/{req_id}_{page_num}.png"
            resp = self.session.get(url, stream=True)
            with open(image_path, 'wb') as fh:
                for chunk in resp.iter_content(decode_unicode=False):
                    fh.write(chunk)
            im = Image.open(image_path)
            trimmed_im = trim(im)
            im.close()
            trimmed_im.save(image_path)
            yield image_path
            os.remove(image_path)

    def _generate_pdf(self, req_id):
        """Take the images and create a PDF"""
        pdf = None
        for page_num, image_path in enumerate(self._save_pages(req_id), 1):
            page_update(req_id, page_num)
            if pdf is None:
                im = Image.open(image_path)
                wheight = im.size[0]
                wwidth = im.size[1]
                im.close()
                pdf = FPDF("L", "pt", [wwidth, wheight])
                pdf.set_margins(0, 0, 0)

            pdf.add_page()
            pdf.image(image_path, 0, 0)
        return pdf
