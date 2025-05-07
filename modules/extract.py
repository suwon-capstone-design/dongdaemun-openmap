import time
import re
from bs4 import BeautifulSoup as bs


class ReviewExtractor:
    def __init__(self, driver):
        self.driver = driver

    def extract_road_address(self, address):
        if not address:
            return None
        match = re.search(r"(동대문구 [^ ]+로[^ ]*)", address)
        return match.group(1) if match else None

    def extract_land_address(self, address):
        if not address:
            return None
        match = re.search(r"(동대문구 [가-힣]+동[\s\d\-]*)", address)
        return match.group(1) if match else None

    def get_store_rating(self):
        soup = bs(self.driver.page_source, "html.parser")
        rating_tag = soup.select_one("span.PXMot.LXIwF")
        return rating_tag.get_text(strip=True).replace("별점", "") if rating_tag else None

    def get_store_info(self, name, road, lot):
        soup = bs(self.driver.page_source, "html.parser")
        road_match = self.extract_road_address(road)
        lot_match = self.extract_land_address(lot)

        for item in soup.select("li._list_item_sis14_40"):
            link = item.select_one("a._a_item_sis14_59")
            cid_match = re.search(r"/place/(\d+)", link["href"]) if link else None
            cid = cid_match.group(1) if cid_match else None

            if not cid:
                continue

            address_btn = item.select_one("button._item_address_sis14_319")
            address = address_btn.get_text(strip=True).replace("주소보기", "") if address_btn else ""

            if (road_match and road_match in address) or (lot_match and lot_match in address):
                return cid, address

        return None, None

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
