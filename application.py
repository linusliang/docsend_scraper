import os
import platform
import time
import random
import logging

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
    if DEBUG_FLAG:
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


def send_email(browser, email):
    """Check if there's email input"""
    try:
        email_element = browser.find_element_by_name('visitor[email]')
        email_element.send_keys(email)
        time.sleep(1)
    except:
        logging.debug("no e-mail required")


@application.route('/savepdf', methods = ['POST'])
def savepdf(url="", emailad="", emailpass=""):

    # Check if it exists
    url = request.form['url']
    emailad = request.form['emailad'].encode("ascii")
    emailpass = request.form['emailpass'].encode("ascii")

    url, id_ = normalize_url(url)
    browser = setup_browser()
    load_first_page(browser, url)
    send_email(browser, emailad)

    # Check if there's password input
    
    try:
        pass_ID = browser.find_element_by_name('visitor[passcode]')
        pass_ID.send_keys(emailpass)
    except:
        print("no password required")
    time.sleep(1)    
    try:
        email_ID.send_keys(Keys.TAB)
        email_ID.send_keys(Keys.ENTER)
    except:
        print("ae")
    
    exitflag = 0
    browser.switch_to_active_element().send_keys(Keys.RIGHT)
    
    while exitflag == 0:
        #click right until no blank pagescheck until pages stabilizes
        browser.switch_to_active_element().send_keys(Keys.RIGHT)
        time.sleep(0.4+random.randint(1,100)/100)
        pages = browser.find_elements_by_css_selector(".preso-view.page-view")
        urls = []
        for x in pages:
            urls.append(x.get_attribute("src"))
        if any("blank.gif" in s for s in urls):
            exitflag = 0
        else:
            exitflag = 1
            
    urls = []
    for x in pages:
        urls.append(x.get_attribute("src"))
        
    c = 1
    for x in urls:
        browser.get(x)
        browser.save_screenshot("AX"+str(c)+".png")
        c = c+1
        
    imagelist = []
    for i in range(1,c):
        imagelist.append("AX"+str(i)+".png")
     
    time.sleep(10)   
    for img in imagelist:
        im = Image.open(img)
        im = trim(im)
        im.save(img)
    
    im = Image.open(imagelist[0])
    wheight = im.size[0]
    wwidth = im.size[1]
    im.close()    
    
    pdf = FPDF("L","pt",[wwidth,wheight])
    pdf.set_margins(0,0,0)
    
    for image in imagelist:
        pdf.add_page()
        pdf.image(image,0,0)
        
    for i in (imagelist):
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
    application.run(host='0.0.0.0')