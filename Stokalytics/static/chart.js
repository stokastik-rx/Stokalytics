document.addEventListener('DOMContentLoaded', function () {
  // === Dashboard Chart ===
  const dashboardCanvas = document.getElementById('profitChart');
  if (dashboardCanvas && typeof chartData !== 'undefined') {
    const ctx = dashboardCanvas.getContext('2d');

    new Chart(ctx, {
      type: 'line',
      data: {
        datasets: [{
          label: '',
          data: chartData,
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
              family: "'JetBrains Mono', monospace",
              size: 12,
              weight: '600'
            },
            bodyFont: {
              family: "'JetBrains Mono', monospace",
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
            ticks: {
              color: '#ffffff',
              font: {
                family: "'JetBrains Mono', monospace",
                size: 11
              }
            },
            grid: { color: '#333' }
          },
          y: {
            ticks: {
              color: '#ffffff',
              font: {
                family: "'JetBrains Mono', monospace",
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


});


const combinedCanvas = document.getElementById('combinedBankrollChart');
if (combinedCanvas && typeof combinedBankrollData !== 'undefined') {
  const ctx = combinedCanvas.getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [{
        label: 'Total Bankroll',
        data: combinedBankrollData,
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
            font: { family: "'JetBrains Mono', monospace", size: 11 }
          },
          grid: { color: '#333' }
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: '#ffffff',
            font: { family: "'JetBrains Mono', monospace", size: 11 },
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








