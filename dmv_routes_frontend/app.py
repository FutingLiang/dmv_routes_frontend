from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import pandas as pd
from sqlalchemy import create_engine, text
import json, os

app = Flask(__name__)
CORS(app)

# PostgreSQL 連線（僅使用 Postgres）
PG_DSN = os.getenv('PG_DSN', 'postgresql+psycopg2://postgres:s8304021@localhost:5432/postgres')
engine = create_engine(PG_DSN, pool_pre_ping=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/debug')
def debug():
    with open('debug.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/test')
def test():
    with open('simple_test.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/api/routes')
def get_routes():
    """取得所有路線資料和統計資訊（可用 limit 限制筆數）"""
    try:
        # 新增可調整的限制，預設 300 筆，避免一次撈整張表
        try:
            limit = int(request.args.get('limit', '300'))
            if limit <= 0:
                limit = 300
        except Exception:
            limit = 300

        with engine.connect() as conn:
            # 取得路線資料 (根據source_file區分台北區和台北市區)
            query = """
                SELECT 
                    CASE 
                        WHEN source_file LIKE '%臺北區監理所%' THEN 'taipei_district'
                        WHEN source_file LIKE '%臺北市區監理所%' THEN 'taipei_city'
                        ELSE district
                    END as district,
                    route_type,
                    "公司名稱",
                    "路線編號", 
                    "路線名稱",
                    "里程往",
                    "里程返",
                    "班次一",
                    "班次二",
                    "班次三",
                    "班次四",
                    "班次五",
                    "班次六", 
                    "班次日",
                    "車輛數",
                    "站牌數往",
                    "站牌數返",
                    "補貼_路線",
                    "聯營業者",
                    "路線性質",
                    source_file,
                    imported_at
                FROM dmv_routes_2025 
                LIMIT :limit
            """
            
            result = conn.execute(text(query), {"limit": limit})
            routes = []
            
            for row in result:
                route_dict = {
                    'district': row[0],
                    'route_type': row[1],
                    '公司名稱': row[2],
                    '路線編號': row[3],
                    '路線名稱': row[4],
                    '里程往': float(row[5]) if row[5] is not None else None,
                    '里程返': float(row[6]) if row[6] is not None else None,
                    '班次一': row[7],
                    '班次二': row[8],
                    '班次三': row[9],
                    '班次四': row[10],
                    '班次五': row[11],
                    '班次六': row[12],
                    '班次日': row[13],
                    '車輛數': row[14],
                    '站牌數往': row[15],
                    '站牌數返': row[16],
                    '補貼_路線': row[17],
                    '聯營業者': row[18],
                    '路線性質': row[19],
                    'source_file': row[20],
                    'imported_at': row[21]
                }
                routes.append(route_dict)
            
            # 計算統計資訊
            stats_query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT district) as districts,
                    SUM(CASE WHEN route_type = 'local_routes' THEN 1 ELSE 0 END) as local_routes,
                    SUM(CASE WHEN route_type = 'hwy_routes' THEN 1 ELSE 0 END) as hwy_routes
                FROM dmv_routes_2025
            """
            
            stats_result = conn.execute(text(stats_query))
            stats_row = stats_result.fetchone()
            
            statistics = {
                'total': stats_row[0],
                'districts': stats_row[1], 
                'local_routes': stats_row[2],
                'hwy_routes': stats_row[3]
            }
            
            return jsonify({
                'success': True,
                'routes': routes,
                'statistics': statistics,
                'limit_used': limit
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/routes/search')
def search_routes():
    """搜尋路線資料"""
    try:
        # 取得查詢參數
        district = request.args.get('district', '')
        route_type = request.args.get('route_type', '')
        search_term = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 建構查詢條件
        conditions = []
        params = {}
        
        if district:
            conditions.append('district = :district')
            params['district'] = district
            
        if route_type:
            conditions.append('route_type = :route_type')
            params['route_type'] = route_type
            
        if search_term:
            conditions.append('''(
                "路線名稱" ILIKE :search_term OR 
                "路線編號" ILIKE :search_term OR 
                "公司名稱" ILIKE :search_term
            )''')
            params['search_term'] = f'%{search_term}%'
        
        where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
        
        with engine.connect() as conn:
            # 計算總數
            count_query = f"SELECT COUNT(*) FROM dmv_routes_2025 {where_clause}"
            total_count = conn.execute(text(count_query), params).fetchone()[0]
            
            # 取得分頁資料
            offset = (page - 1) * per_page
            data_query = f"""
                SELECT 
                    district, route_type, "公司名稱", "路線編號", "路線名稱",
                    "里程往", "里程返", "班次一", "車輛數", "站牌數往"
                FROM dmv_routes_2025 
                {where_clause}
                ORDER BY district, route_type, "路線編號"
                LIMIT :per_page OFFSET :offset
            """
            
            params.update({'per_page': per_page, 'offset': offset})
            result = conn.execute(text(data_query), params)
            
            routes = []
            for row in result:
                routes.append({
                    'district': row[0],
                    'route_type': row[1],
                    '公司名稱': row[2],
                    '路線編號': row[3],
                    '路線名稱': row[4],
                    '里程往': float(row[5]) if row[5] is not None else None,
                    '里程返': float(row[6]) if row[6] is not None else None,
                    '班次一': row[7],
                    '車輛數': row[8],
                    '站牌數往': row[9]
                })
            
            return jsonify({
                'success': True,
                'routes': routes,
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/statistics')
def get_statistics():
    """取得詳細統計資訊"""
    try:
        with engine.connect() as conn:
            # 按監理所和路線類型統計 (根據source_file區分台北區和台北市區)
            query = """
                SELECT 
                    CASE 
                        WHEN source_file LIKE '%臺北區監理所%' THEN 'taipei_district'
                        WHEN source_file LIKE '%臺北市區監理所%' THEN 'taipei_city'
                        ELSE district
                    END as district_key,
                    route_type,
                    COUNT(*) as route_count,
                    COUNT(DISTINCT "公司名稱") as company_count
                FROM dmv_routes_2025 
                WHERE district IS NOT NULL 
                GROUP BY district_key, route_type
                ORDER BY district_key, route_type
            """
            
            result = conn.execute(text(query))
            stats = result.fetchall()
            
            # 整理統計資料
            statistics = {}
            total_routes = 0
            total_companies = 0
            
            for row in stats:
                district = row[0]
                route_type = row[1]
                route_count = row[2]
                company_count = row[3]
                
                total_routes += route_count
                
                if district not in statistics:
                    statistics[district] = {
                        'hwy_routes': {'route_count': 0, 'company_count': 0},
                        'local_routes': {'route_count': 0, 'company_count': 0}
                    }
                
                statistics[district][route_type] = {
                    'route_count': route_count,
                    'company_count': company_count
                }
            
            # 計算總業者數
            total_companies_query = """
                SELECT COUNT(DISTINCT "公司名稱") as total_companies
                FROM dmv_routes_2025 
                WHERE "公司名稱" IS NOT NULL
            """
            result = conn.execute(text(total_companies_query))
            total_companies = result.fetchone()[0]
            
            return jsonify({
                'success': True,
                'statistics': statistics,
                'totals': {
                    'total_routes': total_routes,
                    'total_companies': total_companies
                }
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/detailed-statistics')
def get_detailed_statistics():
    """取得按監理所->客運公司->路線類型的詳細統計資訊"""
    try:
        with engine.connect() as conn:
            # 按監理所、客運公司和路線類型統計
            query = """
                SELECT 
                    CASE 
                        WHEN source_file LIKE '%臺北區監理所%' THEN '臺北區監理所'
                        WHEN source_file LIKE '%臺北市區監理所%' THEN '臺北市區監理所'
                        WHEN district = 'hsinchu' THEN '新竹區監理所'
                        WHEN district = 'taichung' THEN '台中區監理所'
                        WHEN district = 'chiayi' THEN '嘉義區監理所'
                        WHEN district = 'kaohsiung' THEN '高雄區監理所'
                        ELSE district
                    END as district_name,
                    "公司名稱",
                    route_type,
                    COUNT(*) as route_count
                FROM dmv_routes_2025 
                WHERE "公司名稱" IS NOT NULL 
                GROUP BY district_name, "公司名稱", route_type
                ORDER BY district_name, "公司名稱", route_type
            """
            
            result = conn.execute(text(query))
            rows = result.fetchall()
            
            # 整理統計資料
            detailed_stats = {}
            
            for row in rows:
                district = row[0]
                company = row[1]
                route_type = row[2]
                count = row[3]
                
                if district not in detailed_stats:
                    detailed_stats[district] = {}
                
                if company not in detailed_stats[district]:
                    detailed_stats[district][company] = {
                        'hwy_routes': 0,
                        'local_routes': 0,
                        'total': 0
                    }
                
                detailed_stats[district][company][route_type] = count
                detailed_stats[district][company]['total'] += count
            
            # 計算每個監理所的總計
            district_totals = {}
            for district, companies in detailed_stats.items():
                district_totals[district] = {
                    'hwy_routes': 0,
                    'local_routes': 0,
                    'total': 0,
                    'companies': len(companies)
                }
                
                for company_data in companies.values():
                    district_totals[district]['hwy_routes'] += company_data.get('hwy_routes', 0)
                    district_totals[district]['local_routes'] += company_data.get('local_routes', 0)
                    district_totals[district]['total'] += company_data.get('total', 0)
            
            return jsonify({
                'success': True,
                'detailed_statistics': detailed_stats,
                'district_totals': district_totals
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')  # 使用本地回環避免 WinError 10013
    port = int(os.getenv('FLASK_PORT', '5050'))  # 改用 5050 端口避免衝突
    debug = os.getenv('FLASK_DEBUG', '1') == '1'

    # 啟動前健康檢查（可快速定位 Postgres 連線問題）
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print(f"PostgreSQL 連線成功: {PG_DSN}")
    except Exception as e:
        print("PostgreSQL 連線失敗，請檢查主機/埠號/帳號密碼/防火牆與服務狀態：")
        print(f"  DSN: {PG_DSN}")
        print(f"  錯誤: {e}")
        raise

    app.run(debug=debug, host=host, port=port)
