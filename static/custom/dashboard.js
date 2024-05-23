/* globals Chart:false */
let myChart = null

document.addEventListener('DOMContentLoaded', function() {
  Chart.register({
    id: 'afterDrawLabelEmptyCustom',
    afterDraw: function(chart) {
      if (chart.data.datasets.length === 0) {
        // No data is present
        console.log(chart)
        let ctx = chart.ctx;
        let width = chart.width;
        let height = chart.height
        chart.clear();
        
        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = '24px sans-serif';
        ctx.fillText('No data to display', width / 2, height / 2);
        ctx.restore();
      }
    }
  });
  let chartColor = document.documentElement.getAttribute('data-bs-theme') == 'dark' ? '#ccc' : '#333'
  Chart.defaults.color = chartColor;

  const ctx = document.getElementById('myChart')
  myChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [
      ],
      datasets: [
        
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: false
        },
        title: {
          display: true,
          text: (ctx) => {
            console.log(ctx.chart, 'ctx.chart')
            return 'Quota Usage (MB)'
          },
        },

        // datalabel plugin
        datalabels: {
          display: true,
          align: 'center',
          anchor: 'end',
          formatter: function(value, context) {
            return Math.round(value/1000000) + 'MB';
          }
        }
      },

      scales: {
        y: {
          // grid: {
          //   color: chartColor
          // },
          ticks: {
            color: chartColor
          }
        },
        x: {
          // grid: {
          //   color: chartColor
          // },
          ticks: {
            color: chartColor
          }
        },
      }

    },
    plugins: [ChartDataLabels]
  })

});
const downloadPng = () => {
  console.log(myChart, 'myChart')
  const dataimg = myChart.toBase64Image('image/png', 1)
  console.log(dataimg)
  let a = document.createElement('a');
  a.href = dataimg;
  a.download = "output.png";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
const downloadCsv = (idtable) => {
  let table = document.getElementById(idtable);
  let headers = table.querySelectorAll("thead th");
  let rows = table.rows;
  let csvContent = "";

  // kasih header dulu
  // for (let i = 0; i < headers.length; i++) {
  //     csvContent += headers[i].textContent + (i !== headers.length - 1 ? "," : "");
  // }
  // csvContent += "\n";

  // tambahin data
  for (let i = 0; i < rows.length; i++) {
      let cells = rows[i].cells;
      for (let j = 0; j < cells.length; j++) {
          csvContent += cells[j].textContent + (j !== cells.length - 1 ? "," : "");
      }
      csvContent += "\n";
  }

  // download
  let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  let link = document.createElement("a");
  let url = URL.createObjectURL(blob);
  let filename = 'export_' + idtable + '_' + new Date().toISOString() + '.csv';
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function formatTime(milliseconds) {
  let seconds = Math.floor(milliseconds / 1000);
  let minutes = Math.floor(seconds / 60);
  let hours = Math.floor(minutes / 60);

  seconds = seconds % 60;
  minutes = minutes % 60;

  let timeString = '';
  if (hours > 0) {
      timeString += `${hours}h `;
  }
  if (minutes > 0) {
      timeString += `${minutes}m `;
  }
  timeString += `${seconds}s`;

  return timeString;
}
const buildChart = async (btn) => {
  console.log(btn)
  let prevBtnTxt = `${btn.innerHTML}`
  btn.innerHTML = 'Build Chart Loading...'
  btn.disabled = true;
  
  document.getElementById('tableDetail').style.display = 'none'

  let startTime = Date.now();
  function updateLoadingMessage() {
    let elapsedTime = Date.now() - startTime;
    let loadingTime = formatTime(elapsedTime);
    btn.innerHTML = `Build Chart Loading... ${loadingTime}`;
}

// Update loading message every second
let loadingInterval = setInterval(updateLoadingMessage, 1000);

  const [data1, data2] = await getData()
  let chartUsage1 = {
      label: 'Usage 1',
      data: data1.graph_month,
      borderColor: 'rgb(54, 162, 235)',
      backgroundColor: 'transparent',
      pointStyle: 'circle',
      pointRadius: 5,
      pointHoverRadius: 10
    }
  let chartUsage2 = {
      label: 'Usage 2',
      data: data2.graph_month,
      borderColor: 'rgb(255, 159, 64)',
      backgroundColor: 'transparent',
      pointStyle: 'circle',
      pointRadius: 5,
      pointHoverRadius: 10
    }
    
    myChart.data.labels.length = 0; 
    myChart.data.datasets.length = 0;
    myChart.data.labels.push(...data1.graph_month_label);
    myChart.data.datasets.push(...[chartUsage1, chartUsage2])
    myChart.update()

    
    clearInterval(loadingInterval);
    btn.innerHTML = prevBtnTxt
    btn.disabled = false;
    
    document.getElementById('tableDetail').style.display = ''
    buildTable(data1, data2)
    
}

const buildTable = async (data1, data2) => {
  const tableMonth = document.getElementById('tableMonth')
  const tableDay = document.getElementById('tableDay')

  const tbodyMonth = tableMonth.querySelector('tbody')
  let htmlMonth = data1.graph_month_label.map((label, index) => {
    let value1 = data1.graph_month[index]
    let value2 = data2.graph_month[index]
    return `<tr>
      <td class="fw-bold">${label}</td>
      <td>${value1}</td>
      <td>${value2}</td>
      <td>${Math.round(value1/1000000)} MB</td>
      <td>${Math.round(value2/1000000)} MB</td>
    </tr>`
  }).join('')

  tbodyMonth.innerHTML = htmlMonth

  const tbodyDay = tableDay.querySelector('tbody')
  let htmlDay = data1.graph_day_label.map((label, index) => {
    let value1 = data1.graph_day[index]
    let value2 = data2.graph_day[index]
    return `<tr>
      <td class="fw-bold">${label}</td>
      <td>${value1}</td>
      <td>${value2}</td>
      <td>${Math.round(value1/1000000)} MB</td>
      <td>${Math.round(value2/1000000)} MB</td>
    </tr>`
  }).join('')

  tbodyDay.innerHTML = htmlDay
}

const getData = async () => {
  const url = 'http://localhost:3007/api/arima/predict';

  
  const fetchUsage1 = fetch(url, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      "start_tarik_data": "2023-07-01",
      "end_tarik_data": "2023-12-15",

      "start_train_data": "2023-07-01",
      "end_train_data": "2023-12-15",

      "start_date": "2023-12-16",
      "end_date": "2024-02-29",
      "device_id": "1ee01383af6c0308c68d371b81349fd",
      "sensor_key": "usage1"
    })
  }).then(response => {
    if (!response.ok) {
      throw new Error(`Error fetching ${url}: ${response.statusText}`);
    }
    return response.json();
  });

  const fetchUsage2 = fetch(url, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      "start_tarik_data": "2023-07-01",
      "end_tarik_data": "2023-12-15",

      "start_train_data": "2023-07-01",
      "end_train_data": "2023-12-15",

      "start_date": "2023-12-16",
      "end_date": "2024-02-29",
      "device_id": "1ee01383af6c0308c68d371b81349fd",
      "sensor_key": "usage2"
    })
  }).then(response => {
    if (!response.ok) {
      throw new Error(`Error fetching ${url}: ${response.statusText}`);
    }
    return response.json();
  });

  // Use Promise.all to handle both fetch promises
  const [data1, data2] = await Promise.all([fetchUsage1, fetchUsage2])

  return [data1, data2]


    
}


// darkmode handling chart
document.querySelector('button[data-bs-theme-value="light"]').addEventListener('click', () => {
  Chart.defaults.color = '#333'; // Set default text color
  Chart.defaults.borderColor = '#333'; // Set default border color

  // Update the existing chart instance with the new color settings
  // myChart.options.scales.x.grid.color = '#333'; // X-axis label color
  // myChart.options.scales.y.grid.color = '#333'; // Y-axis label color
  myChart.options.scales.x.ticks.color = '#333'; // X-axis label color
  myChart.options.scales.y.ticks.color = '#333'; // Y-axis label color

  myChart.update();
});

document.querySelector('button[data-bs-theme-value="dark"]').addEventListener('click', () => {
  Chart.defaults.color = '#ccc'; // Set default text color
  Chart.defaults.borderColor = '#ccc'; // Set default border color

  // Update the existing chart instance with the new color settings
  // myChart.options.scales.x.grid.color = '#ccc'; // X-axis label color
  // myChart.options.scales.y.grid.color = '#ccc'; // Y-axis label color
  myChart.options.scales.x.ticks.color = '#ccc'; // X-axis label color
  myChart.options.scales.y.ticks.color = '#ccc'; // Y-axis label color

  myChart.update();
});
