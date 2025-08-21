# 台灣客運路線資料查詢系統

本專案是一個以 Flask 為後端、Bootstrap 為前端樣式的單頁應用，提供全台公路汽車客運路線的查詢、篩選與統計視覺化。

- 後端：`Flask` + `SQLAlchemy` 連線 PostgreSQL 取得資料表 `dmv_routes_2025`
- 前端：`templates/index.html` + `static/script.js` + `Bootstrap 5`
- API：提供路線清單、搜尋、統計等 JSON 端點

## 專案結構

- `app.py`：Flask 主應用程式與 API 路由
- `templates/index.html`：首頁版型（顯示統計卡片、表格、分頁、篩選）
- `static/script.js`：前端邏輯（載入資料、搜尋、分頁、統計表渲染）
- `static/style.css`：樣式（如需自訂）
- `requirements.txt`：Python 套件需求
- `check_db.py`：快速檢查 PostgreSQL 中 `dmv_routes_2025` 表是否存在及筆數
- `simple_migrate.py`：示範從 PostgreSQL 匯出資料到本地 SQLite 的遷移工具
- `debug.html`：簡易除錯頁面（`/debug` 端點）

## 環境需求

- Python 3.10+（建議）
- PostgreSQL 12+（需具備資料表 `dmv_routes_2025`）
- Windows（本 README 指令以 Windows 範例為主）

## 安裝與啟動

1) 建立與啟用虛擬環境（Windows PowerShell）

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2) 安裝套件

```powershell
pip install -r requirements.txt
```

3) 設定資料庫連線（可選，否則使用 `app.py` 預設）

`app.py` 會讀取環境變數 `PG_DSN`，若未設定，預設為：

```
postgresql+psycopg2://postgres:s8304021@localhost:5432/postgres
```

建議以環境變數覆寫（密碼請改為你自己的）：

```powershell
set PG_DSN=postgresql+psycopg2://<user>:<password>@<host>:<port>/<database>
```

其他可用環境變數：

```powershell
set FLASK_HOST=127.0.0.1   # 預設 127.0.0.1（避免 WinError 10013）
set FLASK_PORT=5050        # 預設 5050
set FLASK_DEBUG=1          # 1 開啟、0 關閉
```

4) 確認資料表存在

執行檢查腳本：

```powershell
python check_db.py
```

若顯示 `Table does not exist`，請先在 PostgreSQL 建立並匯入資料至 `dmv_routes_2025`。資料欄位（依 `app.py`/查詢使用）：

- `district`（如：taipei_district, taipei_city, hsinchu, taichung, chiayi, kaohsiung）
- `route_type`（`local_routes` 一般公路、`hwy_routes` 國道客運）
- `source_file`（用於分辨臺北區/臺北市區）
- 中文欄位：`公司名稱`、`路線編號`、`路線名稱`、`里程往`、`里程返`、`班次一`…`班次日`、`車輛數`、`站牌數往`、`站牌數返`、`補貼_路線`、`聯營業者`、`路線性質`
- `imported_at`（可選）

5) 啟動服務

```powershell
python app.py
```

啟動後預設網址：http://127.0.0.1:5050/

## 使用方式（前端）

打開首頁 `/`：

- __統計卡片__：顯示總路線數、一般公路、國道客運、監理所數（呼叫 `/api/routes` 的統計彙總）
- __調查範圍表__：由 `/api/detailed-statistics` 生成，列出各監理所、各業者分路線類型數量
- __搜尋與篩選__：依監理所、路線類型、關鍵字（路線名稱/編號/公司）本地篩選
- __資料表__：顯示路線清單與分頁，並提供「匯出 CSV」與「重新載入」按鈕（前端功能位於 `static/script.js`）

## API 端點

- `GET /`：首頁（`templates/index.html`）
- `GET /debug`：除錯頁（`debug.html`）
- `GET /api/routes?limit=300`：
  - 回傳路線清單（最多 limit 筆，預設 300）與整體統計 `{ total, districts, local_routes, hwy_routes }`
- `GET /api/routes/search?district=&route_type=&search=&page=1&per_page=20`：
  - 伺服器端搜尋與分頁（支援 `ILIKE` 模糊比對中文欄位）
- `GET /api/statistics`：
  - 依監理所與路線類型彙整，另回傳 `total_routes` 與 `total_companies`
- `GET /api/detailed-statistics`：
  - 依「監理所 → 客運公司 → 路線類型」的巢狀統計，並附各監理所總計

說明：部分端點會依 `source_file` 內容將「臺北區/臺北市區」重新映射。

## 資料庫注意事項

- 需在 PostgreSQL 建立 `dmv_routes_2025` 資料表並匯入資料。
- 若需要離線 Demo，可參考 `simple_migrate.py` 將 PostgreSQL 資料匯出到本機 SQLite：

```powershell
python simple_migrate.py
```

完成後會產生 `dmv_routes.db`（僅供示範；目前 `app.py` 僅支援 PostgreSQL）。

## 常見問題排除（Windows）

- __WinError 10013__：維持 `FLASK_HOST=127.0.0.1`，或確認防火牆/權限。
- __連線 PostgreSQL 失敗__：
  - 檢查 `PG_DSN` 主機、埠、帳密、資料庫；確認 PostgreSQL 服務已啟動。
  - `app.py` 於啟動時會執行 `SELECT 1` 健康檢查並打印錯誤細節。
- __查無資料/空白畫面__：
  - 先跑 `python check_db.py` 檢查表與筆數。
  - 確認 `dmv_routes_2025` 欄位與型別符合需求（特別是中文欄位與 `route_type`）。
- __psycopg2 安裝問題__：
  - 將 pip 更新至最新，或改用 `psycopg2-binary`（本專案已使用）。

## 開發指引

- 後端：在 `app.py` 新增路由時，請使用 `sqlalchemy.text` 與參數綁定避免 SQL Injection。
- 前端：主要邏輯在 `static/script.js`。若要新增 UI 功能，請同步調整 `templates/index.html` 的元素 ID 與事件綁定。
- 若需要國際化或更多區域映射，請參考 `app.py` 中 `source_file` 與 `district` 轉換邏輯。

## 授權

本專案未設定授權，若需開源請補上 LICENSE。
