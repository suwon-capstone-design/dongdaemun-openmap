import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

CHROME_PATH = "/home/jys0207/capstone/chrome_install/opt/google/chrome/google-chrome"
CHROMEDRIVER_PATH = "/home/jys0207/capstone/chromedriver"


class ChromeDriverManager:
    @staticmethod
    def get_driver():
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless=new")
        options.add_argument("--incognito")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                             "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

        if platform.system() == "Linux":
            options.binary_location = CHROME_PATH
            service = Service(CHROMEDRIVER_PATH)
            return webdriver.Chrome(service=service, options=options)
        else:
            return webdriver.Chrome(options=options)
