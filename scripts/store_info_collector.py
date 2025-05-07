import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.driver import ChromeDriverManager
from modules.extract import ReviewExtractor
from db.mysql_pool_client import MySQLPoolClient

BASE_SEARCH_URL = "https://m.map.naver.com/search?query={}"
BASE_STORE_URL = "https://m.place.naver.com/restaurant/{}/review/visitor?reviewSort=recent"


class StoreInfoCollector:
    def __init__(self):
        self.db = MySQLPoolClient()
        self.driver = ChromeDriverManager.get_driver()
        self.extractor = ReviewExtractor(self.driver)

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

        cid, address = self.extractor.get_store_info(name, road, lot)
        
        if cid:
            print(f"[📌 매칭 성공] {name} → CID: {cid}")
            self.driver.get(BASE_STORE_URL.format(cid))
            time.sleep(1.5)
            rating = self.extractor.get_store_rating()
            self.insert_store(public_id, rating, cid)
        else:
            print(f"[❌ 매칭 실패] {name}")
            self.insert_store(public_id, None, None)

    def run(self):
        for store in self.get_unmapped_stores():
            self.search_and_save(store["store_name"], store["road_address"], store["lot_address"], store["id"])
        self.driver.quit()
        self.db.close()


if __name__ == "__main__":
    StoreInfoCollector().run()
