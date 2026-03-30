import requests
import selenium.webdriver.firefox.firefox_profile
from selenium.webdriver.firefox.options import Options
from undetected_geckodriver import Firefox
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, JavascriptException

from urllib.parse import urlencode, urlparse

import threading
import pyray as pr
import os
import json
import pyperclip

LINK = r"https://rule34.xxx/index.php?"
PARAMS = {
    "tags": r"",
    "page": "post",
    "s": "list",
}
PATH = r"/home/tim/Private"
DATA = r"data.json"

RANDOM = True

HEADERS = {
    "Host": "wimg.rule34.xxx",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=4",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

KEY_PASS = pr.KeyboardKey.KEY_Q
KEY_SMASH = pr.KeyboardKey.KEY_W
KEY_CURSED = pr.KeyboardKey.KEY_E


class Scraper:
    def __init__(self):
        self.uithread = threading.Thread(target=loadui, name="ui", args=[self])
        self.ui = None
        options = selenium.webdriver.Firefox.options = Options()
        options.set_preference("browser.privatebrowsing.autostart", True)
        self.browser = Firefox(options)
        self.session = requests.Session()

        self.smash_counter = 0
        self.pass_counter = 0
        self.cursed_counter = 0
        self.data = {}
        self.load()

        self.browser.get(LINK + urlencode(PARAMS))
        # self.browser.execute_script("Cookie.create('resize-original',1); Cookie.create('resize-notification',1);")

        cookies = self.browser.get_cookies()
        for cookie in cookies:
            self.session.cookies.set(cookie['name'], cookie['value'])
        self.session.headers = HEADERS

    def save(self):
        self.data = {
            "smash": self.smash_counter,
            "pass": self.pass_counter,
            "cursed": self.cursed_counter,
        }
        with open(DATA, "w") as f:
            f.write(json.dumps(self.data))

    def load(self):
        if os.path.exists(DATA):
            with open(DATA) as f:
                self.data = json.load(f)
            self.smash_counter = self.data["smash"]
            self.pass_counter = self.data["pass"]
            self.cursed_counter = self.data["cursed"]

    def start(self):
        self.uithread.start()

    def end(self):
        self.browser.quit()
        self.session.close()
        self.save()

    def get_url(self):
        try:
            image = self.browser.find_element(By.CSS_SELECTOR,
                                          "html body#body div#content div#post-view div.sidebar div.link-list ul li a[style=\"font-weight: bold;\"]")
            url = image.get_attribute("href")
            return url
        except NoSuchElementException:
            return None

    def passf(self, true=True):
        pass
        try:
            if RANDOM:
                button = self.browser.find_element(By.CSS_SELECTOR,
                                                           "#subnavbar > li:nth-child(4) > a:nth-child(1)")
            else:
                button = self.browser.find_element(By.CSS_SELECTOR, "#next_search_link")
            button.click()
        except NoSuchElementException:
            print("No next button found")
        if true:
            self.pass_counter += 1

    def smashf(self, path: str):
        try:
            # try:
            #     self.scraper.browser.execute_script("Post.highres(); $('resized_notice').hide(); Note.sample=false;")  # increase the quality
            # except JavascriptException:
            #     pass
            url = self.get_url()
            if url is None:
                raise NoSuchElementException
            filename = os.path.join(path, urlparse(url).path.split("/")[-1])
            response = self.session.get(url)
            print(url)
            if response.status_code != 200:
                raise FileNotFoundError()
            with open(filename, "wb") as f:
                f.write(response.content)
                print(f"Saved to {filename}!")
        except NoSuchElementException:
            print("No Image Found")
        except FileNotFoundError:
            print("File not found")
        self.smash_counter += 1
        self.passf(False)

    def cursedf(self):
        url = self.get_url()
        if url is None:
            print("No URL Found")
        else:
            pyperclip.copy(url)
        self.cursed_counter += 1
        self.passf(False)


class UI:
    def __init__(self, scraper: Scraper):
        self.cursor = [0, 0]
        self.clicked = False
        self.scraper = scraper


    def start(self):
        pr.init_window(600, 200, "Rule34 Scraper")
        pr.set_target_fps(60)
        pr.set_window_state(pr.ConfigFlags.FLAG_WINDOW_TOPMOST)

    def run(self):
        self.start()
        while not pr.window_should_close():
            self.update()
            self.draw()
        self.end()

    def update(self):
        self.cursor[0] = pr.get_mouse_x()
        self.cursor[1] = pr.get_mouse_y()
        self.clicked = pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_LEFT)

    def addbutton(self, x: int, x2: int, text: str, color1: int, color2: int, func, key: int):
        hover = x < self.cursor[0] < x2
        pr.draw_rectangle(x, 0, x2 - x, 200, pr.get_color(color2) if hover else pr.get_color(color1))
        pr.draw_text(text, x, 100, 32, pr.get_color(0x000000FF))
        if (hover and self.clicked) or pr.is_key_pressed(key):
            func()

    def draw(self):
        pr.begin_drawing()
        self.addbutton(0, 200, "Pass", 0xF72C5BFF, 0xFF748BFF, self.scraper.passf, KEY_PASS)
        self.addbutton(200, 400, "Smash", 0xA7D477FF, 0xE4F1ACFF, lambda: self.scraper.smashf(PATH), KEY_SMASH)
        self.addbutton(400, 600, "Cursed", 0x3399ffFF, 0x66ccffFF, self.scraper.cursedf, KEY_CURSED)
        pr.draw_text(str(self.scraper.pass_counter), 0, 0, 32, pr.get_color(0x000000FF))
        pr.draw_text(str(self.scraper.smash_counter), 200, 0, 32, pr.get_color(0x000000FF))
        pr.draw_text(str(self.scraper.cursed_counter), 400, 0, 32, pr.get_color(0x000000FF))
        pr.end_drawing()

    def end(self):
        pr.close_window()
        self.scraper.end()



def loadui(scraper: Scraper):
    ui = UI(scraper)
    ui.run()
    scraper.ui = ui


def main():
    scraper = Scraper()
    scraper.start()


if __name__ == '__main__':
    main()
