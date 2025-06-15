import json
from flask import Blueprint, render_template, request
import os
import sys

import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN

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
        SELECT nms.id as nms_id, pd.store_name, nms.latitude, nms.longitude,
               nms.avg_rating, nms.naver_store_url, r.id as review_id
        FROM naver_map_store nms
        JOIN public_data pd ON nms.public_data_id = pd.id
        JOIN review r ON nms.id = r.store_id
        WHERE nms.latitude IS NOT NULL
          AND nms.longitude IS NOT NULL
          AND nms.naver_store_url IS NOT NULL
          AND nms.avg_rating IS NOT NULL
    """
    if min_rating > 0:
        query += " AND nms.avg_rating >= %s"
    query += " ORDER BY nms.avg_rating DESC LIMIT %s"

    params = []
    if min_rating > 0:
        params.append(min_rating)
    params.append(limit)

    cursor.execute(query, tuple(params))
    stores = cursor.fetchall()
    cursor.close()
    conn.close()

    df = pd.DataFrame(stores)
    df['latitude'] = df['latitude'].astype(float)
    df['longitude'] = df['longitude'].astype(float)
    good_df = df[df['avg_rating'] >= 4.6].copy()

    kms_per_rad = 6371.0088
    epsilon = 0.5 / kms_per_rad  # 0.5km를 라디안 단위로
    coords = good_df[['latitude', 'longitude']].to_numpy()
    db = DBSCAN(eps=epsilon, min_samples=5, metric='haversine').fit(np.radians(coords))
    good_df['cluster_id'] = db.labels_

    centroids = (
        good_df
        .groupby('cluster_id')[['latitude', 'longitude']]
        .mean()
        .reset_index()
        .rename(columns={'latitude': 'cent_lat', 'longitude': 'cent_lng'})
    )

    df = df.merge(
        good_df[['nms_id', 'cluster_id']],
        on='nms_id', how='left'
    ).merge(
        centroids,
        on='cluster_id', how='left'
    )

    df['cluster_id'] = df['cluster_id'].fillna(-1).astype(int)
    df['cent_lat'] = df['cent_lat'].where(df['cluster_id'] >= 0, None)
    df['cent_lng'] = df['cent_lng'].where(df['cluster_id'] >= 0, None)

    stores = df.to_dict(orient='records')

    kakao_api_key = os.getenv('KAKAO_API_KEY')

    current_dir = os.path.dirname(os.path.abspath(__file__))
    geojson_path = os.path.join(current_dir, 'templates', 'dongdaemun-gu.geojson')
    with open(geojson_path, encoding="utf-8") as f:
        dongdaemun_geo = json.load(f)

    return render_template(
        'map.html',
        stores=stores,
        kakao_api_key=kakao_api_key,
        dongdaemun_geo=dongdaemun_geo,
        limit=limit,
        min_rating=min_rating
    )


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
