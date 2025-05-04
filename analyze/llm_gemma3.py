import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
from db.mysql_pool_client import MySQLPoolClient

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:27b-it-qat"


class ReviewAnalyzer:
    def __init__(self, batch_size: int = 10):
        self.db = MySQLPoolClient()
        self.batch_size = batch_size
        self.ollama_url = OLLAMA_URL
        self.model_name = MODEL_NAME

    def fetch_reviews(self, offset: int):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, store_id, review_content
            FROM review
            ORDER BY store_id DESC
            LIMIT %s OFFSET %s
            """,
            (self.batch_size, offset),
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def analyze_review(self, review_content: str) -> str:
        prompt = f"""
        절대 다른 텍스트를 추가하지 말고, 반드시 JSON 오브젝트만 반환해야 합니다!

        다음 리뷰를 실제 리뷰 내용을 바탕으로 아래 형식에 꼭 맞춰 작성해 주세요.

        1)   
        - 3~5문장 이내의 간결한 텍스트로 분석합니다.  

        2) 위생 평가  
        - 3~5문장 이내의 간결한 텍스트로 분석합니다.  

        3) 전반적인 평가  
        - 3~5문장 이내의 간결한 텍스트로 분석합니다.  

        4) 점수  
        -   
        - 위생 점수: 100점 만점, 재료 신선도·매장 청결도·포장 상태 각각 33.33점 배점  
        - 전반 점수: 가성비 점수 50% + 위생 점수 50% 가중 평균  
        - 소수점 둘째 자리까지 표기  

        JSON 스키마:
        {{
          "costPerformanceText": string,   // 3~5문장 이내 (가성비 평가)
          "hygieneText": string,           // 3~5문장 이내 (위생 평가)
          "overallText": string,           // 3~5문장 이내 (전반적인 평가)
          "costPerformanceScore": number,  // 0.00~100.00 소수점 둘째 자리까지 (가성비 점수: 100점 만점, 가격 대비 품질·양·서비스 만족도 각각 25점 배점)
          "hygieneScore": number,          // 0.00~100.00 소수점 둘째 자리까지 (위생 점수: 100점 만점, 재료 신선도·매장 청결도·포장 상태 각각 33.33점 배점)
          "overallScore": number           // 가성비 50% + 위생 50% 가중 평균 (전반 점수: 가성비 점수 50% + 위생 점수 50% 가중 평균)
        }}

        리뷰 원문:  
        {review_content}
        """

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": 0.0,
            "stream": False,
        }

        try:
            resp = requests.post(self.ollama_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "오류 발생: 모델이 응답하지 않습니다.")
        except requests.exceptions.RequestException as e:
            print(f"API 요청 중 오류 발생: {e}")
            return "API 요청 실패"

    def save_analysis(self, review_id: int, analysis: str):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE review SET review_analysis_result = %s WHERE id = %s",
            (analysis, review_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

    def process_all(self):
        offset = 0
        while True:
            batch = self.fetch_reviews(offset)
            if not batch:
                break

            for row in batch:
                review_id = row["id"]
                content = row["review_content"]
                analysis = self.analyze_review(content)
                print(f"[Review ID {review_id}] 분석 결과:\n{analysis}\n")
                # self.save_analysis(review_id, analysis)

            offset += self.batch_size


if __name__ == "__main__":
    analyzer = ReviewAnalyzer(batch_size=10)
    analyzer.process_all()
