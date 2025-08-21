import os
import sys
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, inspect, text
from datetime import datetime
import pytz
import re
import glob

# 設定控制台編碼為UTF-8
if sys.platform == "win32":
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 設定資料夾路徑
data_folder = r"C:\Users\root\Desktop\114公路總局_客運路線表"
if not os.path.exists(data_folder):
    print("找不到指定資料夾，請確認路徑是否正確")
    exit(1)

os.chdir(data_folder)

# PostgreSQL 連線
engine = create_engine('postgresql+psycopg2://postgres:s8304021@localhost:5432/postgres')

# 區域 / 路線類型對照
district_map = {
    "臺北市區": "taipei", "臺北": "taipei", "台北": "taipei",
    "新竹": "hsinchu",
    "臺中": "taichung", "台中": "taichung",
    "嘉義": "chiayi",
    "高雄": "kaohsiung",
}
route_map = {
    "國道": "hwy_routes",
    "一般公路": "local_routes",
    "一般客運": "local_routes",
    "一般": "local_routes",
}

TARGET_TABLE = "dmv_routes_2025"
success_list, failed_list, skipped_list = [], [], []
table_created = False

tz = pytz.timezone("Asia/Taipei")
now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S%z")

def clean_numeric_field(value):
    """清理數值欄位，移除非數字字符並轉換為適當類型"""
    if pd.isna(value) or value is None:
        return None
    
    # 轉換為字串並清理
    str_val = str(value).strip()
    
    # 移除換行符和多餘空白
    str_val = re.sub(r'\s+', ' ', str_val)
    
    # 如果包含非數字字符（除了小數點），嘗試提取數字部分
    if re.search(r'[^\d\.]', str_val):
        # 提取第一個數字序列
        match = re.search(r'(\d+\.?\d*)', str_val)
        if match:
            str_val = match.group(1)
        else:
            return None
    
    # 嘗試轉換為數字
    try:
        if '.' in str_val:
            return float(str_val)
        else:
            return int(str_val)
    except (ValueError, TypeError):
        return None

def clean_route_number(value):
    """清理路線編號，保持原始格式但確保資料庫相容性"""
    if pd.isna(value) or value is None:
        return None
    
    # 轉換為字串並清理空白字符
    str_val = str(value).strip()
    str_val = re.sub(r'\s+', ' ', str_val)
    
    return str_val if str_val else None

def normalize_column_names(df):
    """標準化欄位名稱，處理不同檔案的命名差異"""
    df_normalized = df.copy()
    
    # 建立欄位名稱對應表
    column_mapping = {
        # 里程相關
        '里_程': '里程往',
        '里程': '里程往',
        '里程_往': '里程往',
        '里程_返': '里程返',
        
        # 班次相關
        '班_次': '班次一',  # 通用班次欄位對應到班次一
        '班_次一': '班次一',
        '班_次二': '班次二', 
        '班_次三': '班次三',
        '班_次四': '班次四',
        '班_次五': '班次五',
        '班_次六': '班次六',
        '班_次日': '班次日',
        '班次_一': '班次一',
        '班次_二': '班次二',
        '班次_三': '班次三',
        '班次_四': '班次四',
        '班次_五': '班次五',
        '班次_六': '班次六',
        '班次_日': '班次日',
        
        # 路線性質相關
        '路線性質_(機場/一般)': '路線性質',
        '路線性質_機場_一般': '路線性質',
        '路線性質': '路線性質',
        
        # 其他欄位
        '公司_名稱': '公司名稱',
        '路線_編號': '路線編號',
        '路線_名稱': '路線名稱',
        '補貼__路線': '補貼_路線',
        '站牌數': '站牌數往',  # 通用站牌數對應到站牌數往
        '站牌數_往': '站牌數往',
        '站牌數_返': '站牌數返',
        '車輛_數': '車輛數',
        '聯營_業者': '聯營業者'
    }
    
    # 重新命名欄位
    df_normalized.rename(columns=column_mapping, inplace=True)
    
    return df_normalized

