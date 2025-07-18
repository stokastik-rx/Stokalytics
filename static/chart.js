document.addEventListener('DOMContentLoaded', function () {
  // === High-DPI Display Support ===
  // Set device pixel ratio for crisp rendering on high-DPI displays
  Chart.defaults.responsive = true;
  Chart.defaults.maintainAspectRatio = false;
  Chart.defaults.devicePixelRatio = window.devicePixelRatio || 1;

  // === Venture Color Map ===
  const ventureColors = {
    Blackjack: '#00ffff',
    'Match Play': '#ffcc00',
    Poker: '#ff66cc'
  };

  const durationVentures = ['Blackjack', 'Poker'];

  // === Chart 1: Cumulative Profit (PnL) ===
  const dashboardCanvas = document.getElementById('profitChart');
  if (dashboardCanvas && typeof chartData !== 'undefined') {
    const ctx = dashboardCanvas.getContext('2d');
    // Calculate min/max for x
    const xVals = chartData.map(d => d.x);
    const xMin = Math.min(...xVals);
    const xMax = Math.max(...xVals);

    new Chart(ctx, {
      type: 'line',
      data: {
        datasets: [{
          label: '',
          data: chartData && chartData.length > 0 ? chartData : [{ x: 0, y: 0 }],
          parsing: false,
          borderColor: '#00ff99',
          backgroundColor: '#00ff9966',
          tension: 0.3,
          fill: false,
          pointRadius: 3
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            titleFont: {
              family: '"JetBrains Mono", monospace',
              size: 12,
              weight: '600'
            },
            bodyFont: {
              family: '"JetBrains Mono", monospace',
              size: 12,
              weight: '400'
            },
            callbacks: {
              label: function (context) {
                return `$${context.parsed.y.toLocaleString()}`;
              }
            }
          }
        },
        scales: {
          x: {
            type: 'linear',
            min: xMin,
            max: xMax,
            title: {
              display: true,
              text: 'Hours',
              color: '#aaa',
              font: { family: '"JetBrains Mono", monospace', size: 11 }
            },
            ticks: {
              color: '#ffffff',
              font: {
                family: '"JetBrains Mono", monospace',
                size: 11
              }
            },
            grid: { color: '#333' }
          },
          y: {
            ticks: {
              color: '#ffffff',
              font: {
                family: '"JetBrains Mono", monospace',
                size: 11
              },
              callback: function (value) {
                return `$${value.toLocaleString()}`;
              }
            },
            grid: { color: '#333' }
          }
        }
      }
    });
  }

  // === Chart 2: Total Bankroll by Date ===
  const combinedCanvas = document.getElementById('combinedBankrollChart');
  if (combinedCanvas && typeof combinedBankrollData !== 'undefined') {
    const ctx = combinedCanvas.getContext('2d');
    let chartData = [];
    if (combinedBankrollData && combinedBankrollData.length > 0) {
      chartData = [{ x: combinedBankrollData[0].x, y: 0 }, ...combinedBankrollData];
    } else {
      chartData = [{ x: new Date().toISOString().split('T')[0], y: 0 }];
    }
    // Calculate min/max for x (dates)
    const xVals = chartData.map(d => new Date(d.x).getTime());
    const xMin = Math.min(...xVals);
    const xMax = Math.max(...xVals);

    new Chart(ctx, {
      type: 'line',
      data: {
        datasets: [{
          label: 'Total Bankroll',
          data: chartData,
          borderColor: '#66ccff',
          backgroundColor: '#66ccff66',
          tension: 0.3,
          fill: false,
          pointRadius: 3
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (context) {
                return `$${context.parsed.y.toLocaleString()}`;
              }
            }
          }
        },
        scales: {
          x: {
            type: 'time',
            min: new Date(xMin),
            max: new Date(xMax),
            time: { unit: 'day' },
            ticks: {
              color: '#ffffff',
              font: { family: '"JetBrains Mono", monospace', size: 11 }
            },
            grid: { color: '#333' }
          },
          y: {
            beginAtZero: true,
            ticks: {
              color: '#ffffff',
              font: { family: '"JetBrains Mono", monospace', size: 11 },
              callback: function (value) {
                return `$${value.toLocaleString()}`;
              }
            },
            grid: { color: '#333' }
          }
        }
      }
    });
  }

  // === Chart 3: Per-Venture PnL Charts ===
  const ventureContainer = document.getElementById('ventureCharts');

  if (ventureContainer && typeof ventureChartData !== 'undefined') {
    Object.entries(ventureChartData).forEach(([venture, data]) => {
      const color = ventureColors[venture] || '#00ffcc';
      const isDuration = durationVentures.includes(venture);

      const wrapper = document.createElement('div');
      wrapper.classList.add('chart', 'chart-narrow');

      const labelHtml =
        venture === 'Blackjack'
          ? `<a href="/blackjack" style="text-decoration:none; color:${color}; border-color:${color};"><div class="chart-label" style="border-color: ${color}; color: ${color}; cursor:pointer;">Blackjack</div></a>`
          : `<div class="chart-label" style="border-color: ${color}; color: ${color};">${venture}</div>`;

      wrapper.innerHTML = `
        ${labelHtml}
        <canvas></canvas>
      `;

      const canvas = wrapper.querySelector('canvas');
      ventureContainer.appendChild(wrapper);

      // Safe handling of venture chart data
      let chartData = [];
      if (data && data.length > 0) {
        const first = data[0];
        // Inject origin if not Match Play
        if (venture !== 'Match Play') {
          chartData = [{ x: isDuration ? 0 : first.x, y: 0 }, ...data];
        } else {
          chartData = data;
        }
      } else {
        // Default data for empty charts
        chartData = [{ x: isDuration ? 0 : new Date().toISOString().split('T')[0], y: 0 }];
      }
      // Calculate min/max for x
      const xVals = isDuration
        ? chartData.map(d => d.x)
        : chartData.map(d => new Date(d.x).getTime());
      const xMin = Math.min(...xVals);
      const xMax = Math.max(...xVals);

      new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
          datasets: [{
            label: '',
            data: chartData,
            borderColor: color,
            backgroundColor: color + '66',
            tension: 0.3,
            fill: false,
            pointRadius: 3
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: function (context) {
                  return `$${context.parsed.y.toLocaleString()}`;
                }
              },
              titleFont: {
                family: '"JetBrains Mono", monospace',
                size: 12,
                weight: '600'
              },
              bodyFont: {
                family: '"JetBrains Mono", monospace',
                size: 12
              }
            }
          },
          scales: {
            x: isDuration ? {
              type: 'linear',
              min: xMin,
              max: xMax,
              title: {
                display: true,
                text: 'Hours',
                color: '#aaa',
                font: { family: '"JetBrains Mono", monospace', size: 11 }
              },
              ticks: {
                color: '#ffffff',
                font: { family: '"JetBrains Mono", monospace', size: 11 }
              },
              grid: { color: '#333' }
            } : {
              type: 'time',
              min: new Date(xMin),
              max: new Date(xMax),
              time: { unit: 'day' },
              title: {
                display: true,
                text: 'Date',
                color: '#aaa',
                font: { family: '"JetBrains Mono", monospace', size: 11 }
              },
              ticks: {
                color: '#ffffff',
                font: { family: '"JetBrains Mono", monospace', size: 11 }
              },
              grid: { color: '#333' }
            },
            y: {
              ticks: {
                color: '#ffffff',
                font: { family: '"JetBrains Mono", monospace', size: 11 },
                callback: function (value) {
                  return `$${value.toLocaleString()}`;
                }
              },
              grid: { color: '#333' }
            }
          }
        }
      });
    });
  }
});

// --- Tips Included in PnL Slider Toggle Functionality ---
document.addEventListener('DOMContentLoaded', function() {
  const tipsToggle = document.getElementById('tips-toggle');
  if (tipsToggle) {
    tipsToggle.addEventListener('change', function() {
      const url = new URL(window.location.href);
      if (this.checked) {
        url.searchParams.set('tips_included', '1');
      } else {
        url.searchParams.set('tips_included', '0');
      }
      window.location.href = url.toString();
    });
  }
});