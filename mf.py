from logzero import logger
import logzero

import selenium 
from selenium import webdriver 
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from alphavantage.price_history import PriceHistory

import requests

import os, time, datetime

class MoneyForward():
    def init(self):
        logger.info("selenium initializing...")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280x3200")
        options.add_argument("--disable-application-cache")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--hide-scrollbars")
        options.add_argument("--v=99")
        options.add_argument("--single-process")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--homedir=/tmp")
        options.add_experimental_option("prefs", {'profile.managed_default_content_settings.images':2})
        self.driver = webdriver.Chrome(chrome_options=options)
        self.wait = WebDriverWait(self.driver, 5)

    def login(self):
        self.driver.execute_script("window.open()")
        if not 'MF_ID' in os.environ or not 'MF_PASS' in os.environ:
            raise ValueError("env MF_ID and/or MF_PASS are not found.")
        mf_id = os.environ['MF_ID']
        mf_pass = os.environ['MF_PASS']
        
        self.driver.get('https://moneyforward.com/users/sign_in')
        self.wait.until(ec.presence_of_all_elements_located)
        
        self.send_to_element('//*[@id="sign_in_session_service_email"]', mf_id)
        self.send_to_element('//*[@id="sign_in_session_service_password"]', mf_pass)
        self.driver.find_element_by_xpath('//*[@id="login-btn-sumit"]').click()
        self.wait.until(ec.presence_of_all_elements_located)

    def portfolio(self):
        usdrate = self.usdrate()
        logger.info("USDJPY: " + str(usdrate))
        self.driver.get('https://moneyforward.com/bs/portfolio')
        self.wait.until(ec.presence_of_all_elements_located)
        elements = self.driver.find_elements_by_xpath('//*[@id="portfolio_det_eq"]/table/tbody/tr')
        for i in range(len(elements)):
            tds = elements[i].find_elements_by_tag_name('td')
            name = tds[1].text
            if name[0:3] == "RSU":
                rsuinfo = name.split('-')
                stock_price = self.stock_price(rsuinfo[1])
                stock_count = int(rsuinfo[2])
                logger.info(rsuinfo[0] + ": " + rsuinfo[1] + ' is ' + str(stock_price) + "USD (" + str(int(usdrate * stock_price)) + " JPY) x " + str(stock_count))
                tds[11].find_element_by_tag_name('img').click()
                det_value = tds[11].find_element_by_id('user_asset_det_value')
                commit = tds[11].find_element_by_name('commit')
                time.sleep(1)
                self.send_to_element_direct(det_value, str(int(usdrate * stock_price) * stock_count))
                commit.click()
                time.sleep(1)
                logger.info(rsuinfo[0] + " is updated.")
                elements = self.driver.find_elements_by_xpath('//*[@id="portfolio_det_eq"]/table/tbody/tr') # avoid stale error

    def stock_price(self, tick):
        history = PriceHistory(period='D', output_size='compact')
        results = history.get(tick)
        return results.records[-1]['close']

    def usdrate(self):
        r = requests.get('https://www.gaitameonline.com/rateaj/getrate')
        if r.status_code != 200:
            raise ConnectionRefusedError()
        data = r.json()
        for quote in data['quotes']:
            if quote['currencyPairCode'] == 'USDJPY':
                return float(quote['open'])

    def close(self):
        try:
            self.driver.close()
        except:
            logger.debug("Ignore exception (close)")
        try:
            self.driver.quit()
        except:
            logger.debug("Ignore exception (quit)")


############################################################

    def print_html(self):
        html = self.driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
        print(html)

    def send_to_element(self, xpath, keys):
        element = self.driver.find_element_by_xpath(xpath)
        element.clear()
        logger.debug("[send_to_element] " + xpath)
        element.send_keys(keys)

    def send_to_element_direct(self, element, keys):
        element.clear()
        logger.debug("[send_to_element] " + element.get_attribute('id'))
        element.send_keys(keys)

if __name__ == "__main__":
    if "LOG_LEVEL" in os.environ:
        logzero.loglevel(int(os.environ["LOG_LEVEL"]))
    mf = MoneyForward()
    try:
        mf.init()
        mf.login()
        mf.portfolio()
    finally:
        mf.close()
