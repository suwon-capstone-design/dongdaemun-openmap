import time
import re
from bs4 import BeautifulSoup as bs
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.driver import ChromeDriverManager
from db.mysql_pool_client import MySQLPoolClient

BASE_SEARCH_URL = "https://m.map.naver.com/search?query={}"
BASE_STORE_URL = "https://m.place.naver.com/restaurant/{}/review/visitor?reviewSort=recent"


class StoreInfoCollector:
    def __init__(self):
        self.db = MySQLPoolClient()
        self.driver = ChromeDriverManager.get_driver()

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

    def get_unmapped_stores(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pd.id, pd.store_name, pd.road_address, pd.lot_address 
            FROM public_data pd
            LEFT JOIN naver_map_store nms ON pd.id = nms.public_data_id
            WHERE nms.public_data_id IS NULL
        """)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result

    def insert_store(self, public_id, rating, cid):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        url = BASE_STORE_URL.format(cid) if cid else None

        cursor.execute("""
            INSERT INTO naver_map_store (public_data_id, avg_rating, latitude, longitude, naver_store_url)
            VALUES (%s, %s, NULL, NULL, %s)
        """, (public_id, rating, url))
        conn.commit()
        cursor.close()
        conn.close()

    def search_and_save(self, name, road, lot, public_id):
        self.driver.get(BASE_SEARCH_URL.format(name))
        time.sleep(1.5)

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
                print(f"[📌 매칭 성공] {name} → CID: {cid}")
                self.driver.get(BASE_STORE_URL.format(cid))
                time.sleep(1.5)
                soup2 = bs(self.driver.page_source, "html.parser")
                rating_tag = soup2.select_one("span.PXMot.LXIwF")
                rating = rating_tag.get_text(strip=True).replace("별점", "") if rating_tag else None
                self.insert_store(public_id, rating, cid)
                return

        print(f"[❌ 매칭 실패] {name}")
        self.insert_store(public_id, None, None)

    def run(self):
        for store in self.get_unmapped_stores():
            self.search_and_save(store["store_name"], store["road_address"], store["lot_address"], store["id"])
        self.driver.quit()
        self.db.close()


if __name__ == "__main__":
    StoreInfoCollector().run()
