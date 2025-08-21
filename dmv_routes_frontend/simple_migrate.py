import sqlite3
import psycopg2
import os

def migrate_to_sqlite():
    """簡單的 PostgreSQL 到 SQLite 遷移"""
    
    # 連接 PostgreSQL
    pg_conn = psycopg2.connect(
        host='localhost',
        database='postgres', 
        user='postgres',
        password='s8304021'
    )
    
    # 創建 SQLite 資料庫
    sqlite_path = os.path.join(os.path.dirname(__file__), 'dmv_routes.db')
    sqlite_conn = sqlite3.connect(sqlite_path)
    
    try:
        print("開始遷移資料...")
        
        # 從 PostgreSQL 讀取資料
        pg_cursor = pg_conn.cursor()
        pg_cursor.execute("""
            SELECT 
                district, route_type, source_file, "公司名稱", "路線編號", "路線名稱",
                "里程往", "里程返", "班次一", "班次二", "班次三", "班次四", "班次五", "班次六", "班次日",
                "站牌數往", "站牌數返", "車輛數", "補貼_路線", "聯營業者", "路線性質"
            FROM dmv_routes_2025
            ORDER BY district, route_type, "路線編號"
        """)
        
        rows = pg_cursor.fetchall()
        print(f"讀取了 {len(rows)} 筆資料")
        
        # 創建 SQLite 表格
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("DROP TABLE IF EXISTS dmv_routes_2025")
        
        sqlite_cursor.execute("""
            CREATE TABLE dmv_routes_2025 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                district TEXT,
                route_type TEXT,
                source_file TEXT,
                "公司名稱" TEXT,
                "路線編號" TEXT,
                "路線名稱" TEXT,
                "里程往" REAL,
                "里程返" REAL,
                "班次一" INTEGER,
                "班次二" INTEGER,
                "班次三" INTEGER,
                "班次四" INTEGER,
                "班次五" INTEGER,
                "班次六" INTEGER,
                "班次日" INTEGER,
                "站牌數往" INTEGER,
                "站牌數返" INTEGER,
                "車輛數" INTEGER,
                "補貼_路線" TEXT,
                "聯營業者" TEXT,
                "路線性質" TEXT
            )
        """)
        
        # 插入資料
        insert_sql = """
            INSERT INTO dmv_routes_2025 (
                district, route_type, source_file, "公司名稱", "路線編號", "路線名稱",
                "里程往", "里程返", "班次一", "班次二", "班次三", "班次四", "班次五", "班次六", "班次日",
                "站牌數往", "站牌數返", "車輛數", "補貼_路線", "聯營業者", "路線性質"
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # 處理每一行資料，轉換 Decimal 類型
        processed_rows = []
        for row in rows:
            processed_row = []
            for value in row:
                if value is None:
                    processed_row.append(None)
                elif str(type(value)) == "<class 'decimal.Decimal'>":
                    processed_row.append(float(value))
                else:
                    processed_row.append(value)
            processed_rows.append(tuple(processed_row))
        
        sqlite_cursor.executemany(insert_sql, processed_rows)
        sqlite_conn.commit()
        
        # 驗證結果
        sqlite_cursor.execute("SELECT COUNT(*) FROM dmv_routes_2025")
        count = sqlite_cursor.fetchone()[0]
        print(f"成功插入 {count} 筆資料到 SQLite")
        
        # 顯示統計
        sqlite_cursor.execute("""
            SELECT 
                CASE 
                    WHEN source_file LIKE '%臺北區監理所%' THEN '臺北區監理所'
                    WHEN source_file LIKE '%臺北市區監理所%' THEN '臺北市區監理所'
                    WHEN district = 'hsinchu' THEN '新竹區監理所'
                    WHEN district = 'taichung' THEN '臺中區監理所'
                    WHEN district = 'chiayi' THEN '嘉義區監理所'
                    WHEN district = 'kaohsiung' THEN '高雄區監理所'
                    ELSE district
                END as district_name,
                route_type,
                COUNT(*) as count
            FROM dmv_routes_2025 
            GROUP BY district_name, route_type
            ORDER BY district_name, route_type
        """)
        
        stats = sqlite_cursor.fetchall()
        print("\n各監理所統計:")
        for row in stats:
            route_type_name = "國道客運" if row[1] == "hwy_routes" else "一般公路"
            print(f"  {row[0]} - {route_type_name}: {row[2]}條")
        
        print(f"\n遷移完成！SQLite 檔案位置: {sqlite_path}")
        return True
        
    except Exception as e:
        print(f"遷移失敗: {e}")
        return False
        
    finally:
        pg_conn.close()
        sqlite_conn.close()

if __name__ == "__main__":
    success = migrate_to_sqlite()
    if success:
        print("\n可以使用 SQLite 版本了！")
        print("執行: python app_sqlite.py")
    else:
        print("\n遷移失敗")
