/**
 * Raspilapse Interactive Charts
 * Chart.js-based data visualization with theme support
 */

// Global state
const ChartsApp = {
    charts: {},
    currentRange: '24h',
    autoRefreshInterval: null,
    isLoading: false
};

// Chart colors that work with both themes
const CHART_COLORS = {
    light: {
        lux: '#f59e0b',
        brightness_mean: '#3b82f6',
        brightness_p5: 'rgba(59, 130, 246, 0.2)',
        brightness_p95: 'rgba(59, 130, 246, 0.2)',
        exposure: '#22c55e',
        gain: '#ef4444',
        temperature: '#ef4444',
        humidity: '#3b82f6',
        wind: '#22c55e',
        cpu_temp: '#f97316',
        load: '#a855f7',
        grid: '#e5e7eb',
        text: '#374151'
    },
    dark: {
        lux: '#fbbf24',
        brightness_mean: '#60a5fa',
        brightness_p5: 'rgba(96, 165, 250, 0.2)',
        brightness_p95: 'rgba(96, 165, 250, 0.2)',
        exposure: '#4ade80',
        gain: '#f87171',
        temperature: '#f87171',
        humidity: '#60a5fa',
        wind: '#4ade80',
        cpu_temp: '#fb923c',
        load: '#c084fc',
        grid: '#374151',
        text: '#9ca3af'
    }
};

/**
 * Get current theme colors
 */
function getThemeColors() {
    const isDark = document.documentElement.classList.contains('dark-theme');
    return isDark ? CHART_COLORS.dark : CHART_COLORS.light;
}

/**
 * Get common chart options
 */
function getCommonOptions(title) {
    const colors = getThemeColors();
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 300
        },
        interaction: {
            mode: 'index',
            intersect: false
        },
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    color: colors.text,
                    usePointStyle: true,
                    padding: 15,
                    font: { size: 11 }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: '#fff',
                bodyColor: '#fff',
                padding: 10,
                displayColors: true,
                callbacks: {
                    title: function(items) {
                        if (items.length > 0) {
                            const date = new Date(items[0].parsed.x);
                            return date.toLocaleString();
                        }
                        return '';
                    }
                }
            }
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    displayFormats: {
                        hour: 'HH:mm',
                        day: 'MMM d',
                        week: 'MMM d'
                    }
                },
                grid: {
                    color: colors.grid,
                    drawBorder: false
                },
                ticks: {
                    color: colors.text,
                    maxTicksLimit: 8
                }
            },
            y: {
                grid: {
                    color: colors.grid,
                    drawBorder: false
                },
                ticks: {
                    color: colors.text
                }
            }
        }
    };
}

/**
 * Calculate time range from preset
 */
function getTimeRange(preset) {
    const now = new Date();
    let start;

    switch (preset) {
        case '1h':
            start = new Date(now - 60 * 60 * 1000);
            break;
        case '6h':
            start = new Date(now - 6 * 60 * 60 * 1000);
            break;
        case '12h':
            start = new Date(now - 12 * 60 * 60 * 1000);
            break;
        case '24h':
            start = new Date(now - 24 * 60 * 60 * 1000);
            break;
        case '7d':
            start = new Date(now - 7 * 24 * 60 * 60 * 1000);
            break;
        case '30d':
            start = new Date(now - 30 * 24 * 60 * 60 * 1000);
            break;
        default:
            start = new Date(now - 24 * 60 * 60 * 1000);
    }

    return {
        start: start.toISOString(),
        end: now.toISOString()
    };
}

/**
 * Fetch chart data from API
 */
async function fetchChartData(metrics, start, end) {
    const params = new URLSearchParams({
        metrics: metrics.join(','),
        start: start,
        end: end,
        downsample: '500'
    });

    const response = await fetch(`/charts/api/data?${params}`);
    if (!response.ok) {
        throw new Error('Failed to fetch data');
    }
    return response.json();
}

/**
 * Convert API data to Chart.js format
 */
function formatChartData(apiData, metric) {
    if (!apiData.timestamps || !apiData.data || !apiData.data[metric]) {
        return [];
    }

    return apiData.timestamps.map((ts, i) => ({
        x: new Date(ts),
        y: apiData.data[metric][i]
    })).filter(point => point.y !== null);
}

