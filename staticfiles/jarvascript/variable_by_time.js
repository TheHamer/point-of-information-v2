
function togleGraph(barID, scatterID, dropDownID) {
    const bar = document.getElementById(barID);
    const scatter = document.getElementById(scatterID);
    const dropDown = document.getElementById(dropDownID);
    if (bar.style.display === "none") {
        bar.style.display = "block";
        scatter.style.display = "none";
        dropDown.style.display = "none";
    }else{
        bar.style.display = "none";
        scatter.style.display = "block";
        dropDown.style.display = "inline";
    }
  }
  
function showNoData(scatterID, noDataID) {
    const scatter = document.getElementById(scatterID);
    const noData = document.getElementById(noDataID);
  
}
  
const smallSpeaksGraph = function() {
  
  /* data analysis functions */
  function dataBySelection(key, selected) {
    let selectionData = []
    for (var i = 1; i<chartData.length; i++) {
      if (chartData[i]["date"] != null) {
        if (chartData[i][key] == selected) {
          selectionData.push({
                "x": chartData[i].date,
                "y": chartData[i].speaker_score
            })
        }
      }
    }
    return selectionData
  }
  
  function groupedDataBySelection(selectedGroup) {
  
    const groupedPositions = {
      "PM and LO": ["PM", "LO"],
      "Deputy": ["DPM", "DLO"],
      "Extension": ["MG", "MO"],
      "Whip": ["GW", "OW"],
      "OG": ["PM", "DPM"],
      "OO": ["LO", "DLO"],
      "CG": ["MG", "GW"],
      "CO": ["MO", "OW"]
    };

    return [...dataBySelection("speaker_position", groupedPositions[selectedGroup][0]),
    ...dataBySelection("speaker_position", groupedPositions[selectedGroup][1])
    ];
  }
  
  function findMinAndMax(data) {
    let yMin = 100;
    let yMax = 50;
  
    if (data != null){
      for (i=0; i<data.length; i++) {
        if (data[i].date) {
            speak = data[i].speaker_score;
            if (speak < yMin) {
            yMin = speak;
            }else if (speak > yMax) {
            yMax = speak;
            }
          }
      }
    }
    return {"yMin": yMin, "yMax": yMax};
  }
  
  function leadSquares(fitData) {
    let sum_x = 0;
    let sum_y = 0;
    let sum_xx = 0;
    let sum_xy = 0;
    let count = 0;

    for (var point of fitData) {
      sum_x += point.x;
      sum_y += point.y;
      sum_xx += point.x*point.x;
      sum_xy += point.x*point.y;
      count++;
    }

    const m = (count*sum_xy - sum_x*sum_y) / (count*sum_xx - sum_x*sum_x);
    const b = (sum_y/count) - (m*sum_x)/count;

    return {"m": m, "b": b};
  }
    
  function bestFit(speaksData) {
    const speaksDataDate = speaksData.filter(
      point => point.x != null
    ).map(function(point) {
        return {
        "x": (new Date(point.x)).getTime()/100000000000,
        "y": point.y}
      });

    let lowDate = speaksDataDate[0].x;
    let heighDate = speaksDataDate[0].x;
    
    for (i=1; i<speaksDataDate.length; i++) {
      const point = speaksDataDate[i].x;
      if (point < lowDate) {
        lowDate = point;
      }else if (point > heighDate) {
        heighDate = point;
      }
    }

    for (let date of speaksDataDate) {
      date.x = date.x - lowDate;
    }
    
    const fitVariables = leadSquares(speaksDataDate);
    
    const lowSpeak = fitVariables.b;
    const heighSpeak = fitVariables.m*(heighDate - lowDate) + fitVariables.b;
    
    return {"low": [new Date(lowDate*100000000000), lowSpeak], "heigh": [new Date(heighDate*100000000000), heighSpeak]};
  }

  function dateWithDate(data) {
      let chartDataDate = []
      for (i=0; i<data.length; i++) {
          if (data[i].date != null) {
              chartDataDate.push(chartData[i])
          }
      }
      return chartDataDate
  }

  function checkDataExists(data) {
      let chartDataExsits = {
          "position": false,
          "roomPoints": false,
          "partner": false,
          "motionType": false
      }
  
      for (i=0; i<chartData.length; i++) {
          if (!chartDataExsits.position){
              if (chartData[i].speaker_position != null) {
                  chartDataExsits.position = true
              }
          }
          if (!chartDataExsits.roomPoints){
              if (chartData[i].room_points != null) {
                  chartDataExsits.roomPoints = true
              }
          }
          if (!chartDataExsits.partner){
              if (chartData[i].partner != null) {
                  chartDataExsits.partner = true
              }
          }
          if (!chartDataExsits.motionType){
              if (chartData[i].motion_type != null) {
                  chartDataExsits.motionType = true
              }
          }
      }
      return  chartDataExsits
  }

  /* graph functions */
  const scatterArbitaryLineSmall = {
    id: 'scatterArbitaryLineSmall',
    beforeDatasetsDraw(chart, args, pluginOptions){
      const {ctx, chartArea: {top, bottom, left, right, width, height},
        scales: {x, y}} = chart;
      ctx.save();

      const chartData = chart.data.datasets[0].data

      const bestFitLine = (chartData.length > 0) ? bestFit(chartData) : {"low": [0, 0], "heigh": [0, 0]};

      ctx.beginPath();
      ctx.strokeStyle = 'rgba(255, 26, 104, 1)';
      ctx.lineWidth = 2;
      ctx.moveTo(x.getPixelForValue(bestFitLine.low[0]), y.getPixelForValue(bestFitLine.low[1]));
      ctx.lineTo(x.getPixelForValue(bestFitLine.heigh[0]), y.getPixelForValue(bestFitLine.heigh[1]));
      ctx.stroke();
      ctx.closePath();
      ctx.restore();
    }
  };
  
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

  const chartData = JSON.parse(document.getElementById("full_data_list").textContent);
  const yMaxAndMin = findMinAndMax(chartData);

  const chartOptions = {
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: false,
        }
  },
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'day',
          unitStepSize: 1,
          displayFormats: {
              'day': 'MMM yyyy'
          }
        }
      },
      y: {
        min: yMaxAndMin["yMin"]-1,
        max: yMaxAndMin["yMax"]+1
      },
    }
  };

  /* big chart */
  const chartDateData = JSON.parse(document.getElementById("speaks_vs_time").textContent);
  const bigChartCanvas = document.getElementById("speaks_vs_time_chart");

  const speaksVsTime = new Chart(bigChartCanvas, {
    type: 'scatter',
    data: {
      datasets: [{
        label: "speaks",
        data: chartDateData,
        borderWidth: 1
      }]
    },
    plugins: [scatterArbitaryLineSmall],
    options: chartOptions
  });

  /* small charts*/
  const chartDataExsits = checkDataExists(chartData);

  function changeContent(variable, dropDownElement, chart) {
      const newData = dataBySelection(variable, dropDownElement.value);
      chart.data.datasets[0].data = newData;
      chart.update();
    }
  
  function changeContentGrouped(dropDownElement, chart) {
    const newData = groupedDataBySelection(dropDownElement.value);
    chart.data.datasets[0].data = newData;
    chart.update();
  }

  if (chartDataExsits.position) {

    const convasPosition = document.getElementById("speaker_postion_scatter");
    const convasPositionGrouped = document.getElementById("position_grouped_scatter");
    const getInitalPosition = document.getElementById('position-dropdown').selectedOptions[0].value;
    const getInitalPositionGrouped = document.getElementById('position-grouped-dropdown').selectedOptions[0].value;
    const initialPositionData = dataBySelection("speaker_position", getInitalPosition);
    const initialPositionGroupedData = groupedDataBySelection(getInitalPositionGrouped);

    const smallScatterPosition = new Chart(convasPosition, {
        type: 'scatter',
        data: {
          datasets: [{
            label: "speaks",
            data: initialPositionData,
            borderWidth: 1
          }]
        },
        plugins: [scatterArbitaryLineSmall],
        options: chartOptions
    });
      
      const smallScatterPositionGrouped = new Chart(convasPositionGrouped, {
          type: 'scatter',
          data: {
            datasets: [{
              label: "speaks",
              data: initialPositionGroupedData,
              borderWidth: 1
            }]
          },
          plugins: [scatterArbitaryLineSmall],
          options: chartOptions
      });

      const positonDropdown = document.getElementById('position-dropdown');
      const positonDropdownGrouped = document.getElementById('position-grouped-dropdown');

      positonDropdown.addEventListener('change', () => {
          changeContent("speaker_position", positonDropdown, smallScatterPosition)
      });
      positonDropdownGrouped.addEventListener('change', () => {
          changeContentGrouped(positonDropdownGrouped, smallScatterPositionGrouped)
      });

  }

  if (chartDataExsits.roomPoints) {
      const convasRoomPoints = document.getElementById("room_points_scatter");
      const getInitalRoomPoints = document.getElementById('room-points-dropdown').selectedOptions[0].value;
      const initialRoomPointsData = dataBySelection("room_points", getInitalRoomPoints);

      const smallScatterRoomPoints = new Chart(convasRoomPoints, {
          type: 'scatter',
          data: {
            datasets: [{
              label: "speaks",
              data: initialRoomPointsData,
              borderWidth: 1
            }]
          },
          plugins: [scatterArbitaryLineSmall],
          options: chartOptions
      });

      const roomPointsDropdown = document.getElementById('room-points-dropdown');

      roomPointsDropdown.addEventListener('change', () => {
          changeContent("room_points", roomPointsDropdown, smallScatterRoomPoints)
        });
  }

  if (chartDataExsits.partner) {
      const convasPartner = document.getElementById("partner_scatter");
      const getInitalPartner = document.getElementById('partner-dropdown').selectedOptions[0].value;
      const initialPartnerData = dataBySelection("partner", getInitalPartner);

      const smallScatterPartner = new Chart(convasPartner, {
          type: 'scatter',
          data: {
            datasets: [{
              label: "speaks",
              data: initialPartnerData,
              borderWidth: 1
            }]
          },
          plugins: [scatterArbitaryLineSmall],
          options: chartOptions
      });

      const partnerDropdown = document.getElementById('partner-dropdown');
      partnerDropdown.addEventListener('change', () => {
          changeContent("partner", partnerDropdown, smallScatterPartner)
      });
  }

  if (chartDataExsits.motionType) {
      const convasMotionType = document.getElementById("motion_scatter");
      const getInitalMotionType = document.getElementById('motion-type-dropdown').selectedOptions[0].value;
      const initialMotionTypeData = dataBySelection("motion_type", getInitalMotionType);

      const smallScatterMotionType = new Chart(convasMotionType, {
          type: 'scatter',
          data: {
            datasets: [{
              label: "speaks",
              data: initialMotionTypeData,
              borderWidth: 1
            }]
          },
          plugins: [scatterArbitaryLineSmall],
          options: chartOptions
        });

      const motionTypeDropdown = document.getElementById('motion-type-dropdown');
  
      motionTypeDropdown.addEventListener('change', () => {
          changeContent("motion_type", motionTypeDropdown, smallScatterMotionType)
      });  
  }
}()