import json
from flask import Blueprint, render_template, request
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.mysql_pool_client import MySQLPoolClient

kakao_map = Blueprint('kakao_map', __name__, 
                      template_folder='templates')

@kakao_map.route('/map')
def show_map():
    db = MySQLPoolClient()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    limit = request.args.get('limit', default=500, type=int)
    min_rating = request.args.get('min_rating', default=0, type=float)
    
    if limit not in [500, 1000, 2000, 3000]:
        limit = 500
    
    query = """
        SELECT nms.id as nms_id, pd.store_name, nms.latitude, nms.longitude, nms.avg_rating, nms.naver_store_url, r.id as review_id
        FROM naver_map_store nms
        JOIN public_data pd ON nms.public_data_id = pd.id
        JOIN review r ON nms.id = r.store_id
        WHERE nms.latitude IS NOT NULL AND nms.longitude IS NOT NULL AND nms.naver_store_url IS NOT NULL AND avg_rating IS NOT NULL
    """
    
    if min_rating > 0:
        query += f" AND nms.avg_rating >= {min_rating}"
    
    query += """
        ORDER BY nms.avg_rating DESC
        LIMIT %s
    """
    
    cursor.execute(query, (limit,))
    
    stores = cursor.fetchall()
    cursor.close()
    conn.close()
    
    kakao_api_key = os.getenv('KAKAO_API_KEY')
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    geojson_path = os.path.join(current_dir, 'templates', 'dongdaemun-gu.geojson')
    
    with open(geojson_path, encoding="utf-8") as f:
        dongdaemun_geo = json.load(f)
    
    return render_template('map.html', 
                         stores=stores,
                         kakao_api_key=kakao_api_key,
                         dongdaemun_geo=dongdaemun_geo,
                         limit=limit,
                         min_rating=min_rating)

@kakao_map.route('/review/<int:review_id>')
def show_review(review_id):
    db = MySQLPoolClient()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.id, r.store_id, r.review_content, r.review_analysis_result,
               pd.store_name, nms.avg_rating, nms.naver_store_url
        FROM review r
        JOIN naver_map_store nms ON r.store_id = nms.id
        JOIN public_data pd ON nms.public_data_id = pd.id
        WHERE r.id = %s
    """, (review_id,))
    
    review = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not review:
        return "리뷰를 찾을 수 없습니다", 404
    
    analysis = json.loads(review['review_analysis_result']) if review['review_analysis_result'] else None
    
    return render_template('review.html',
                          review=review,
                          analysis=analysis)