def clean_dataframe(df):
    """清理整個DataFrame的資料"""
    df_clean = df.copy()
    
    # 數值欄位清理
    numeric_columns = ['里程往', '里程返', '班次一', '班次二', '班次三', '班次四', 
                      '班次五', '班次六', '班次日', '站牌數往', '站牌數返', '車輛數']
    
    for col in numeric_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(clean_numeric_field)
    
    # 路線編號特殊處理（保持為文字但清理格式）
    if '路線編號' in df_clean.columns:
        df_clean['路線編號'] = df_clean['路線編號'].apply(clean_route_number)
    
    # 文字欄位清理（移除多餘空白和換行符）
    text_columns = ['公司名稱', '路線名稱', '補貼_路線', '聯營業者', '路線性質']
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).apply(
                lambda x: re.sub(r'\s+', ' ', str(x).strip()) if pd.notna(x) and str(x).strip() != 'nan' else None
            )
    
    return df_clean

def pick_sheet_name(xlsx_path, preferred="工作表1"):
    try:
        xl = pd.ExcelFile(xlsx_path)
        if preferred in xl.sheet_names:
            return preferred
        return xl.sheet_names[0]
    except Exception:
        return preferred

def create_table_with_proper_types(df, table_name, engine):
    """建立具有適當資料類型的資料表，包含所有可能的欄位"""
    
    # 定義完整的欄位類型對應（包含所有可能出現的欄位）
    column_types = {
        '公司名稱': 'VARCHAR(100)',
        '路線編號': 'VARCHAR(20)',
        '路線名稱': 'VARCHAR(200)',
        '里程往': 'DECIMAL(10,2)',
        '里程返': 'DECIMAL(10,2)',
        '班次一': 'INTEGER',
        '班次二': 'INTEGER',
        '班次三': 'INTEGER',
        '班次四': 'INTEGER',
        '班次五': 'INTEGER',
        '班次六': 'INTEGER',
        '班次日': 'INTEGER',
        '補貼_路線': 'VARCHAR(10)',
        '站牌數往': 'INTEGER',
        '站牌數返': 'INTEGER',
        '車輛數': 'INTEGER',
        '聯營業者': 'VARCHAR(200)',
        '路線性質': 'VARCHAR(20)',  # 新增路線性質欄位
        'district': 'VARCHAR(20)',
        'route_type': 'VARCHAR(20)',
        'source_file': 'VARCHAR(200)',
        'imported_at': 'VARCHAR(30)'
    }
    
    # 建立包含所有可能欄位的完整資料表
    columns_def = []
    for col_name, col_type in column_types.items():
        columns_def.append(f'"{col_name}" {col_type}')
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        {', '.join(columns_def)}
    )
    """
    
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        conn.execute(text(create_sql))
        conn.commit()

inspector = inspect(engine)

# 使用glob來處理可能的編碼問題
xlsx_files = glob.glob("*.xlsx")
for file in xlsx_files:
    # 檢查是否為Excel臨時檔案，但仍嘗試處理
    if file.startswith('~$'):
        print(f"⚠️ 檢測到Excel臨時檔案，嘗試處理：{file}")
        
    # 檢查檔案名稱是否包含路線資料關鍵字
    if "114" in file and ("路線" in file or "route" in file.lower()):
        file_clean = file.replace(" ", "")
        district_en = None
        route_type = None

        for zh, en in district_map.items():
            if zh in file_clean:
                district_en = en
                break
        for zh, en in route_map.items():
            if zh in file_clean:
                route_type = en
                break

        if not (district_en and route_type):
            try:
                print(f"⚠️ 無法辨識區域或類型：{file}")
            except UnicodeEncodeError:
                print(f"⚠️ 無法辨識區域或類型：{repr(file)}")
            skipped_list.append(file)
            continue

        try:
            sheet_name = pick_sheet_name(file, preferred="工作表1")
            df = pd.read_excel(file, sheet_name=sheet_name)

            # 欄名清理
            df.columns = (
                df.columns.astype(str)
                  .str.strip()
                  .str.replace(r"\s+", "_", regex=True)
                  .str.replace(r"[\r\n]+", "_", regex=True)
            )
            
            # 移除空白或無名欄位
            columns_to_drop = [col for col in df.columns if col.startswith('Unnamed:') or col.strip() == '']
            if columns_to_drop:
                df = df.drop(columns=columns_to_drop)
            
            # 標準化欄位名稱
            df = normalize_column_names(df)

            # 資料清理
            df = clean_dataframe(df)

            # 追蹤欄位
            df["district"]    = district_en
            df["route_type"]  = route_type
            df["source_file"] = file
            df["imported_at"] = now_str

            if not table_created:
                # 建立具有適當資料類型的資料表（包含所有可能欄位）
                create_table_with_proper_types(df, TARGET_TABLE, engine)
                table_created = True
            
            # 確保DataFrame包含所有必要欄位（填入None如果不存在）
            required_columns = ['公司名稱', '路線編號', '路線名稱', '里程往', '里程返', 
                              '班次一', '班次二', '班次三', '班次四', '班次五', '班次六', '班次日',
                              '補貼_路線', '站牌數往', '站牌數返', '車輛數', '聯營業者', '路線性質']
            
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None

            # 使用批次插入，並處理可能的資料類型問題
            try:
                df.to_sql(
                    TARGET_TABLE, engine,
                    if_exists="append", index=False,
                    chunksize=100, method="multi"
                )
            except Exception as insert_error:
                # 如果批次插入失敗，嘗試逐行插入以找出問題資料
                print(f"⚠️ 批次插入失敗，嘗試逐行插入：{file}")
                successful_rows = 0
                
                for idx, row in df.iterrows():
                    try:
                        row_df = pd.DataFrame([row])
                        row_df.to_sql(
                            TARGET_TABLE, engine,
                            if_exists="append", index=False
                        )
                        successful_rows += 1
                    except Exception as row_error:
                        print(f"   第 {idx+1} 行插入失敗: {str(row_error)[:100]}...")
                        continue
                
                print(f"   成功插入 {successful_rows}/{len(df)} 行")

            print(f"✅ 已匯入：{file} → {TARGET_TABLE}（district={district_en}, route_type={route_type}）")
            success_list.append((file, TARGET_TABLE))

        except Exception as e:
            error_msg = f"匯入失敗：{file}，錯誤：{str(e)}"
            print(f"❌ {error_msg}")
            failed_list.append((file, str(e)))

# 匯入摘要與報表
print("\n📋 匯入結果總結")
print(f"✅ 成功匯入：{len(success_list)} 個檔案 → {TARGET_TABLE}")
print(f"❌ 匯入失敗：{len(failed_list)} 個")
print(f"⚠️ 略過未識別：{len(skipped_list)} 個")

# 輸出詳細報表
pd.DataFrame(success_list, columns=["檔案名稱", "寫入資料表"]).to_csv("匯入成功清單.csv", index=False, encoding='utf-8-sig')
if failed_list:
    pd.DataFrame(failed_list, columns=["檔案名稱", "錯誤訊息"]).to_csv("匯入失敗清單.csv", index=False, encoding='utf-8-sig')
if skipped_list:
    pd.DataFrame(skipped_list, columns=["未識別檔案名稱"]).to_csv("略過清單.csv", index=False, encoding='utf-8-sig')

print("📁 已輸出：匯入成功清單.csv、匯入失敗清單.csv、略過清單.csv（如有）")

# 資料品質檢查
try:
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) as total_rows FROM {TARGET_TABLE}"))
        total_rows = result.fetchone()[0]
        
        result = conn.execute(text(f"""
            SELECT district, route_type, COUNT(*) as count 
            FROM {TARGET_TABLE} 
            GROUP BY district, route_type 
            ORDER BY district, route_type
        """))
        
        print(f"\n📊 資料統計（總計 {total_rows} 筆）：")
        for row in result:
            print(f"   {row[0]} - {row[1]}: {row[2]} 筆")
            
except Exception as e:
    print(f"⚠️ 無法執行資料統計：{e}")
