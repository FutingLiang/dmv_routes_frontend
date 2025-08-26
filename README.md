# 台灣客運路線資料查詢系統

以 Flask + PostgreSQL/SQLAlchemy 建置的查詢/統計/匯出服務，提供公路總局客運路線資料的檢視與分析。前端位於 `templates/index.html` 並搭配 `static/`。

- 後端：`Flask`、`Flask-CORS`、`SQLAlchemy`
- 匯入工具：`公路總局客運資料匯入.py`（Excel → PostgreSQL `dmv_routes_2025`）
- 匯出：Excel 下載兩種統計表
- 主要程式：`app.py`

---

## 環境需求
- Windows 10/11
- Python 3.10+（建議 3.11）
- PostgreSQL 14+（本機或遠端）

依賴套件在 `requirements.txt`：
- Flask 2.3.3
- Flask-CORS 4.0.0
- pandas 2.0.3
- SQLAlchemy 2.0.21
- psycopg2-binary 2.9.7
- openpyxl 3.1.2

---

## 安裝與啟動

1) 進入專案目錄（PowerShell）
```powershell
cd "g:\桃園公車評鑑程式專案\公路局路線\"
```

2) 建立虛擬環境並安裝套件（Windows）
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

3) 設定環境變數（可選）
- 建議先確認並調整 `PG_DSN`。
```powershell
set FLASK_HOST=127.0.0.1
set FLASK_PORT=5050
set FLASK_DEBUG=1
set PG_DSN=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/postgres
set SKIP_DB=0
```

4) 啟動服務
```powershell
python app.py
```
- 瀏覽器開啟 http://127.0.0.1:5050/

---

## 環境變數
在 `app.py` 中，若未設定環境變數，預設如下：
- `FLASK_HOST=127.0.0.1`
- `FLASK_PORT=5050`
- `FLASK_DEBUG=1`
- `PG_DSN=postgresql+psycopg2://postgres:s8304021@localhost:5432/postgres`（請修改密碼！）
- `SKIP_DB=0`（啟動前會做 DB 健檢；設 `1` 可略過）

健檢說明：
- `SKIP_DB=0` 時，啟動會先執行 `SELECT 1` 測試連線；失敗會印出 DSN 與錯誤細節。

---

## 匯入資料（PostgreSQL）
執行：
```powershell
python 公路總局客運資料匯入.py
```

請先確認（程式第 18 行）：
- `data_folder = r"C:\\Users\\root\\Desktop\\114公路總局_客運路線表"` 指向含年度 Excel 的資料夾
- 會建立/覆寫表 `dmv_routes_2025`，並插入清理後資料

匯入腳本功能（摘要）：
- 依檔名辨識「區域」與「路線類型」（國道/一般公路）
- 清理欄位、標準化格式
- 匯入失敗逐行補救與 CSV 報表

---

## API 端點（`app.py`）

- `GET /`：載入前端 `templates/index.html`
- `GET /debug`：載入專案根目錄的 `debug.html`
- `GET /test`：載入 `simple_test.html`（若存在）

資料查詢：
- `GET /api/routes?limit=300`
  - 回傳部分路線資料與總覽統計
  - 參數：`limit`（預設 300）
- `GET /api/routes/search?district=&route_type=&search=&page=1&per_page=20`
  - 條件查詢 + 分頁
  - 參數：
    - `district`：如 `taipei_district`/`taipei_city`/`hsinchu`/`taichung`/`chiayi`/`kaohsiung`
    - `route_type`：`hwy_routes` 或 `local_routes`
    - `search`：對「路線名稱 / 路線編號 / 公司名稱」做 ILIKE 模糊搜尋
    - `page`、`per_page`

統計與匯出：
- `GET /api/statistics`
  - 監理所 × 路線類型彙整，含總業者數
- `GET /api/detailed-statistics`
  - 監理所 → 公司 → 類型層級的詳細統計，附各監理所小計
- `GET /api/sample-table`
  - 依「班次一」計算 24 以下與 25 以上的路線數與樣本數
- `GET /export/detailed-statistics.xlsx`
  - 下載「調查範圍_標的」Excel（公司明細 + 區小計）
- `GET /export/sample-table.xlsx`
  - 下載「每日往返 24/25 樣本表」Excel（明細 + 區小計 + 總計）

注意：使用上述 API 前，請先完成匯入，確保 `dmv_routes_2025` 有資料。

---

## 前端介面

檔案位置：
- `templates/index.html`（Bootstrap 5 + Font Awesome）
- `static/script.js`
- `static/style.css`

主要功能：
- 首頁統計卡：總路線數、一般公路、國道客運、監理所數
- 調查範圍（標的）：各區監理所 × 受評業者 × 路線類型彙整，支援 Excel 匯出
- 24/25 樣本表：依每日往返班次彙整，支援 Excel 匯出
- 搜尋與篩選：監理所、路線類型、關鍵字，支援分頁顯示
- 路線資料表：基本欄位清單，可 CSV 匯出與重新載入

---

## SQLite（選用）

若需產生可攜式資料庫以便測試：
```powershell
python simple_migrate.py
```
- 產出 `dmv_routes.db` 並顯示各監理所摘要
- 注意：目前 `app.py` 仍使用 PostgreSQL，如需改用 SQLite，需自行調整應用程式

---

## 專案結構（節錄）

- `app.py`：Flask 主程式與 API
- `requirements.txt`：依賴套件
- `公路總局客運資料匯入.py`：資料匯入（Excel → PostgreSQL）
- `simple_migrate.py`：PostgreSQL → SQLite 遷移
- `check_db.py`：資料表 `dmv_routes_2025` 健檢
- `templates/`：前端模板（`index.html`）
- `static/`：靜態資源（`style.css`、`script.js`）
- `debug.html`：除錯頁（根目錄）

---

## 疑難排解

- 服務啟動失敗或埠號占用
  - `FLASK_HOST=127.0.0.1`（預設）
  - `FLASK_PORT=5050`（預設）或改其他未占用埠
- PostgreSQL 連線失敗
  - 檢查 `PG_DSN` 主機/埠/帳密/防火牆/服務啟動
  - 可先 `set SKIP_DB=1` 略過健檢啟動，再逐步排查
- 匯入找不到資料夾
  - 調整 `公路總局客運資料匯入.py` 內的 `data_folder` 路徑

---

## 授權

僅供專案內部或示範使用。如需商用，請先確認資料授權。
