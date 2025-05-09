# 동대문구 ‘착한 업소’ 분석 플랫폼

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)  
[![Python 버전](https://img.shields.io/badge/Python-3.8%2B-green.svg)](#)  
[![Selenium](https://img.shields.io/badge/Selenium-자동–크롤링-orange.svg)](#)

---

## 📌 프로젝트 개요

동대문구 내 **식품위생업소**의 행정 등록 정보와 실제 **민간 리뷰 데이터**를 결합하여  
‘시민이 체감하는’ **신뢰도 높은 업소 리스트**를 자동으로 발굴·시각화하는 데이터 플랫폼입니다.

- **주제**: 리뷰 기반 착한 업소 발굴 및 지역 상권 활성화  
- **목적**  
  1. 행정 DB 상의 업소 목록 검증  
  2. ‘착한 업소’ 인증 지표 마련  
  3. 거리 추천·상권 활성화 정책 인사이트 제공  

---

## 📷 데모 스크린샷

<div align="center">
  <a href="http://dongdaemun-map.kro.kr/map"><img src="https://github.com/user-attachments/assets/32ff854d-7ba7-4794-9090-d0a252de7a89" alt="동대문구 카카오 맵"></a>
  <a href="http://dongdaemun-map.kro.kr/review/1"><img src="https://github.com/user-attachments/assets/724a563a-a509-4b21-bc59-becf7cb3efdb" alt="리뷰 분석 예시"></a>
</div>

---

## 🚀 주요 기능

1. **공공데이터 로드**  
   - `서울특별시 동대문구_식품위생업소현황.csv` 파싱  
2. **업소 검색 & URL 확보**  
   - 네이버 모바일 지도 자동 검색 → 플레이스 URL 수집  
3. **리뷰 크롤링 & 정제**  
   - 최신 리뷰 10개(무한 스크롤) → 작성자·날짜·내용 추출  
4. **AI 감성 분석**  
   - 크롤링된 리뷰 텍스트에 대해 긍정·부정 분류 → 평균 평점 산정  
5. **DB 저장**  
   - MySQL/InnoDB 기반 테이블에 원본·분석 결과 저장  
6. **지도 시각화 & 리포트**  
   - 착한 업소 랭킹, 신뢰 지수 지도, 거리 추천 제안 (예정)  

---

## 🗂️ 데이터 & DB 스키마

```sql
-- 1. 공공데이터 원본 테이블
CREATE TABLE public_data (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '업소 고유 ID',
  store_name VARCHAR(255) NOT NULL COMMENT '업소명',
  business_type VARCHAR(100) COMMENT '업태구분명',
  category VARCHAR(100) COMMENT '업종명',
  road_address VARCHAR(255) COMMENT '도로명주소',
  lot_address VARCHAR(255) COMMENT '지번주소'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='공공데이터 기반 업소 테이블';

-- 2. 네이버 플레이스 테이블
CREATE TABLE naver_map_store (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '플레이스 ID',
  public_data_id INT NOT NULL COMMENT '공공데이터 참조 ID',
  naver_store_url VARCHAR(300) COMMENT '리뷰 페이지 URL',
  avg_rating DECIMAL(3,2) DEFAULT NULL COMMENT '추정 평균 평점',
  latitude DECIMAL(10,7) DEFAULT NULL COMMENT '위도',
  longitude DECIMAL(10,7) DEFAULT NULL COMMENT '경도',
  FOREIGN KEY (public_data_id) REFERENCES public_data(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='네이버 플레이스 매핑 테이블';

-- 3. 리뷰 테이블
CREATE TABLE review (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '리뷰 ID',
  store_id INT NOT NULL COMMENT '플레이스 참조 ID',
  review_content LONGTEXT NOT NULL COMMENT '리뷰 내용',
  review_analysis_result JSON COMMENT '리뷰 분석 결과',
  FOREIGN KEY (store_id) REFERENCES naver_map_store(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='업소별 리뷰 저장 테이블';
```

---

## 🚧 향후 개선사항
- 리뷰 크롤링 정밀도 향상: 블로그/SNS 크롤링 추가

- 프롬프트 최적화: AI 감성 분석 정확도 개선

- 실시간 자동화: 스케줄러 도입 → 주기적 업데이트

- 미등록 업소 보완: 직접 URL 매핑 또는 OCR 기반 매칭

- 웹서비스 배포: 배포 자동화
