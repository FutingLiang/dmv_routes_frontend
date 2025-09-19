// 全域變數
let currentPage = 1;
let totalPages = 1;
let currentData = [];
let allData = [];

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM載入完成，開始初始化...');
    loadRouteData();
    loadDetailedStatistics();
    loadSampleTable();
    setupEventListeners();
});

// 匯出：調查範圍(標的)
function exportDetailedExcel() {
    window.location.href = '/export/detailed-statistics.xlsx';
}

// 匯出：24/25 樣本表
function exportSampleExcel() {
    window.location.href = '/export/sample-table.xlsx';
}

// 設定事件監聽器
function setupEventListeners() {
    document.getElementById('search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchRoutes();
        }
    });
    
    document.getElementById('district-filter').addEventListener('change', searchRoutes);
    document.getElementById('route-type-filter').addEventListener('change', searchRoutes);
}

// 載入路線資料
async function loadRouteData() {
    try {
        console.log('開始載入資料...');
        const response = await fetch('/api/routes');
        console.log('API回應狀態:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP錯誤: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('收到資料筆數:', data.routes ? data.routes.length : 0);
        
        if (!data.success) {
            throw new Error(data.error || '後端回傳錯誤');
        }
        
        allData = data.routes;
        currentData = allData;
        
        updateStatistics(data.statistics);
        displayRoutes(currentData);
        
    } catch (error) {
        console.error('載入資料錯誤:', error);
        showError(`無法載入路線資料: ${error.message}`);
    }
}

// 更新統計資訊
function updateStatistics(stats) {
    document.getElementById('total-routes').textContent = stats.total || 0;
    document.getElementById('local-routes').textContent = stats.local_routes || 0;
    document.getElementById('hwy-routes').textContent = stats.hwy_routes || 0;
    document.getElementById('districts').textContent = stats.districts || 0;
}

// 搜尋路線
function searchRoutes() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const districtFilter = document.getElementById('district-filter').value;
    const routeTypeFilter = document.getElementById('route-type-filter').value;
    
    currentData = allData.filter(route => {
        const matchesSearch = !searchTerm || 
            (route.路線名稱 && route.路線名稱.toLowerCase().includes(searchTerm)) ||
            (route.路線編號 && route.路線編號.toLowerCase().includes(searchTerm)) ||
            (route.公司名稱 && route.公司名稱.toLowerCase().includes(searchTerm));
            
        const matchesDistrict = !districtFilter || route.district === districtFilter;
        const matchesRouteType = !routeTypeFilter || route.route_type === routeTypeFilter;
        
        return matchesSearch && matchesDistrict && matchesRouteType;
    });
    
    currentPage = 1;
    displayRoutes(currentData);
}

