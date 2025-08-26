import psycopg2

try:
    conn = psycopg2.connect('postgresql://postgres:s8304021@localhost:5432/postgres')
    cur = conn.cursor()
    
    # 檢查資料表是否存在
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'dmv_routes_2025'
        )
    """)
    exists = cur.fetchone()[0]
    print(f'Table dmv_routes_2025 exists: {exists}')
    
    if exists:
        cur.execute('SELECT COUNT(*) FROM dmv_routes_2025')
        count = cur.fetchone()[0]
        print(f'Records count: {count}')
    else:
        print('Table does not exist - migration needed')
    
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')
