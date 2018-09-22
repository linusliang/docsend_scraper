import os
import platform
import time
import random
import logging
import uuid

from flask import Flask, render_template, request, make_response
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.keys import Keys
from flask_bootstrap import Bootstrap
from fpdf import FPDF
from PIL import Image, ImageChops


# Setting debug to True enables debug output.
DEBUG_FLAG = bool(os.getenv("DEBUG"))


# EB looks for an 'application' callable by default.
application = Flask(__name__)
bootstrap = Bootstrap(application)
def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((50,50)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -10)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)


def setup_browser():
    chrome_options = Options()
    if not DEBUG_FLAG:
        chrome_options.add_argument("--headless")
    driver_path = './chromedriver' if platform.system() == "Darwin" else './chromedriver_linux'
    return webdriver.Chrome(driver_path, chrome_options=chrome_options)


class ApplicationError(Exception):
    pass


def normalize_url(url_or_id):
    if 'docsend.com/view' in url_or_id:
        loc = str.find(url_or_id, "view")
        id_ = url_or_id[loc + 5:]
    elif url_or_id.isalnum():
        id_ = url_or_id
    else:
        raise ApplicationError(f"`{url_or_id}` is not a valid url or id")
    return f'https://docsend.com/view/{id_}', id_


def load_first_page(browser, url):
    browser.get(url)
    time.sleep(2)
    try:
        element = WebDriverWait(browser, 4).until(
            EC.presence_of_element_located((By.ID, "youtube-modal"))
        )
    except TimeoutException as err:
        logging.error("failed")
        if browser.title == '404 Page Not Found':
            raise ApplicationError(f'`{browser.current_url}` returned a 404')
        else:
            raise


def send_auth(browser, email, password):
    """Send email and password input if required"""
    try:
        email_element = browser.find_element_by_name('visitor[email]')
        email_element.send_keys(email)
        time.sleep(1)
    except:
        logging.debug("no e-mail required")
        return
    try:
        pass_element = browser.find_element_by_name('visitor[passcode]')
        pass_element.send_keys(password)
    except:
        logging.debug("no password required")
    email_element.send_keys(Keys.TAB)
    email_element.send_keys(Keys.ENTER)
    time.sleep(1)


def load_pages(browser):
    """Clicks right until no blank pages. check until pages stabilizes"""
    is_stable = False
    browser.switch_to_active_element().send_keys(Keys.RIGHT)
    pages = []
    while not is_stable:
        browser.switch_to_active_element().send_keys(Keys.RIGHT)
        # not sure why this is random...
        time.sleep(0.4 + random.randint(1, 100) / 100)
        pages = browser.find_elements_by_css_selector(".preso-view.page-view")
        urls = []
        for x in pages:
            urls.append(x.get_attribute("src"))
        if any("blank.gif" in s for s in urls):
            is_stable = False
        else:
            is_stable = True

    return pages


def save_pages(req_id, browser, pages):
    """Save each page as a png and return a list of paths to the saved images"""
    image_paths = []
    for page_num, page in enumerate(pages, 1):
        url = page.get_attribute("src")
        browser.get(url)
        image_path = f"{req_id}_{page_num}.png"
        time.sleep(1)
        browser.save_screenshot(image_path)
        im = Image.open(image_path)
        trimmed_im = trim(im)
        im.close()
        trimmed_im.save(image_path)
        image_paths.append(image_path)
    return image_paths


@application.route('/savepdf', methods = ['POST'])
def savepdf(url="", emailad="", emailpass=""):

    req_id = uuid.uuid4()
    url = request.form['url']
    emailad = request.form['emailad'].encode("ascii")
    emailpass = request.form['emailpass'].encode("ascii")

    url, id_ = normalize_url(url)
    browser = setup_browser()
    load_first_page(browser, url)
    send_auth(browser, emailad, emailpass)
    pages = load_pages(browser)
    image_paths = save_pages(req_id, browser, pages)

    im = Image.open(image_paths[0])
    wheight = im.size[0]
    wwidth = im.size[1]
    im.close()
    
    pdf = FPDF("L","pt",[wwidth,wheight])
    pdf.set_margins(0,0,0)
    
    for image in image_paths:
        pdf.add_page()
        pdf.image(image,0,0)
        
    for i in (image_paths):
        os.remove(i)
    
    cdir = os.getcwd()        
    browser.close()  

    # now serve the PDF
    response = make_response(pdf.output(dest='S'))
    response.headers.set('Content-Disposition', 'attachment', filename=id_ + '.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response


@application.route('/')
def serve_front_page():
    return render_template('index.html')

# run the app.
if __name__ == "__main__":
    application.debug = DEBUG_FLAG
    if DEBUG_FLAG:
        logging.root.setLevel(logging.DEBUG)
    application.run(host='0.0.0.0')