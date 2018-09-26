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
from selenium.webdriver.support.wait import WebDriverWait

from doc_scraper.extensions import socketio
from doc_scraper.logging import LOGGER
from doc_scraper.utils import normalize_url, trim
from doc_scraper.errors import ApplicationError
from doc_scraper.settings import DEBUG, IMAGE_DIR, INFO_NAMESPACE


def run_job(req_id, url, email, password):
    LOGGER.info("job: %s url: %s email: %s", req_id, url, email)
    image_paths = []
    try:
        url, id_ = normalize_url(url)
        browser = setup_browser()
        load_first_page(browser, url)
        stage_update(req_id, 'setting auth')
        send_auth(browser, email, password)
        stage_update(req_id, 'loading slides')
        urls = load_pages(browser)
        stage_update(req_id, 'converting to images')
        image_paths = save_pages(req_id, browser, urls)
        stage_update(req_id, 'creating PDF')
        pdf = generate_pdf(req_id, image_paths)
        stage_update(req_id, 'done')
        browser.close()
    finally:
        for i in image_paths:
            os.remove(i)
    return pdf


def stage_update(req_id, stage):
    socketio.emit('stage update', {'stage': stage},
                  namespace=INFO_NAMESPACE, room=req_id)
    LOGGER.info("stage updated: %s request: %s", stage, str(req_id))


def setup_browser():
    chrome_options = Options()
    if not DEBUG:
        chrome_options.add_argument("--headless")
    driver_path = './chromedriver' if platform.system() == "Darwin" else './chromedriver_linux'
    return webdriver.Chrome(driver_path, chrome_options=chrome_options)


def load_first_page(browser, url):
    browser.get(url)
    socketio.sleep(2)
    try:
        element = WebDriverWait(browser, 4).until(
            EC.presence_of_element_located((By.ID, "youtube-modal"))
        )
    except TimeoutException:
        LOGGER.error("failed")
        if browser.title == '404 Page Not Found':
            raise ApplicationError(f'`{browser.current_url}` returned a 404')
        else:
            raise


def send_auth(browser, email, password):
    """Send email and password input if required"""
    try:
        email_element = browser.find_element_by_name('visitor[email]')
        email_element.send_keys(email)
        socketio.sleep(1)
    except:
        LOGGER.debug("no e-mail required")
        return
    try:
        pass_element = browser.find_element_by_name('visitor[passcode]')
        pass_element.send_keys(password)
    except:
        LOGGER.debug("no password required")
    email_element.send_keys(Keys.TAB)
    email_element.send_keys(Keys.ENTER)
    socketio.sleep(1)


def load_pages(browser):
    """Clicks right until no blank pages. check until pages stabilizes"""
    is_stable = False
    browser.switch_to_active_element().send_keys(Keys.RIGHT)
    urls = []
    while not is_stable:
        browser.switch_to_active_element().send_keys(Keys.RIGHT)
        # not sure why this is random...
        socketio.sleep(0.4 + random.randint(1, 100) / 100)
        pages = browser.find_elements_by_css_selector(".preso-view.page-view")
        urls = [page.get_attribute("src") for page in pages]
        if any("blank.gif" in s for s in urls):
            is_stable = False
        else:
            is_stable = True

    return urls


def save_pages(req_id, browser, urls):
    """Save each page as a png and return a list of paths to the saved images"""
    image_paths = []
    for page_num, url in enumerate(urls, 1):
        socketio.emit("page update", {'page': page_num},
                      namespace=INFO_NAMESPACE, room=req_id)
        browser.get(url)
        image_path = f"{IMAGE_DIR}/{req_id}_{page_num}.png"
        socketio.sleep(1)
        browser.save_screenshot(image_path)
        im = Image.open(image_path)
        trimmed_im = trim(im)
        im.close()
        trimmed_im.save(image_path)
        image_paths.append(image_path)
    return image_paths


def generate_pdf(req_id, image_paths):
    """Take the images and create a PDF"""
    if not image_paths:
        raise ApplicationError("No images")
    im = Image.open(image_paths[0])
    wheight = im.size[0]
    wwidth = im.size[1]
    im.close()

    pdf = FPDF("L", "pt", [wwidth, wheight])
    pdf.set_margins(0, 0, 0)

    for page_num, image_path in enumerate(image_paths, 1):
        socketio.emit("page update", {'page': page_num},
                      namespace=INFO_NAMESPACE, room=req_id)
        pdf.add_page()
        pdf.image(image_path, 0, 0)
    return pdf