// 顯示路線資料
function displayRoutes(data, page = 1) {
    const itemsPerPage = 20;
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageData = data.slice(startIndex, endIndex);
    
    const tbody = document.getElementById('routes-table-body');
    
    if (pageData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center text-muted">
                    <i class="fas fa-search me-2"></i>找不到符合條件的路線資料
                </td>
            </tr>
        `;
        updatePagination(0, page, itemsPerPage);
        return;
    }
    
    try {
        tbody.innerHTML = pageData.map(route => {
            // 安全地取得欄位值
            const companyName = route['公司名稱'] || route.company_name || '-';
            const routeNumber = route['路線編號'] || route.route_number || '-';
            const routeName = route['路線名稱'] || route.route_name || '-';
            const distanceGo = route['里程往'] || route.distance_go;
            const distanceReturn = route['里程返'] || route.distance_return;
            const frequency = route['班次一'] || route.frequency_1 || '-';
            const vehicles = route['車輛數'] || route.vehicles || '-';
            const stopsGo = route['站牌數往'] || route.stops_go || '-';
            
            return `
                <tr>
                    <td><span class="badge bg-secondary">${getDistrictName(route.district)}</span></td>
                    <td><span class="badge ${route.route_type === 'hwy_routes' ? 'bg-warning' : 'bg-success'}">${getRouteTypeName(route.route_type)}</span></td>
                    <td>${companyName}</td>
                    <td><strong>${routeNumber}</strong></td>
                    <td>${routeName}</td>
                    <td>${distanceGo ? distanceGo.toFixed(1) + ' km' : '-'}</td>
                    <td>${distanceReturn ? distanceReturn.toFixed(1) + ' km' : '-'}</td>
                    <td>${frequency}</td>
                    <td>${vehicles}</td>
                    <td>${stopsGo}</td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('顯示資料時發生錯誤:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>顯示資料時發生錯誤: ${error.message}
                </td>
            </tr>
        `;
    }
    
    updatePagination(data.length, page, itemsPerPage);
}

// 更新分頁
function updatePagination(totalItems, currentPage, itemsPerPage) {
    totalPages = Math.ceil(totalItems / itemsPerPage);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // 上一頁
    paginationHTML += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">上一頁</a>
        </li>
    `;
    
    // 頁碼
    for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
        paginationHTML += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>
        `;
    }
    
    // 下一頁
    paginationHTML += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">下一頁</a>
        </li>
    `;
    
    pagination.innerHTML = paginationHTML;
}

// 切換頁面
function changePage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    displayRoutes(currentData, page);
}

// 載入詳細統計資料
async function loadDetailedStatistics() {
    try {
        console.log('載入詳細統計資料...');
        const response = await fetch('/api/detailed-statistics');
        
        if (!response.ok) {
            throw new Error(`HTTP錯誤: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || '載入詳細統計失敗');
        }
        
        updateDetailedStatisticsTable(data.detailed_statistics, data.district_totals);
        
    } catch (error) {
        console.error('載入詳細統計失敗:', error);
        document.getElementById('detailed-stats-body').innerHTML = 
            '<tr><td colspan="5" class="text-center text-danger">載入統計資料失敗</td></tr>';
    }
}

// 更新詳細統計表格
function updateDetailedStatisticsTable(detailedStats, districtTotals) {
    const tbody = document.getElementById('detailed-stats-body');
    let html = '';
    
    // 按監理所順序排列
    const districtOrder = ['臺北區監理所', '臺北市區監理所', '新竹區監理所', '台中區監理所', '嘉義區監理所', '高雄區監理所'];
    
    for (const district of districtOrder) {
        if (!detailedStats[district]) continue;
        
        const companies = detailedStats[district];
        const companyNames = Object.keys(companies).sort();
        
        // 監理所標題行
        if (companyNames.length > 0) {
            html += `
                <tr class="table-secondary">
                    <td rowspan="${companyNames.length + 1}" class="align-middle fw-bold">${district}</td>
                </tr>
            `;
            
            // 各客運公司資料
            companyNames.forEach((company, idx) => {
                const data = companies[company];
                const rowClass = idx === 0 ? 'district-separator' : '';
                html += `
                    <tr class="${rowClass}">
                        <td>${company}</td>
                        <td class="text-center">${data.hwy_routes || 0}</td>
                        <td class="text-center">${data.hwy_routes || 0}</td>
                        <td class="text-center">${data.local_routes || 0}</td>
                        <td class="text-center">${data.local_routes || 0}</td>
                    </tr>
                `;
            });
        }
    }
    
    // 總計行
    let totalHwyRoutes = 0;
    let totalLocalRoutes = 0;
    let totalRoutes = 0;
    
    Object.values(districtTotals).forEach(total => {
        totalHwyRoutes += total.hwy_routes;
        totalLocalRoutes += total.local_routes;
        totalRoutes += total.total;
    });
    
    html += `
        <tr class="table-dark fw-bold">
            <td>總計</td>
            <td></td>
            <td class="text-center">${totalHwyRoutes}</td>
            <td class="text-center">${totalHwyRoutes}</td>
            <td class="text-center">${totalLocalRoutes}</td>
            <td class="text-center">${totalLocalRoutes}</td>
        </tr>
    `;
    
    tbody.innerHTML = html;
    
    // 更新摘要資訊
    const totalOperators = Object.values(detailedStats).reduce((sum, district) => sum + Object.keys(district).length, 0);
    document.getElementById('summary-operators').textContent = totalOperators;
    document.getElementById('summary-routes').textContent = totalRoutes;
}

// 取得區域中文名稱
function getDistrictName(district) {
    const names = {
        'taipei_district': '臺北區',
        'taipei_city': '臺北市區',
        'hsinchu': '新竹',
        'taichung': '台中', 
        'chiayi': '嘉義',
        'kaohsiung': '高雄'
    };
    return names[district] || district;
}

function getRouteTypeName(routeType) {
    const names = {
        'local_routes': '一般公路',
        'hwy_routes': '國道客運'
    };
    return names[routeType] || routeType;
}

function showError(message) {
    const tbody = document.getElementById('routes-table-body');
    tbody.innerHTML = `
        <tr>
            <td colspan="10" class="text-center text-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>${message}
            </td>
        </tr>
    `;
}

// 24/25 樣本表：載入
async function loadSampleTable() {
    try {
        const res = await fetch('/api/sample-table');
        if (!res.ok) throw new Error(`HTTP錯誤: ${res.status}`);
        const data = await res.json();
        if (!data.success) throw new Error(data.error || '載入樣本表失敗');
        renderSampleTable(data);
    } catch (e) {
        console.error(e);
        const tbody = document.getElementById('sample-table-body');
        if (tbody) tbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger">載入樣本表失敗</td></tr>';
    }
}

// 24/25 樣本表：渲染
function renderSampleTable(payload) {
    const tbody = document.getElementById('sample-table-body');
    if (!tbody) return;

    const byDistrict = payload.by_district || {};
    const districtTotals = payload.district_totals || {};
    const grand = payload.grand_totals || {};

    const districtOrder = ['臺北區監理所', '臺北市區監理所', '新竹區監理所', '台中區監理所', '嘉義區監理所', '高雄區監理所'];

    let html = '';

    for (const dist of districtOrder) {
        if (!byDistrict[dist]) continue;
        const companies = Object.keys(byDistrict[dist]).sort();
        if (companies.length === 0) continue;

        // 區塊起始（用第一列加上 rowSpan）
        const rowSpan = companies.length + 1; // +1 for subtotal row
        let firstRow = true;
        for (const company of companies) {
            const rec = byDistrict[dist][company] || {};
            const hwy = rec.hwy || { a: 0, b: 0, samples: 0 };
            const local = rec.local || { c: 0, d: 0, samples: 0 };
            const totalSamples = (hwy.samples || 0) + (local.samples || 0);

            html += '<tr>';
            if (firstRow) {
                html += `<td rowspan="${rowSpan}" class="fw-bold align-top">${dist}</td>`;
                firstRow = false;
            }
            html += `
                <td>${company}</td>
                <td class="text-center">${hwy.a || 0}</td>
                <td class="text-center">${hwy.b || 0}</td>
                <td class="text-center">${hwy.samples || 0}</td>
                <td class="text-center">${local.c || 0}</td>
                <td class="text-center">${local.d || 0}</td>
                <td class="text-center">${local.samples || 0}</td>
                <td class="text-center">${totalSamples}</td>
            </tr>`;
        }

        // 小計
        const dt = districtTotals[dist] || { hwy: {}, local: {}, samples_total: 0 };
        html += `
            <tr class="table-secondary fw-bold">
                <td>小計</td>
                <td class="text-center">${(dt.hwy && dt.hwy.a) || 0}</td>
                <td class="text-center">${(dt.hwy && dt.hwy.b) || 0}</td>
                <td class="text-center">${(dt.hwy && dt.hwy.samples) || 0}</td>
                <td class="text-center">${(dt.local && dt.local.c) || 0}</td>
                <td class="text-center">${(dt.local && dt.local.d) || 0}</td>
                <td class="text-center">${(dt.local && dt.local.samples) || 0}</td>
                <td class="text-center">${dt.samples_total || 0}</td>
            </tr>`;
    }

    // 總計
    html += `
        <tr class="table-dark fw-bold">
            <td colspan="2">總計</td>
            <td class="text-center">${(grand.hwy && grand.hwy.a) || 0}</td>
            <td class="text-center">${(grand.hwy && grand.hwy.b) || 0}</td>
            <td class="text-center">${(grand.hwy && grand.hwy.samples) || 0}</td>
            <td class="text-center">${(grand.local && grand.local.c) || 0}</td>
            <td class="text-center">${(grand.local && grand.local.d) || 0}</td>
            <td class="text-center">${(grand.local && grand.local.samples) || 0}</td>
            <td class="text-center">${grand.samples_total || 0}</td>
        </tr>`;

    tbody.innerHTML = html || '<tr><td colspan="8" class="text-center text-muted">無資料</td></tr>';
}
