import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.driver import ChromeDriverManager
from modules.extract import ReviewExtractor
from db.mysql_pool_client import MySQLPoolClient


class ReviewCollector:
    def __init__(self):
        self.db = MySQLPoolClient()
        self.driver = ChromeDriverManager.get_driver()
        self.extractor = ReviewExtractor(self.driver)

    def get_target_stores(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nms.id AS store_id, pd.store_name, nms.naver_store_url
            FROM naver_map_store nms
            JOIN public_data pd ON nms.public_data_id = pd.id
            LEFT JOIN review r ON nms.id = r.store_id
            WHERE nms.naver_store_url IS NOT NULL AND r.store_id IS NULL
        """)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result

    def insert_combined_review(self, store_id, reviews):
        combined = "\n".join([f"[{r['review_date']}] ({r['reviewer_name']}): {r['review_content']}" for r in reviews])
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO review (store_id, review_content) VALUES (%s, %s)", (store_id, combined))
        conn.commit()
        cursor.close()
        conn.close()

    def run(self):
        for store in self.get_target_stores():
            store_id = store["store_id"]
            name = store["store_name"]
            url = store["naver_store_url"]
            print(f"[🔍 수집 중] {name} - {url}")
            try:
                self.driver.get(url)
                time.sleep(1.5)
                self.extractor.load_all_reviews()
                reviews = self.extractor.extract_reviews()
                if not reviews:
                    print(f"[⚠️ 없음] {name}")
                    continue
                self.insert_combined_review(store_id, reviews)
                print(f"[✅ 저장 완료] {name} - {len(reviews)}개")
            except Exception as e:
                print(f"[❌ 실패] {name} - {e}")
        self.driver.quit()
        self.db.close()


if __name__ == "__main__":
    ReviewCollector().run()
