import pandas as pd
import os
from sqlalchemy import create_engine

# 切換到桌面
os.chdir("C:\\Users\\root\\Desktop\\114公路總局_客運路線表")

# PostgreSQL 資料庫連線設定（請依照你的環境調整）
engine = create_engine('postgresql+psycopg2://postgres:s8304021@localhost:5432/postgres')

# 中文區域關鍵字與英文代碼對照表
district_map = {
    "臺北市區": "taipei",
    "臺北": "taipei",
    "台北": "taipei",
    "新竹": "hsinchu",
    "臺中": "taichung",
    "台中": "taichung",
    "嘉義": "chiayi",
    "高雄": "kaohsiung",
}

# 路線類型關鍵字與英文資料表代碼
route_map = {
    "國道": "hwy_routes",
    "一般公路": "local_routes",
    "一般客運": "local_routes",
    "一般": "local_routes"
}

# 結果清單
success_list, failed_list, skipped_list = [], [], []

# 處理桌面上所有符合條件的 Excel 檔
for file in os.listdir():
    if file.endswith(".xlsx") and "114年路線資料" in file:
        # 將檔名空白移除以提高容錯率
        file_clean = file.replace(" ", "")
        district_en = None
        route_type = None

        # 比對區域
        for zh, en in district_map.items():
            if zh in file_clean:
                district_en = en
                break

        # 比對路線類型
        for zh, en in route_map.items():
            if zh in file_clean:
                route_type = en
                break

        # 若可辨識，開始匯入
        if district_en and route_type:
            table_name = f"{district_en}_dmv_2025_{route_type}"
            try:
                df = pd.read_excel(file, sheet_name="工作表1")
                df.to_sql(table_name, engine, if_exists="replace", index=False)
                print(f"✅ 匯入完成：{file} → {table_name}")
                success_list.append((file, table_name))
            except Exception as e:
                print(f"❌ 匯入失敗：{file}，錯誤：{e}")
                failed_list.append((file, str(e)))
        else:
            print(f"⚠️ 無法辨識區域或類型：{file}")
            skipped_list.append(file)

# 顯示匯入摘要
print("\n📋 匯入結果總結")
print(f"✅ 成功匯入：{len(success_list)} 個")
print(f"❌ 匯入失敗：{len(failed_list)} 個")
print(f"⚠️ 略過未識別：{len(skipped_list)} 個")

if failed_list:
    pd.DataFrame(failed_list, columns=["檔案名稱", "錯誤訊息"]).to_csv("匯入失敗清單.csv", index=False)

if skipped_list:
    pd.DataFrame(skipped_list, columns=["未識別檔案名稱"]).to_csv("略過清單.csv", index=False)

print("📁 已輸出：匯入成功清單.csv、匯入失敗清單.csv、略過清單.csv（如有）")

