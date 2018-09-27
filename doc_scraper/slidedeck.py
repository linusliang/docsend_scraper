import os
import platform
import random

from PIL import Image
from fpdf import FPDF
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from doc_scraper.utils import sleep, stage_update, page_update
from doc_scraper.logging import LOGGER
from doc_scraper.errors import ApplicationError
from doc_scraper.utils import normalize_url, trim


class SlideDeck():
    def __init__(self, url, email, password, image_dir, debug=False):
        self.url, self.id_ = normalize_url(url)
        self.browser = self._setup_browser(debug=debug)
        self.image_dir = image_dir
        self.images = []
        self._load_first_page()
        self._send_auth(email, password)

    def convert_to_pdf(self, req_id):
        try:
            stage_update(req_id, 'loading slides')
            urls = self._load_pages()
            stage_update(req_id, 'converting to images')
            self._save_pages(req_id, urls)
            self.browser.close()
            stage_update(req_id, 'creating PDF')
            pdf = self._generate_pdf(req_id)
            stage_update(req_id, 'done')
        except Exception as err:
            raise ApplicationError(str(err))
        finally:
            for i in self.images:
                os.remove(i)

        return pdf

    def _setup_browser(self, debug=False):
        chrome_options = Options()
        if not debug:
            chrome_options.add_argument("--headless")
        driver_path = './chromedriver' if platform.system() == "Darwin" else './chromedriver_linux'
        return webdriver.Chrome(driver_path, chrome_options=chrome_options)

    def _load_first_page(self):
        self.browser.get(self.url)
        sleep(2)
        try:
            WebDriverWait(self.browser, 4).until(
                EC.presence_of_element_located((By.ID, "youtube-modal"))
            )
        except TimeoutException:
            LOGGER.error("failed")
            if self.browser.title == '404 Page Not Found':
                raise ApplicationError(f'`{self.browser.current_url}` returned a 404')
            else:
                raise

    def _send_auth(self, email, password):
        """Send email and password input if required"""
        try:
            email_element = self.browser.find_element_by_name('visitor[email]')
            email_element.send_keys(email)
            sleep(1)
        except:
            LOGGER.debug("no e-mail required")
            return
        try:
            pass_element = self.browser.find_element_by_name('visitor[passcode]')
            pass_element.send_keys(password)
        except:
            LOGGER.debug("no password required")
        email_element.send_keys(Keys.TAB)
        email_element.send_keys(Keys.ENTER)
        sleep(1)


    def _load_pages(self):
        """Clicks right until no blank pages. check until pages stabilizes"""
        is_stable = False
        self.browser.switch_to_active_element().send_keys(Keys.RIGHT)
        urls = []
        while not is_stable:
            self.browser.switch_to_active_element().send_keys(Keys.RIGHT)
            # not sure why this is random...
            sleep(0.4 + random.randint(1, 100) / 100)
            pages = self.browser.find_elements_by_css_selector(".preso-view.page-view")
            urls = [page.get_attribute("src") for page in pages]
            if not any("blank.gif" in s for s in urls):
                is_stable = True

        return urls


    def _save_pages(self, req_id, urls):
        """Save each page as a png and store the paths in self.images"""
        for page_num, url in enumerate(urls, 1):
            page_update(req_id, page_num)
            self.browser.get(url)
            image_path = f"{self.image_dir}/{req_id}_{page_num}.png"
            sleep(1)
            self.browser.save_screenshot(image_path)
            im = Image.open(image_path)
            trimmed_im = trim(im)
            im.close()
            trimmed_im.save(image_path)
            self.images.append(image_path)


    def _generate_pdf(self, req_id):
        """Take the images and create a PDF"""
        if not self.images:
            raise ApplicationError("No images")
        im = Image.open(self.images[0])
        wheight = im.size[0]
        wwidth = im.size[1]
        im.close()

        pdf = FPDF("L", "pt", [wwidth, wheight])
        pdf.set_margins(0, 0, 0)

        for page_num, image_path in enumerate(self.images, 1):
            page_update(req_id, page_num)
            pdf.add_page()
            pdf.image(image_path, 0, 0)
        return pdf
