
const positionSpeaks = (function(){

  function getSpeaks(speaks_data) {

    const position = [];
    const speaks = [];
  
    for (const [key, value] of Object.entries(speaks_data)){
      position.push(key);
      speaks.push(value[2]);
    }
  
    return {"position": position, "speaks": speaks};
  }

  function getMinandMax(speaks) {

    const speaksNozero = [...speaks.speaks];

    for (var i = 0; i < speaksNozero.length; i++) {
      if (speaksNozero[i] === 0) {
        speaksNozero.splice(i, 1);
      }
    }

    const max = Math.max(...speaksNozero)
    const min = Math.min(...speaksNozero)

    const lowBound = Math.floor(min/5)*5
    const heighBound = Math.ceil(max/5)*5

    return {"max": heighBound, "min": lowBound};
  }

  function makeChart(convasName, dataSet) {

    const minAndmax = getMinandMax(dataSet);

    new Chart(convasName, {
      type: 'bar',
      data: {
        labels: dataSet.position,
        datasets: [{
          label: 'speaks',
          data: dataSet.speaks,
          borderWidth: 1
        }]
      },
      options: {
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,

            }
        },
        scales: {
          y: {
            min: minAndmax.min,
            max: minAndmax.max
          }
        }
      }
    });
  };

  const canvases = {
    'speaker_postion_chart': 'position_speak_avg',
    'position_grouped_chart': 'grouped_position_avg',
    'room_points_chart': 'room_points_avg',
    'partner_chart': 'partner_avg',
    'motion_chart': 'motion_avg',
  };

  function loopChats() {
    for (const [key, value] of Object.entries(canvases)){

      const chartData = JSON.parse(document.getElementById(value).textContent);
      const chartCanvas = document.getElementById(key);
      const plotData = getSpeaks(chartData);

      makeChart(chartCanvas, plotData);
    }
  }
  loopChats();

})();