/**
 * Show/hide loading indicator
 */
function setLoading(chartId, loading) {
    const loader = document.getElementById(`${chartId}Loading`);
    if (loader) {
        loader.style.display = loading ? 'block' : 'none';
    }
}

/**
 * Create Light Levels chart
 */
async function createLightChart(start, end) {
    const ctx = document.getElementById('lightChart');
    if (!ctx) return;

    setLoading('light', true);
    const colors = getThemeColors();

    try {
        const data = await fetchChartData(['lux', 'sun_elevation'], start, end);

        if (ChartsApp.charts.light) {
            ChartsApp.charts.light.destroy();
        }

        const options = getCommonOptions('Light Levels');
        options.scales.y.type = 'logarithmic';
        options.scales.y.min = 0.01;
        options.scales.y.title = { display: true, text: 'Lux', color: colors.text };

        ChartsApp.charts.light = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Lux',
                    data: formatChartData(data, 'lux'),
                    borderColor: colors.lux,
                    backgroundColor: colors.lux + '33',
                    borderWidth: 2,
                    fill: true,
                    pointRadius: 0,
                    tension: 0.1
                }]
            },
            options: options
        });

        updatePointInfo(data);
    } catch (error) {
        console.error('Error creating light chart:', error);
    } finally {
        setLoading('light', false);
    }
}

/**
 * Create Brightness chart with P5-P95 band
 */
async function createBrightnessChart(start, end) {
    const ctx = document.getElementById('brightnessChart');
    if (!ctx) return;

    setLoading('brightness', true);
    const colors = getThemeColors();

    try {
        const data = await fetchChartData(['brightness_mean', 'brightness_p5', 'brightness_p95'], start, end);

        if (ChartsApp.charts.brightness) {
            ChartsApp.charts.brightness.destroy();
        }

        const options = getCommonOptions('Brightness');
        options.scales.y.min = 0;
        options.scales.y.max = 255;
        options.scales.y.title = { display: true, text: 'Brightness', color: colors.text };

        ChartsApp.charts.brightness = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'P95',
                        data: formatChartData(data, 'brightness_p95'),
                        borderColor: 'transparent',
                        backgroundColor: colors.brightness_p95,
                        fill: '+1',
                        pointRadius: 0,
                        order: 2
                    },
                    {
                        label: 'P5',
                        data: formatChartData(data, 'brightness_p5'),
                        borderColor: 'transparent',
                        backgroundColor: colors.brightness_p5,
                        fill: false,
                        pointRadius: 0,
                        order: 3
                    },
                    {
                        label: 'Mean',
                        data: formatChartData(data, 'brightness_mean'),
                        borderColor: colors.brightness_mean,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0,
                        tension: 0.1,
                        order: 1
                    }
                ]
            },
            options: options
        });
    } catch (error) {
        console.error('Error creating brightness chart:', error);
    } finally {
        setLoading('brightness', false);
    }
}

/**
 * Create Exposure & Gain chart with dual axis
 */
async function createExposureChart(start, end) {
    const ctx = document.getElementById('exposureChart');
    if (!ctx) return;

    setLoading('exposure', true);
    const colors = getThemeColors();

    try {
        const data = await fetchChartData(['exposure_time_us', 'analogue_gain'], start, end);

        if (ChartsApp.charts.exposure) {
            ChartsApp.charts.exposure.destroy();
        }

        const options = getCommonOptions('Exposure & Gain');
        options.scales.y.type = 'logarithmic';
        options.scales.y.position = 'left';
        options.scales.y.title = { display: true, text: 'Exposure (us)', color: colors.text };
        options.scales.y1 = {
            type: 'linear',
            position: 'right',
            title: { display: true, text: 'Gain', color: colors.text },
            grid: { drawOnChartArea: false },
            ticks: { color: colors.text }
        };

        ChartsApp.charts.exposure = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Exposure',
                        data: formatChartData(data, 'exposure_time_us'),
                        borderColor: colors.exposure,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0,
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Gain',
                        data: formatChartData(data, 'analogue_gain'),
                        borderColor: colors.gain,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0,
                        tension: 0.1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: options
        });
    } catch (error) {
        console.error('Error creating exposure chart:', error);
    } finally {
        setLoading('exposure', false);
    }
}

