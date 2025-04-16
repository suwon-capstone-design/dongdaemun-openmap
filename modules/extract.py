import time
from bs4 import BeautifulSoup as bs


class ReviewExtractor:
    def __init__(self, driver):
        self.driver = driver

    def extract_reviews(self):
        soup = bs(self.driver.page_source, "html.parser")
        reviews = []

        for r in soup.select("li.place_apply_pui"):
            name = r.select_one("span.pui__NMi-Dp")
            content = r.select_one("div.pui__vn15t2 a")
            date = r.select_one("div > span > span.pui__blind:nth-child(3)")

            if content and len(content.text.strip()) >= 2:
                reviews.append({
                    "reviewer_name": name.text.strip() if name else "익명",
                    "review_content": content.text.strip(),
                    "review_date": date.text.strip().replace(".", "-") if date else None
                })

        return reviews

    def load_all_reviews(self, max_clicks=30):
        for _ in range(max_clicks):
            clicked = False
            try:
                more = self.driver.find_element("css selector", "a.fvwqf")
                if "더보기" in more.text:
                    self.driver.execute_script("arguments[0].click();", more)
                    time.sleep(1.5)
                    clicked = True
            except Exception:
                pass

            try:
                expand = self.driver.find_element("css selector", "a.Kv9y6")
                if "펼쳐보기" in expand.text:
                    self.driver.execute_script("arguments[0].click();", expand)
                    time.sleep(1)
                    clicked = True
            except Exception:
                pass

            if not clicked:
                break
