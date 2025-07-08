document.addEventListener('DOMContentLoaded', function () {
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

    new Chart(ctx, {
      type: 'line',
      data: {
        datasets: [{
          label: '',
          data: [{ x: 0, y: 0 }, ...chartData],

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
    new Chart(ctx, {
      type: 'line',
      data: {
        datasets: [{
          label: 'Total Bankroll',
          data: [{ x: combinedBankrollData[0].x, y: 0 }, ...combinedBankrollData],
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

      wrapper.innerHTML = `
        <div class="chart-label" style="border-color: ${color}; color: ${color};">
          ${venture}
        </div>
        <canvas></canvas>
      `;

      const canvas = wrapper.querySelector('canvas');
      ventureContainer.appendChild(wrapper);

      new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
          datasets: [{
            label: '',
            data: (() => {
  if (!data.length) return [];
  const first = data[0];

  // Inject origin if not Match Play
  if (venture !== 'Match Play') {
    return [{ x: isDuration ? 0 : first.x, y: 0 }, ...data];
  }

  return data;
})(),


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