/**
 * Create Weather chart with multi-axis
 */
async function createWeatherChart(start, end) {
    const ctx = document.getElementById('weatherChart');
    if (!ctx) return;

    setLoading('weather', true);
    const colors = getThemeColors();

    try {
        const data = await fetchChartData(['weather_temperature', 'weather_humidity', 'weather_wind_speed'], start, end);

        if (ChartsApp.charts.weather) {
            ChartsApp.charts.weather.destroy();
        }

        const options = getCommonOptions('Weather');
        options.scales.y.position = 'left';
        options.scales.y.title = { display: true, text: 'Temp (C)', color: colors.text };
        options.scales.y1 = {
            type: 'linear',
            position: 'right',
            title: { display: true, text: 'Humidity (%) / Wind (m/s)', color: colors.text },
            grid: { drawOnChartArea: false },
            ticks: { color: colors.text },
            min: 0
        };

        ChartsApp.charts.weather = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Temperature',
                        data: formatChartData(data, 'weather_temperature'),
                        borderColor: colors.temperature,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0,
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Humidity',
                        data: formatChartData(data, 'weather_humidity'),
                        borderColor: colors.humidity,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0,
                        tension: 0.1,
                        yAxisID: 'y1'
                    },
                    {
                        label: 'Wind Speed',
                        data: formatChartData(data, 'weather_wind_speed'),
                        borderColor: colors.wind,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0,
                        tension: 0.1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: options
        });
    } catch (error) {
        console.error('Error creating weather chart:', error);
    } finally {
        setLoading('weather', false);
    }
}

/**
 * Create System Metrics chart
 */
async function createSystemChart(start, end) {
    const ctx = document.getElementById('systemChart');
    if (!ctx) return;

    setLoading('system', true);
    const colors = getThemeColors();

    try {
        const data = await fetchChartData(['system_cpu_temp', 'system_load_1min'], start, end);

        if (ChartsApp.charts.system) {
            ChartsApp.charts.system.destroy();
        }

        const options = getCommonOptions('System Metrics');
        options.scales.y.position = 'left';
        options.scales.y.title = { display: true, text: 'CPU Temp (C)', color: colors.text };
        options.scales.y1 = {
            type: 'linear',
            position: 'right',
            title: { display: true, text: 'Load', color: colors.text },
            grid: { drawOnChartArea: false },
            ticks: { color: colors.text },
            min: 0
        };

        ChartsApp.charts.system = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'CPU Temp',
                        data: formatChartData(data, 'system_cpu_temp'),
                        borderColor: colors.cpu_temp,
                        backgroundColor: colors.cpu_temp + '33',
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0,
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Load (1min)',
                        data: formatChartData(data, 'system_load_1min'),
                        borderColor: colors.load,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0,
                        tension: 0.1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: options
        });
    } catch (error) {
        console.error('Error creating system chart:', error);
    } finally {
        setLoading('system', false);
    }
}

/**
 * Update point info display
 */
function updatePointInfo(data) {
    const infoEl = document.getElementById('pointInfo');
    if (infoEl && data) {
        infoEl.textContent = `Showing ${data.point_count || 0} points (downsampled from ${data.original_count || 0})`;
    }
}

/**
 * Update all charts
 */
async function updateAllCharts() {
    if (ChartsApp.isLoading) return;
    ChartsApp.isLoading = true;

    const range = getTimeRange(ChartsApp.currentRange);

    // Check for custom range
    const startInput = document.getElementById('startDate');
    const endInput = document.getElementById('endDate');

    let start = range.start;
    let end = range.end;

    if (startInput?.value && endInput?.value) {
        start = new Date(startInput.value).toISOString();
        end = new Date(endInput.value).toISOString();
    }

    try {
        await Promise.all([
            createLightChart(start, end),
            createBrightnessChart(start, end),
            createExposureChart(start, end),
            createWeatherChart(start, end),
            createSystemChart(start, end)
        ]);
    } catch (error) {
        console.error('Error updating charts:', error);
    } finally {
        ChartsApp.isLoading = false;
    }
}

