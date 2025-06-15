import re
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError, GeocoderTimedOut


class AddressGeocoder:
    """
    geopy의 Nominatim을 사용해, 주어진 주소 문자열에서
    위도(latitude)와 경도(longitude)를 반환합니다.
    빌딩 몇 층, 호실 정보가 포함되어도 기본 주소만 추출해 처리합니다.
    """

    def __init__(self, user_agent: str = "my_geocoder"):
        self.geolocator = Nominatim(user_agent=user_agent, timeout=10)

    def _normalize_address(self, raw_addr: str) -> str:
        addr = raw_addr

        # 1) 쉼표(,)나 그 뒤의 텍스트 제거: “~, 2층” → “~”
        addr = re.sub(r",.*$", "", addr)

        # 2) 지하/지상+n층, n층, n-n호, n호 모두 제거
        addr = re.sub(r"(?:지하|지상)\s*\d+\s*층", "", addr)
        addr = re.sub(r"\d+\s*층", "", addr)
        addr = re.sub(r"\d+[-–]\d+\s*호", "", addr)
        addr = re.sub(r"\d+\s*호", "", addr)

        # 3) 건물명＋동＋호 패턴 (ABC동101호, 빨강동 56호 등) 제거
        addr = re.sub(r"[^\s,]+동\s*\d+\s*호", "", addr)
        addr = re.sub(r"[^\s,]+동(?=\d+)", "", addr)

        # 4) 괄호 안 텍스트 제거
        addr = re.sub(r"\(.*?\)", "", addr)

        # 5) 남은 “지하” “지상” 단어 제거
        addr = re.sub(r"\b(?:지하|지상)\b", "", addr)

        # 6) 다중 공백·쉼표 정리
        addr = re.sub(r"[,\s]+", " ", addr).strip()

        return addr

    def geocode(self, raw_address: str, max_retries: int = 2) -> tuple[float, float]:
        """
        주소 문자열을 받아서 (latitude, longitude) 반환.
        실패 시 ValueError를 발생시킵니다.
        """
        addr = self._normalize_address(raw_address)

        for attempt in range(1, max_retries + 1):
            try:
                location = self.geolocator.geocode(addr)
                if location:
                    return (location.latitude, location.longitude)
                else:
                    raise ValueError(f"주소를 찾을 수 없습니다: '{raw_address}' → '{addr}'")

            except (GeocoderTimedOut, GeocoderServiceError) as e:
                if attempt < max_retries:
                    time.sleep(1)  # 잠시 대기 후 재시도
                    continue
                raise ValueError(f"지오코딩 서비스 오류: {e}")

        # 이 지점까지 오면 실패
        raise ValueError(f"지오코딩 실패: '{raw_address}' → '{addr}'")
