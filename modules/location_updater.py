import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.mysql_pool_client import MySQLPoolClient
from modules.address_geocoder import AddressGeocoder


class LocationUpdater:
    def __init__(self):
        self.db = MySQLPoolClient()
        self.geocoder = AddressGeocoder(user_agent="location_updater")

    def fetch_records(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                pd.road_address,
                pd.lot_address,
                nms.id AS naver_map_store_id
            FROM public_data pd
            JOIN naver_map_store nms
              ON pd.id = nms.public_data_id
            WHERE nms.latitude = 0.0
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def save_location(self, store_id: int, lat: float, lon: float):
        sql = """
        UPDATE naver_map_store
           SET latitude  = %s,
               longitude = %s
         WHERE id = %s
        """
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (lat, lon, store_id))
        finally:
            conn.close()

    def process_all(self):
        batch = self.fetch_records()
        if not batch:
            print("처리할 레코드가 없습니다.")
        for row in batch:
            store_id = row["naver_map_store_id"]
            road_addr = (row.get("road_address") or "").strip()
            lot_addr = (row.get("lot_address") or "").strip()

            if road_addr:
                address = road_addr
            elif lot_addr:
                address = lot_addr
            else:
                print(f"[ID {store_id}] 주소 없음 → (0.0, 0.0) 저장")
                self.save_location(store_id, 0.0, 0.0)
                continue

            try:
                lat, lon = self.geocoder.geocode(address)
                print(f"[ID {store_id}] {address} → ({lat:.6f}, {lon:.6f})")
                self.save_location(store_id, lat, lon)
            except ValueError as e:
                print(f"[ID {store_id}] 지오코딩 실패: {e} → (0.0, 0.0) 저장")
                self.save_location(store_id, 0.0, 0.0)

        self.db.close()


if __name__ == "__main__":
    updater = LocationUpdater()
    updater.process_all()