/**
 * Export chart as PNG
 */
function exportChartAsPNG(chartId, filename) {
    const chart = ChartsApp.charts[chartId];
    if (!chart) return;

    const link = document.createElement('a');
    link.download = filename || `${chartId}_chart.png`;
    link.href = chart.toBase64Image();
    link.click();
}

/**
 * Handle preset button clicks
 */
function handlePresetClick(event) {
    const btn = event.target;
    if (!btn.classList.contains('preset-btn') || btn.id === 'applyRange') return;

    // Update active state
    document.querySelectorAll('.preset-btn[data-range]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Clear custom inputs
    const startInput = document.getElementById('startDate');
    const endInput = document.getElementById('endDate');
    if (startInput) startInput.value = '';
    if (endInput) endInput.value = '';

    // Update range and refresh
    ChartsApp.currentRange = btn.dataset.range;
    updateAllCharts();
}

/**
 * Handle custom range apply
 */
function handleApplyRange() {
    const startInput = document.getElementById('startDate');
    const endInput = document.getElementById('endDate');

    if (startInput?.value && endInput?.value) {
        // Clear preset active state
        document.querySelectorAll('.preset-btn[data-range]').forEach(b => b.classList.remove('active'));
        updateAllCharts();
    }
}

/**
 * Handle auto-refresh toggle
 */
function handleAutoRefresh(event) {
    if (event.target.checked) {
        ChartsApp.autoRefreshInterval = setInterval(updateAllCharts, 60000);
    } else {
        clearInterval(ChartsApp.autoRefreshInterval);
        ChartsApp.autoRefreshInterval = null;
    }
}

/**
 * Update charts when theme changes
 */
function handleThemeChange() {
    const colors = getThemeColors();

    Object.values(ChartsApp.charts).forEach(chart => {
        if (!chart) return;

        // Update scale colors
        if (chart.options.scales) {
            Object.values(chart.options.scales).forEach(scale => {
                if (scale.grid) scale.grid.color = colors.grid;
                if (scale.ticks) scale.ticks.color = colors.text;
                if (scale.title) scale.title.color = colors.text;
            });
        }

        // Update legend colors
        if (chart.options.plugins?.legend?.labels) {
            chart.options.plugins.legend.labels.color = colors.text;
        }

        chart.update('none');
    });
}

/**
 * Initialize charts
 */
function initializeCharts() {
    // Set up event listeners
    document.querySelectorAll('.preset-btn[data-range]').forEach(btn => {
        btn.addEventListener('click', handlePresetClick);
    });

    document.getElementById('applyRange')?.addEventListener('click', handleApplyRange);
    document.getElementById('autoRefresh')?.addEventListener('change', handleAutoRefresh);

    // Listen for theme changes
    const themeToggle = document.getElementById('themeToggle');
    const mobileThemeToggle = document.getElementById('mobileThemeToggle');
    themeToggle?.addEventListener('click', () => setTimeout(handleThemeChange, 200));
    mobileThemeToggle?.addEventListener('click', () => setTimeout(handleThemeChange, 200));

    // Set default date inputs
    const now = new Date();
    const yesterday = new Date(now - 24 * 60 * 60 * 1000);

    const startInput = document.getElementById('startDate');
    const endInput = document.getElementById('endDate');

    if (startInput) {
        startInput.value = yesterday.toISOString().slice(0, 16);
    }
    if (endInput) {
        endInput.value = now.toISOString().slice(0, 16);
    }

    // Load saved settings from localStorage
    const savedRange = localStorage.getItem('chartsRange');
    if (savedRange) {
        ChartsApp.currentRange = savedRange;
        document.querySelectorAll('.preset-btn[data-range]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.range === savedRange);
        });
    }

    // Save range on change
    document.querySelectorAll('.preset-btn[data-range]').forEach(btn => {
        btn.addEventListener('click', () => {
            localStorage.setItem('chartsRange', btn.dataset.range);
        });
    });

    // Initial load
    updateAllCharts();
}

// Export functions for use in templates
window.ChartsApp = ChartsApp;
window.exportChartAsPNG = exportChartAsPNG;
window.updateAllCharts = updateAllCharts;
window.initializeCharts = initializeCharts;
