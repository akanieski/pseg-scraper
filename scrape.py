

import time
import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from flask import Flask, request, make_response

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option('prefs', {
    'download.prompt_for_download': False,
    'plugins.always_open_pdf_externally': True,
    'download.default_directory': os.getcwd()
})


def init_driver():
    driver = webdriver.Chrome(chrome_options=chrome_options)
    # driver = webdriver.PhantomJS()
    driver.wait = WebDriverWait(driver, 5)
    return driver


def get_available_dates(username, password):
    try:
        driver = init_driver()

        driver.get("https://myaccount.pseg.com/SSOLogin/login.htm")
        box = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "username")))
        box2 = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "password")))
        button = driver.wait.until(EC.element_to_be_clickable(
            (By.ID, "submit")))
        box.send_keys(username)
        box2.send_keys(password)
        button.click()

        print driver.current_url

        driver.get('https://myaccount.pseg.com/psegbdisu/public/index.jsp')

        driver.switch_to_frame(
            driver.find_element_by_name('billerdirect_content'))

        selections = driver.find_element_by_id('selectedDate')

        print len(selections.find_elements_by_tag_name('option'))

        return [option.get_attribute('value') for option in selections.find_elements_by_tag_name('option') if option.get_attribute('value') != 'V']

    except Exception as ex:
        print ex


def lookup(username, password, date_str):
    try:
        driver = init_driver()

        driver.get("https://myaccount.pseg.com/SSOLogin/login.htm")
        box = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "username")))
        box2 = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "password")))
        button = driver.wait.until(EC.element_to_be_clickable(
            (By.ID, "submit")))
        box.send_keys(username)
        box2.send_keys(password)
        button.click()

        driver.get('https://myaccount.pseg.com/psegbdisu/public/index.jsp')

        driver.switch_to_frame(
            driver.find_element_by_name('billerdirect_content'))

        selections = driver.find_element_by_id('selectedDate')

        found = False
        for option in selections.find_elements_by_tag_name('option'):
            if option.get_attribute('value') == date_str:
                found = True
                option.click()
                break
        
        if not found:
            return 'ERROR: No statement found for given date ' + date_str
        
        stmt_button = driver.find_element_by_css_selector('.dataleft a')

        stmt_button.click()

        popup = driver.window_handles[1]

        driver.switch_to_window(popup)

        # rename resulting downloaded file
        time.sleep(3)

        os.rename('getPDFforBillView.sap', 'pseg-statement.pdf')
        driver.quit()

        with open('pseg-statement.pdf', mode='rb') as file:
            fileContent = file.read()
        os.remove('pseg-statement.pdf')

        return fileContent

    except Exception as ex:
        print ex


# if __name__ == "__main__":
    # lookup(os.environ['USERNAME'], os.environ['PASSWORD'])

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/statements/<date_str>")
def get_statement(date_str):
    b = lookup(request.headers.get('pseg_username'), request.headers.get('pseg_password'), date_str)

    r = make_response(b)
    r.headers['Content-Type'] = 'application/pdf'
    r.headers['Content-Disposition'] = 'attachment; filename=statement.pdf'
    return r


@app.route("/statement-dates")
def get_statement_dates():
    b = get_available_dates(request.headers.get('pseg_username'), request.headers.get('pseg_password'))

    r = make_response(json.dumps(b))
    r.headers['Content-Type'] = 'application/json'
    return r
