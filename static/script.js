async function loadDashboard() {
    const gender = document.getElementById('gender').value;
    const disease = document.getElementById('disease').value;
    const region = document.getElementById('region').value;

    const response = await fetch(`/dashboard-data?gender=${gender}&disease=${disease}&region=${region}`);
    const data = await response.json();

    renderCharts(data);
}

function renderCharts(data) {
    const isDarkMode = document.body.getAttribute('data-theme') === 'dark';
    
    const darkLayoutUpdate = {
        paper_bgcolor: '#2d2d2d',
        plot_bgcolor: '#2d2d2d',
        font: { color: '#e0e0e0' },
        xaxis: { gridcolor: '#444', zerolinecolor: '#444' },
        yaxis: { gridcolor: '#444', zerolinecolor: '#444' }
    };

    const config = { 
        displayModeBar: true, 
        displaylogo: false, 
        locale: 'ko',
        modeBarButtonsToRemove: [
            'zoom2d', 'pan2d', 'select2d', 'lasso2d', 'autoScale2d',
            'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines'
        ]
    };

    const charts = [
        { id: 'age-chart', jsonData: data.age_chart },
        { id: 'disease-chart', jsonData: data.disease_chart },
        { id: 'region-chart', jsonData: data.region_chart }
    ];

    charts.forEach(cfg => {
        const fullData = JSON.parse(cfg.jsonData);
        
        // 원 그래프 추가 설정
        if (cfg.id === 'region-chart') {
            fullData.data[0].textinfo = 'percent+label';
            fullData.data[0].insidetextorientation = 'radial';
        }

        // 레이아웃 병합 (서버 설정을 유지하면서 다크모드 색상만 변경)
        if (isDarkMode) {
            fullData.layout = Object.assign({}, fullData.layout, darkLayoutUpdate);
        }

        Plotly.newPlot(cfg.id, fullData.data, fullData.layout, config);
    });
}

// 테마 토글 버튼 이벤트 리스너 복구
const toggleBtn = document.getElementById('theme-toggle');
if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
        const isDark = document.body.getAttribute('data-theme') === 'dark';
        if (isDark) {
            document.body.removeAttribute('data-theme');
            toggleBtn.textContent = '🌙 다크 모드';
        } else {
            document.body.setAttribute('data-theme', 'dark');
            toggleBtn.textContent = '☀️ 라이트 모드';
        }
        loadDashboard(); 
    });
}

window.onload = loadDashboard;