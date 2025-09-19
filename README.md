# dmv_routes_frontend 專案說明

本專案為以 Flask 建置的前後端整合服務，連線 PostgreSQL/SQLAlchemy，提供公路總局客運路線資料的查詢、統計與 Excel 輸出。

- 後端：`Flask` + `SQLAlchemy`
- 資料庫：PostgreSQL（預設），提供 SQLite 遷移工具
- 匯入工具：`公路總局客運資料匯入.py`（將 Excel 路線資料匯入 PostgreSQL 的 `dmv_routes_2025` 表）
- 主要服務檔案：`app.py`

---

## 需求環境
- Windows 10/11
- Python 3.10+（建議 3.11）
- PostgreSQL 14+（本機或遠端均可）

---

## 安裝步驟（首次）
1) 下載或複製此專案至本機。
2) 在專案根目錄執行：
   
   會自動建立 `.venv` 虛擬環境並安裝 `requirements.txt`。

> 如遇到權限/防火牆問題，請以系統管理員身分執行 CMD 或調整安全性設定。

---

## 啟動服務
1) 確認 PostgreSQL 可連線，且已建立資料表 `dmv_routes_2025`（見下方匯入資料）。

2) 執行 `python app.py` 啟動服務。

3) 瀏覽器前往 `http://127.0.0.1:5050/`。

預設設定（可用環境變數覆寫）：
- `FLASK_HOST=127.0.0.1`
- `FLASK_PORT=5050`
- `FLASK_DEBUG=1`
- `PG_DSN=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/postgres`
- `SKIP_DB=1`（可略過啟動前 DB 健檢，預設 0）

---

## 環境變數說明
- `PG_DSN`：PostgreSQL 連線字串（SQLAlchemy 格式）。
  - 範例：`postgresql+psycopg2://postgres:password@localhost:5432/postgres`
- `FLASK_HOST`、`FLASK_PORT`、`FLASK_DEBUG`：Flask 啟動參數。
- `SKIP_DB`：設定為 `1` 可略過啟動前健康檢查（在 `app.py` 中使用）。

> 預設 DSN 目前寫在 `app.py` 的 `PG_DSN` 變數中，請依實際情況修改或以環境變數覆寫。

---

## 匯入資料（PostgreSQL）
執行 `python 公路總局客運資料匯入.py`。

請先確認並視需要修改：
- `公路總局客運資料匯入.py` 第 18 行的資料夾：`data_folder = r"C:\\Users\\root\\Desktop\\114公路總局_客運路線表"`
- 將對應年度/區別的 Excel 置於該資料夾。
- 會建立/覆寫表 `dmv_routes_2025`，並插入清理後資料。

匯入腳本功能：
- 自動辨識檔名中的區域與路線類型。
- 標準化欄位名稱、清理數值/文字欄位。
- 失敗逐行補救插入與清單報表輸出（`csv`）。

---

## API 端點（`app.py`）
- `GET /`：載入 `templates/index.html`（前端頁面）。
- `GET /debug`：載入 `debug.html`。
- `GET /test`：載入 `simple_test.html`（若檔案存在）。

- `GET /api/routes?limit=300`：
  - 取得部分路線資料與基本統計。
  - 參數：`limit`（預設 300）。

- `GET /api/routes/search?district=&route_type=&search=&page=1&per_page=20`：
  - 依條件分頁查詢。
  - 參數：`district`、`route_type`（`hwy_routes`/`local_routes`）、`search`、`page`、`per_page`。

- `GET /api/statistics`：
  - 監理所 × 路線類型彙整，含總業者數。

- `GET /api/detailed-statistics`：
  - 監理所 → 公司 → 類型層級統計，並含各監理所小計。

- `GET /api/sample-table`：
  - 依每日往返班次（以「班次一」判斷）計算 24 以下與 25 以上的樣本數彙整。

- Excel 匯出：
  - `GET /export/detailed-statistics.xlsx`
  - `GET /export/sample-table.xlsx`

> 所有 API 須先有資料表 `dmv_routes_2025` 並有資料。

---

## SQLite 遷移（可選）
若想以 SQLite 測試/攜帶式資料庫：
1) 確保 PostgreSQL 有資料。
2) 執行 `python simple_migrate.py`。
3) 產生 `dmv_routes.db`，並會顯示各監理所統計摘要。

> 目前 `app.py` 仍使用 PostgreSQL。若要改 SQLite，需另行撰寫/切換對應的 app 檔（例如 `app_sqlite.py`）。

---

## 專案結構（節錄）
- `app.py`：Flask 主程式與 API。
- `requirements.txt`：套件列表。
- `公路總局客運資料匯入.py`：資料匯入（Excel → PostgreSQL）。
- `simple_migrate.py`：PostgreSQL → SQLite 遷移工具。
- `check_db.py`：檢查 `dmv_routes_2025` 是否存在與筆數。
- `templates/`：前端模板（`index.html` 等）。
- `static/`：靜態檔案。

---

## 疑難排解
- 無法啟動（WinError 10013 或埠號占用）
  - 將 `FLASK_HOST` 設為 `127.0.0.1`（已預設）。
  - 改用 `FLASK_PORT=5050`（已預設）或其他未占用埠。
- PostgreSQL 連線失敗
  - 檢查 `PG_DSN` 主機/埠/帳密/防火牆/服務啟動。
  - 可先將 `SKIP_DB=1` 啟動服務，再逐步排查。
- 匯入找不到資料夾
  - 調整 `公路總局客運資料匯入.py` 的 `data_folder`。

---

## 授權
僅供專案內部或示範使用，如需商用請先確認資料授權。
