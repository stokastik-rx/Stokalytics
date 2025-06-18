const ctx = document.getElementById('profitChart').getContext('2d');

const profitChart = new Chart(ctx, {
  type: 'line',
  data: {
    datasets: [{
      label: '',
      data: chartData, // expects array of {x: cumulative_hours, y: cumulative_profit}
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
      legend: {
        display: false
      },
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
          label: function(context) {
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
        grid: {
          color: '#333'
        }
      },
      y: {
        ticks: {
          color: '#ffffff',
          font: {
            family: "'JetBrains Mono', monospace",
            size: 11
          },
          callback: function(value) {
            return `$${value.toLocaleString()}`;
          }
        },
        grid: {
          color: '#333'
        }
      }
    }
  }
});
