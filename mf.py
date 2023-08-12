from logzero import logger
import logzero

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

import requests

import os, time, datetime
import imaplib, email, re, pyotp, pytz


class MoneyForward:
    def __init__(self) -> None:
        self.stock_price_cache: dict[str, float] = dict()

    def init(self):
        logger.info("selenium initializing...")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=800x1000")
        options.add_argument("--disable-application-cache")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--hide-scrollbars")
        options.add_argument("--lang=ja-JP")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
        )
        options.binary_location = "/usr/bin/chromium-browser"
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 5)
        self.driver.implicitly_wait(10)
        if not "ALPHAVANTAGE_API_KEY" in os.environ:
            raise ValueError("env ALPHAVANTAGE_API_KEY is not found.")
        self.alphavantage_apikey = os.environ["ALPHAVANTAGE_API_KEY"]

    def login(self):
        self.driver.execute_script("window.open()")
        if not "MF_ID" in os.environ or not "MF_PASS" in os.environ:
            raise ValueError("env MF_ID and/or MF_PASS are not found.")
        mf_id = os.environ["MF_ID"]
        mf_pass = os.environ["MF_PASS"]

        self.driver.get("https://moneyforward.com/sign_in")
        self.wait.until(ec.presence_of_all_elements_located)
        self.driver.find_element(by=By.XPATH, value='//img[@alt="email"]').click()
        self.wait.until(ec.presence_of_all_elements_located)

        login_time = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))
        self.send_to_element('//input[@type="email"]', mf_id)
        self.driver.find_element(by=By.XPATH, value='//button[@id="submitto"]').click()
        self.wait.until(ec.presence_of_all_elements_located)
        time.sleep(3)
        self.send_to_element('//input[@type="password"]', mf_pass)
        self.driver.find_element(by=By.XPATH, value='//button[@id="submitto"]').click()
        self.wait.until(ec.presence_of_all_elements_located)

        if self.driver.find_elements(by=By.ID, value="page-home"):
            logger.info("successfully logged in.")
        # New type of MoneyForward two step verifications
        elif self.driver.current_url.startswith(
            "https://id.moneyforward.com/two_factor_auth/totp"
        ):
            self.confirm_two_step_verification_param()
            if os.environ["MF_TWO_STEP_VERIFICATION"].lower() == "totp":
                confirmation_code = self.get_confirmation_code_from_totp()
            else:
                raise ValueError(
                    "unsupported two step verification is found. check your env MF_TWO_STEP_VERIFICATION."
                )
            self.send_to_element('//*[@name="otp_attempt"]', confirmation_code)
            self.driver.find_element(
                by=By.XPATH, value='//button[@id="submitto"]'
            ).click()
            self.wait.until(ec.presence_of_all_elements_located)
            if self.driver.find_elements(
                by=By.XPATH, value='//div[contains(@class,"registerLaterWrapper")]/a'
            ):
                logger.info(
                    "recognized as unknown devise and selecting register later."
                )
                self.driver.find_element(
                    by=By.XPATH,
                    value='//div[contains(@class,"registerLaterWrapper")]/a',
                ).click()
                self.wait.until(ec.presence_of_all_elements_located)
            if self.driver.find_elements(by=By.ID, value="home"):
                logger.info("successfully logged in.")
            else:
                logger.debug(self.driver.current_url)
                raise ValueError("failed to log in.")
        # Old type of MoneyForward two step verifications
        elif self.driver.find_elements(by=By.ID, value="page-two-step-verifications"):
            self.confirm_two_step_verification_param()
            if os.environ["MF_TWO_STEP_VERIFICATION"].lower() == "gmail":
                logger.info("waiting confirmation code from Gmail...")
                confirmation_code = self.get_confirmation_code_from_gmail(login_time)
            else:
                raise ValueError(
                    "unsupported two step verification is found. check your env MF_TWO_STEP_VERIFICATION."
                )
            self.driver.get(
                "https://moneyforward.com/users/two_step_verifications/verify/{confirmation_code}".format(
                    confirmation_code=confirmation_code
                )
            )
            self.wait.until(ec.presence_of_all_elements_located)
            self.driver.get("https://moneyforward.com/users/sign_in")
            if self.driver.find_elements(by=By.ID, value="home"):
                logger.info("successfully logged in.")
            else:
                raise ValueError("failed to log in.")
        else:
            raise ValueError("failed to log in.")

    def portfolio(self):
        usdrate = self.usdrate()
        logger.info("USDJPY: " + str(usdrate))
        self.driver.get("https://moneyforward.com/bs/portfolio")
        self.wait.until(ec.presence_of_all_elements_located)
        elements = self.driver.find_elements(
            by=By.XPATH, value='//*[@id="portfolio_det_eq"]/table/tbody/tr'
        )
        for i in range(len(elements)):
            tds = elements[i].find_elements(by=By.TAG_NAME, value="td")
            name = tds[1].text
            if name[0:1] == "#":
                entry = name.split("-")
                stock_price = self.stock_price(entry[1])
                stock_count = int(entry[2])
                logger.info(
                    entry[0]
                    + ": "
                    + entry[1]
                    + " is "
                    + str(stock_price)
                    + "USD ("
                    + str(int(usdrate * stock_price))
                    + " JPY) x "
                    + str(stock_count)
                )
                img = tds[11].find_element(by=By.TAG_NAME, value="img")
                self.driver.execute_script("arguments[0].click();", img)
                det_value = tds[11].find_element(by=By.ID, value="user_asset_det_value")
                commit = tds[11].find_element(by=By.NAME, value="commit")
                time.sleep(1)
                self.send_to_element_direct(
                    det_value, str(int(usdrate * stock_price) * stock_count)
                )
                commit.click()
                time.sleep(1)
                logger.info(entry[0] + " is updated.")
                elements = self.driver.find_elements(
                    by=By.XPATH, value='//*[@id="portfolio_det_eq"]/table/tbody/tr'
                )  # avoid stale error

    def stock_price(self, tick):
        if not tick in self.stock_price_cache:
            for retry in range(3):
                r = requests.get(
                    f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={tick}&apikey={self.alphavantage_apikey}"
                )
                if r.status_code != 200:
                    raise ConnectionRefusedError()
                data = r.json()
                if "Global Quote" in data:
                    self.stock_price_cache[tick] = float(
                        data["Global Quote"]["05. price"]
                    )
                    break
        return self.stock_price_cache[tick]

    def usdrate(self):
        r = requests.get(
            f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=JPY&apikey={self.alphavantage_apikey}"
        )
        if r.status_code != 200:
            raise ConnectionRefusedError()
        data = r.json()
        return float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])

    def close(self):
        try:
            self.driver.close()
        except:
            logger.debug("Ignore exception (close)")
        try:
            self.driver.quit()
        except:
            logger.debug("Ignore exception (quit)")

    ################## Two step verification ###################

    def confirm_two_step_verification_param(self):
        logger.info("two step verification is enabled.")
        if not "MF_TWO_STEP_VERIFICATION" in os.environ:
            raise ValueError("env MF_TWO_STEP_VERIFICATION is not found.")

    def get_confirmation_code_from_totp(self):
        if not "MF_TWO_STEP_VERIFICATION_TOTP_SECRET_KEY" in os.environ:
            raise ValueError(
                "env MF_TWO_STEP_VERIFICATION_TOTP_SECRET_KEY are not found."
            )
        confirmation_code = pyotp.TOTP(
            os.getenv("MF_TWO_STEP_VERIFICATION_TOTP_SECRET_KEY")
        ).now()
        return confirmation_code

    def get_confirmation_code_from_gmail(self, sent_since):
        if (
            not "MF_TWO_STEP_VERIFICATION_GMAIL_ACCOUNT" in os.environ
            or not "MF_TWO_STEP_VERIFICATION_GMAIL_APP_PASS" in os.environ
        ):
            raise ValueError(
                "env MF_TWO_STEP_VERIFICATION_GMAIL_ACCOUNT and/or MF_TWO_STEP_VERIFICATION_GMAIL_APP_PASS are not found."
            )
        timeout = int(os.getenv("MF_TWO_STEP_VERIFICATION_TIMEOUT", "180"))
        interval = int(os.getenv("MF_TWO_STEP_VERIFICATION_INTERVAL", "5"))
        deadline = time.time() + timeout
        while time.time() < deadline:
            confirmation_code = self.read_confirmation_code_from_gmail(sent_since)
            if confirmation_code:
                return confirmation_code
            time.sleep(interval)

    def read_confirmation_code_from_gmail(self, sent_since):
        gmail_account = os.getenv("MF_TWO_STEP_VERIFICATION_GMAIL_ACCOUNT")
        gmail_app_pass = os.getenv("MF_TWO_STEP_VERIFICATION_GMAIL_APP_PASS")
        gmail = imaplib.IMAP4_SSL("imap.gmail.com", "993")
        gmail.login(gmail_account, gmail_app_pass)
        gmail.select()
        search_option = (
            '(FROM "feedback@moneyforward.com" SENTSINCE {sent_since})'.format(
                sent_since=sent_since.strftime("%d-%b-%Y")
            )
        )
        head, data = gmail.search(None, search_option)

        confirmation_code = ""
        for num in data[0].split():
            h, d = gmail.fetch(num, "(RFC822)")
            raw_email = d[0][1]
            message = email.message_from_string(raw_email.decode("utf-8"))
            message_encoding = (
                email.header.decode_header(message.get("Subject"))[0][1]
                or "iso-2022-jp"
            )
            subject_header = email.header.decode_header(message.get("Subject"))[0][0]
            subject = str(subject_header.decode(message_encoding))
            if subject != "【マネーフォワード ME】2段階認証メール":
                continue
            date_header = email.header.decode_header(message.get("Date"))
            message_time = datetime.datetime.strptime(
                date_header[0][0], "%a, %d %b %Y %H:%M:%S %z"
            )  # RFC 2822 format
            if sent_since < message_time:
                body = (
                    message.get_payload()[0]
                    .get_payload(decode=True)
                    .decode(encoding=message_encoding)
                )
                m = re.search(
                    r"https://moneyforward.com/users/two_step_verifications/verify/([0-9]+)",
                    body,
                )
                confirmation_code = m.group(1)
                sent_since = message_time

        gmail.close()
        gmail.logout()
        return confirmation_code

    ############################################################

    def print_html(self):
        html = self.driver.execute_script(
            "return document.getElementsByTagName('html')[0].innerHTML"
        )
        print(html)

    def send_to_element(self, xpath, keys):
        element = self.driver.find_element(by=By.XPATH, value=xpath)
        element.clear()
        logger.debug("[send_to_element] " + xpath)
        element.send_keys(keys)

    def send_to_element_direct(self, element, keys):
        element.clear()
        logger.debug("[send_to_element] " + element.get_attribute("id"))
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
