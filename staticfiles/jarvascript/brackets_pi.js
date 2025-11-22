
const speackerBrakets = function() {
  const chartData = JSON.parse(document.getElementById("full_data_list").textContent);
  const convasSpeaksBraket = document.getElementById("position-pi");

  function getSpeakerBracket(speaksData) {

    let _95to100 = 0; 
    let _92to94 = 0;
    let _89to91 = 0;
    let _86to88 = 0;
    let _83to85 = 0;
    let _79to82 = 0;
    let _76to78 = 0;
    let _73to75 = 0;
    let _70to72 = 0;
    let _67to69 = 0;
    let _64to66 = 0;
    let _61to63 = 0;
    let _58to60 = 0;
    let _55to57 = 0;
    let _50to54 = 0;

    for (let i = 1; i<speaksData.length; i++) {

      const speaks = speaksData[i]["speaker_score"];

      if (speaks >= 95) {
        _95to100 += 1;
      }else if(speaks >= 92) {
        _92to94 += 1;
      }else if(speaks >= 89) {
        _89to91 += 1;
      }else if(speaks >= 86) {
        _86to88 += 1;
      }else if(speaks >= 83) {
        _83to85 += 1;
      }else if(speaks >= 79) {
        _79to82 += 1;
      }else if(speaks >= 76) {
        _76to78 += 1;
      }else if(speaks >= 73) {
        _73to75 += 1;
      }else if(speaks >= 70) {
        _70to72 += 1;
      }else if(speaks >= 67) {
        _67to69 += 1;
      }else if(speaks >= 92) {
        _64to66 += 1;
      }else if(speaks >= 61) {
        _61to63 += 1;
      }else if(speaks >= 58) {
        _58to60 += 1;
      }else if(speaks >= 55) {
        _55to57 += 1;
      }else if(speaks >= 50) {
        _50to54 += 1;
      }
    }

    const breakets = {
      "95 to 100": _95to100,
      "92 to 94": _92to94,
      "89 to 91": _89to91,
      "86 to 88": _86to88,
      "83 to 85": _83to85,
      "79 to 82": _79to82,
      "76 to 78": _76to78,
      "73 to 75": _73to75,
      "70 to 72": _70to72,
      "67 to 69": _67to69,
      "64 to 66": _64to66,
      "61 to 63": _61to63,
      "58 to 60": _58to60,
      "55 to 57": _55to57,
      "50 to 54": _50to54,
    }

    const finalData = []
    const finalLabels = []

    for (const key in breakets) {
      value = breakets[key]
      if (value != 0) {
        finalData.push(value)
        finalLabels.push(key)
      }
    }

    return {
      "data": finalData,
      "labels": finalLabels
    }
  }

  const dataAndLabels = getSpeakerBracket(chartData);

  Chart.register({
    id: 'noData',
    afterDraw: function(chart) {
        if (chart.data.datasets[0].data.every(item => item === 0)) {
            let ctx = chart.ctx;
            let width = chart.width;
            let height = chart.height;

            chart.clear();
            ctx.save();
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.font = "20px 'Helvetica Neue', Helvetica, Arial, sans-serif";
            ctx.fillStyle = "#8E8E90";
            ctx.fillText('No data to display', width / 2, height / 2);
            ctx.restore();
        }
    }
});

const chartOptions = {
  maintainAspectRatio: false,
  plugins: {
      legend: {
          position: 'bottom',
          display: true,
      }
  },
}
  
const smallScatterPosition = new Chart(convasSpeaksBraket, {
    type: 'doughnut',
    data: {
      labels: dataAndLabels.labels,
      datasets: [{
        data: dataAndLabels.data,
        borderWidth: 1
      }]
    },
    options: chartOptions
  });

}()