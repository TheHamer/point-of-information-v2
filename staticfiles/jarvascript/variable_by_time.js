/**
 * Variable by Time Charts Module
 * 
 * Handles scatter plot visualizations with trend lines and running averages.
 * Updated to support filter state integration.
 */

function togleGraph(barID, scatterID, dropDownID) {
  const bar = document.getElementById(barID);
  const scatter = document.getElementById(scatterID);
  const dropDown = document.getElementById(dropDownID);
  if (bar.style.display === "none") {
    bar.style.display = "block";
    scatter.style.display = "none";
    dropDown.style.display = "none";
  } else {
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
  'use strict';

  // Store references to charts for updates
  let mainChart = null;
  let positionChart = null;
  let positionGroupedChart = null;
  let roomPointsChart = null;
  let partnerChart = null;
  let motionTypeChart = null;

  /* data analysis functions */
  function dataBySelection(data, key, selected) {
    let selectionData = [];
    for (var i = 0; i < data.length; i++) {
      if (data[i]["date"] != null) {
        if (data[i][key] == selected) {
          selectionData.push({
            "x": data[i].date,
            "y": data[i].speaker_score
          });
        }
      }
    }
    return selectionData;
  }

  function groupedDataBySelection(data, selectedGroup) {
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

    return [
      ...dataBySelection(data, "speaker_position", groupedPositions[selectedGroup][0]),
      ...dataBySelection(data, "speaker_position", groupedPositions[selectedGroup][1])
    ];
  }

  function findMinAndMax(data) {
    let yMin = 100;
    let yMax = 50;

    if (data != null) {
      for (var i = 0; i < data.length; i++) {
        if (data[i].date) {
          const speak = data[i].speaker_score;
          if (speak < yMin) {
            yMin = speak;
          } else if (speak > yMax) {
            yMax = speak;
          }
        }
      }
    }
    return { "yMin": yMin, "yMax": yMax };
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
      sum_xx += point.x * point.x;
      sum_xy += point.x * point.y;
      count++;
    }

    if (count === 0 || (count * sum_xx - sum_x * sum_x) === 0) {
      return { "m": 0, "b": 0 };
    }

    const m = (count * sum_xy - sum_x * sum_y) / (count * sum_xx - sum_x * sum_x);
    const b = (sum_y / count) - (m * sum_x) / count;

    return { "m": m, "b": b };
  }

  /**
   * Calculate standard error and confidence intervals for linear regression
   * Returns error bars for points along the line from minX to maxX
   * Uses standard error of the regression line (confidence band), not prediction intervals
   */
  function calculateErrorBars(fitData, m, b, minX, maxX, numPoints = 50) {
    if (fitData.length < 2) {
      return [];
    }

    // Calculate residuals and standard error
    let sumSquaredResiduals = 0;
    
    for (const point of fitData) {
      const predicted = m * point.x + b;
      const residual = point.y - predicted;
      sumSquaredResiduals += residual * residual;
    }

    const stdError = Math.sqrt(sumSquaredResiduals / (fitData.length - 2));
    
    // Calculate mean of x values
    const meanX = fitData.reduce((sum, p) => sum + p.x, 0) / fitData.length;
    
    // Calculate sum of squared deviations from mean x
    const sumSquaredDevX = fitData.reduce((sum, p) => sum + Math.pow(p.x - meanX, 2), 0);
    
    // Calculate error bars at evenly spaced points along the line
    // Use standard error of the regression line (confidence band) - narrower than prediction intervals
    const errorBars = [];
    const multiplier = 1.96; // Use 1.96 standard error for tighter error bars
    const step = (maxX - minX) / (numPoints - 1);
    
    for (let i = 0; i < numPoints; i++) {
      const x = minX + i * step;
      const predicted = m * x + b;
      // Confidence band formula (without the +1 term that makes prediction intervals wider)
      const margin = multiplier * stdError * Math.sqrt(1 / fitData.length + Math.pow(x - meanX, 2) / sumSquaredDevX);
      
      errorBars.push({
        x: x,
        yUpper: predicted + margin,
        yLower: predicted - margin
      });
    }
    
    return errorBars;
  }

  function bestFit(speaksData, xAxisMin, xAxisMax) {
    if (!speaksData || speaksData.length === 0) {
      return { 
        line: { "low": [0, 0], "high": [0, 0] },
        errorBars: []
      };
    }

    // Convert dates to timestamps for calculation
    const speaksDataDate = speaksData.filter(
      point => point.x != null && point.y != null
    ).map(function(point) {
      const date = new Date(point.x);
      return {
        "x": date.getTime(),
        "y": point.y,
        "originalDate": date
      };
    });

    if (speaksDataDate.length === 0) {
      return { 
        line: { "low": [0, 0], "high": [0, 0] },
        errorBars: []
      };
    }

    // Find min and max dates from data for regression calculation
    let minDate = speaksDataDate[0].x;
    let maxDate = speaksDataDate[0].x;

    for (var i = 1; i < speaksDataDate.length; i++) {
      const point = speaksDataDate[i].x;
      if (point < minDate) {
        minDate = point;
      } else if (point > maxDate) {
        maxDate = point;
      }
    }

    // Use chart's x-axis range if provided, otherwise use data range
    const lineMinDate = xAxisMin ? new Date(xAxisMin).getTime() : minDate;
    const lineMaxDate = xAxisMax ? new Date(xAxisMax).getTime() : maxDate;

    // Normalize x values to start from 0 for regression calculation
    const normalizedData = speaksDataDate.map(point => ({
      x: point.x - minDate,
      y: point.y,
      originalDate: point.originalDate
    }));

    const fitVariables = leadSquares(normalizedData);

    // Calculate error bars along the line using the chart's x-axis range
    const normalizedLineMin = lineMinDate - minDate;
    const normalizedLineMax = lineMaxDate - minDate;
    const normalizedErrorBars = calculateErrorBars(
      normalizedData, 
      fitVariables.m, 
      fitVariables.b, 
      normalizedLineMin, 
      normalizedLineMax
    );

    // Convert error bars back to original date coordinates
    const errorBarData = normalizedErrorBars.map(bar => ({
      x: new Date(minDate + bar.x),
      yUpper: bar.yUpper,
      yLower: bar.yLower
    }));

    // Calculate line endpoints using chart's x-axis range
    const minY = fitVariables.m * normalizedLineMin + fitVariables.b;
    const maxY = fitVariables.m * normalizedLineMax + fitVariables.b;

    return {
      line: {
        "low": [new Date(lineMinDate), minY],
        "high": [new Date(lineMaxDate), maxY]
      },
      errorBars: errorBarData
    };
  }

  /**
   * Calculate running average for time series data
   * @param {Array} data - Array of {x: date, y: value} objects
   * @param {number} windowSize - Number of points for moving average
   * @returns {Array} Array of {x: date, y: avg} objects
   */
  function calculateRunningAverage(data, windowSize = 5) {
    if (!data || data.length === 0) return [];

    // Sort by date
    const sorted = [...data].sort((a, b) => new Date(a.x) - new Date(b.x));

    const result = [];
    for (let i = 0; i < sorted.length; i++) {
      const start = Math.max(0, i - windowSize + 1);
      const window = sorted.slice(start, i + 1);
      const sum = window.reduce((acc, point) => acc + point.y, 0);
      const avg = sum / window.length;

      result.push({
        x: sorted[i].x,
        y: Math.round(avg * 100) / 100
      });
    }

    return result;
  }

  function dateWithDate(data) {
    let chartDataDate = [];
    for (var i = 0; i < data.length; i++) {
      if (data[i].date != null) {
        chartDataDate.push(data[i]);
      }
    }
    return chartDataDate;
  }

  function checkDataExists(data) {
    let chartDataExsits = {
      "position": false,
      "roomPoints": false,
      "partner": false,
      "motionType": false
    };

    for (var i = 0; i < data.length; i++) {
      if (!chartDataExsits.position) {
        if (data[i].speaker_position != null) {
          chartDataExsits.position = true;
        }
      }
      if (!chartDataExsits.roomPoints) {
        if (data[i].room_points != null) {
          chartDataExsits.roomPoints = true;
        }
      }
      if (!chartDataExsits.partner) {
        if (data[i].partner != null) {
          chartDataExsits.partner = true;
        }
      }
      if (!chartDataExsits.motionType) {
        if (data[i].motion_type != null) {
          chartDataExsits.motionType = true;
        }
      }
    }
    return chartDataExsits;
  }

  /* graph plugins */
  const scatterArbitaryLineSmall = {
    id: 'scatterArbitaryLineSmall',
    beforeDatasetsDraw(chart, args, pluginOptions) {
      const { ctx, chartArea: { top, bottom, left, right, width, height },
        scales: { x, y } } = chart;
      ctx.save();

      const chartData = chart.data.datasets[0].data;

      if (!chartData || chartData.length === 0) {
        ctx.restore();
        return;
      }

      // Get the chart's x-axis range for proper alignment
      // Convert pixel positions at chart boundaries to values
      const xAxisMin = x.getValueForPixel(left);
      const xAxisMax = x.getValueForPixel(right);
      const bestFitResult = bestFit(chartData, xAxisMin, xAxisMax);

      // Draw error bars (upper bound) as dotted line
      if (bestFitResult.errorBars && bestFitResult.errorBars.length > 0) {
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(54, 162, 235, 0.5)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([5, 5]);

        for (let i = 0; i < bestFitResult.errorBars.length; i++) {
          const point = bestFitResult.errorBars[i];
          const px = x.getPixelForValue(point.x);
          const py = y.getPixelForValue(point.yUpper);

          if (i === 0) {
            ctx.moveTo(px, py);
          } else {
            ctx.lineTo(px, py);
          }
        }

        ctx.stroke();
        ctx.setLineDash([]);
        ctx.closePath();

        // Draw error bars (lower bound) as dotted line
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(54, 162, 235, 0.5)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([5, 5]);

        for (let i = 0; i < bestFitResult.errorBars.length; i++) {
          const point = bestFitResult.errorBars[i];
          const px = x.getPixelForValue(point.x);
          const py = y.getPixelForValue(point.yLower);

          if (i === 0) {
            ctx.moveTo(px, py);
          } else {
            ctx.lineTo(px, py);
          }
        }

        ctx.stroke();
        ctx.setLineDash([]);
        ctx.closePath();
      }

      // Draw best fit line
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(54, 162, 235, 1)';
      ctx.lineWidth = 2;
      ctx.moveTo(x.getPixelForValue(bestFitResult.line.low[0]), y.getPixelForValue(bestFitResult.line.low[1]));
      ctx.lineTo(x.getPixelForValue(bestFitResult.line.high[0]), y.getPixelForValue(bestFitResult.line.high[1]));
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

  // Get initial data
  const chartDataElement = document.getElementById("full_data_list");
  let chartData = chartDataElement ? JSON.parse(chartDataElement.textContent) : [];
  const yMaxAndMin = findMinAndMax(chartData);

  const chartOptions = {
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          title: function(context) {
            // Format title to show tournament and date
            const tournament = context[0].raw?.tournament ?? '';
            const date = new Date(context[0].parsed.x);
            const dateStr = date.toLocaleDateString('en-US', { 
              year: 'numeric', 
              month: 'short', 
              day: 'numeric' 
            });
            return tournament ? `${tournament} ${dateStr}` : dateStr;
          },
          label: function(context) {
            // Format label to show round, speaker position, and speaker score
            const round = context.raw?.round;
            const roundStr = round != null ? `R${round}` : 'N/A';
            const speakerPosition = context.raw?.speaker_position ?? 'N/A';
            const score = context.parsed.y;
            return `speaks: (${roundStr}, ${speakerPosition}, ${score})`;
          }
        }
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
        min: yMaxAndMin["yMin"] - 1,
        max: yMaxAndMin["yMax"] + 1
      },
    }
  };

  /* big chart */
  const speaksTimeElement = document.getElementById("speaks_vs_time");
  const chartDateData = speaksTimeElement ? JSON.parse(speaksTimeElement.textContent) : [];
  const bigChartCanvas = document.getElementById("speaks_vs_time_chart");

  if (bigChartCanvas) {
    mainChart = new Chart(bigChartCanvas, {
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
  }

  /* small charts */
  const chartDataExsits = checkDataExists(chartData);

  function changeContent(data, variable, dropDownElement, chart) {
    const newData = dataBySelection(data, variable, dropDownElement.value);
    chart.data.datasets[0].data = newData;
    chart.update();
  }

  function changeContentMultiSelect(data, variable, dropDownElement, chart) {
    const selectedOptions = Array.from(dropDownElement.selectedOptions);
    
    // Color palette for multiple partners
    const colors = [
      { border: 'rgba(54, 162, 235, 1)', background: 'rgba(54, 162, 235, 0.1)' },
      { border: 'rgba(255, 99, 132, 1)', background: 'rgba(255, 99, 132, 0.1)' },
      { border: 'rgba(75, 192, 192, 1)', background: 'rgba(75, 192, 192, 0.1)' },
      { border: 'rgba(255, 206, 86, 1)', background: 'rgba(255, 206, 86, 0.1)' },
      { border: 'rgba(153, 102, 255, 1)', background: 'rgba(153, 102, 255, 0.1)' },
      { border: 'rgba(255, 159, 64, 1)', background: 'rgba(255, 159, 64, 0.1)' },
      { border: 'rgba(199, 199, 199, 1)', background: 'rgba(199, 199, 199, 0.1)' },
      { border: 'rgba(83, 102, 255, 1)', background: 'rgba(83, 102, 255, 0.1)' }
    ];

    // Create datasets for each selected partner
    const datasets = selectedOptions.map((option, index) => {
      const partnerData = dataBySelection(data, variable, option.value);
      const colorIndex = index % colors.length;
      return {
        label: option.value,
        data: partnerData,
        borderColor: colors[colorIndex].border,
        backgroundColor: colors[colorIndex].background,
        borderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      };
    });

    // Update chart with new datasets
    chart.data.datasets = datasets;
    chart.update();
  }

  function changeContentGrouped(data, dropDownElement, chart) {
    const newData = groupedDataBySelection(data, dropDownElement.value);
    chart.data.datasets[0].data = newData;
    chart.update();
  }

  if (chartDataExsits.position) {
    const convasPosition = document.getElementById("speaker_postion_scatter");
    const convasPositionGrouped = document.getElementById("position_grouped_scatter");
    const positionDropdown = document.getElementById('position-dropdown');
    const positionDropdownGrouped = document.getElementById('position-grouped-dropdown');

    if (convasPosition && positionDropdown) {
      const getInitalPosition = positionDropdown.selectedOptions[0].value;
      const initialPositionData = dataBySelection(chartData, "speaker_position", getInitalPosition);

      positionChart = new Chart(convasPosition, {
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

      positionDropdown.addEventListener('change', () => {
        changeContent(chartData, "speaker_position", positionDropdown, positionChart);
      });
    }

    if (convasPositionGrouped && positionDropdownGrouped) {
      const getInitalPositionGrouped = positionDropdownGrouped.selectedOptions[0].value;
      const initialPositionGroupedData = groupedDataBySelection(chartData, getInitalPositionGrouped);

      positionGroupedChart = new Chart(convasPositionGrouped, {
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

      positionDropdownGrouped.addEventListener('change', () => {
        changeContentGrouped(chartData, positionDropdownGrouped, positionGroupedChart);
      });
    }
  }

  if (chartDataExsits.roomPoints) {
    const convasRoomPoints = document.getElementById("room_points_scatter");
    const roomPointsDropdown = document.getElementById('room-points-dropdown');

    if (convasRoomPoints && roomPointsDropdown) {
      const getInitalRoomPoints = roomPointsDropdown.selectedOptions[0].value;
      const initialRoomPointsData = dataBySelection(chartData, "room_points", getInitalRoomPoints);

      roomPointsChart = new Chart(convasRoomPoints, {
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

      roomPointsDropdown.addEventListener('change', () => {
        changeContent(chartData, "room_points", roomPointsDropdown, roomPointsChart);
      });
    }
  }

  if (chartDataExsits.partner) {
    const convasPartner = document.getElementById("partner_scatter");
    const partnerDropdown = document.getElementById('partner-dropdown');

    if (convasPartner && partnerDropdown) {
      // Color palette for multiple partners
      const colors = [
        { border: 'rgba(54, 162, 235, 1)', background: 'rgba(54, 162, 235, 0.1)' },
        { border: 'rgba(255, 99, 132, 1)', background: 'rgba(255, 99, 132, 0.1)' },
        { border: 'rgba(75, 192, 192, 1)', background: 'rgba(75, 192, 192, 0.1)' },
        { border: 'rgba(255, 206, 86, 1)', background: 'rgba(255, 206, 86, 0.1)' },
        { border: 'rgba(153, 102, 255, 1)', background: 'rgba(153, 102, 255, 0.1)' },
        { border: 'rgba(255, 159, 64, 1)', background: 'rgba(255, 159, 64, 0.1)' },
        { border: 'rgba(199, 199, 199, 1)', background: 'rgba(199, 199, 199, 0.1)' },
        { border: 'rgba(83, 102, 255, 1)', background: 'rgba(83, 102, 255, 0.1)' }
      ];

      // Ensure at least one option is selected initially
      if (partnerDropdown.selectedOptions.length === 0 && partnerDropdown.options.length > 0) {
        partnerDropdown.options[0].selected = true;
      }

      // Initialize with selected partners
      const initialSelected = Array.from(partnerDropdown.selectedOptions);
      
      const initialDatasets = initialSelected.map((option, index) => {
        const partnerData = dataBySelection(chartData, "partner", option.value);
        const colorIndex = index % colors.length;
        return {
          label: option.value,
          data: partnerData,
          borderColor: colors[colorIndex].border,
          backgroundColor: colors[colorIndex].background,
          borderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        };
      });

      partnerChart = new Chart(convasPartner, {
        type: 'scatter',
        data: {
          datasets: initialDatasets
        },
        plugins: [scatterArbitaryLineSmall],
        options: {
          ...chartOptions,
          plugins: {
            ...chartOptions.plugins,
            legend: {
              display: true,
              position: 'top'
            }
          }
        }
      });

      partnerDropdown.addEventListener('change', () => {
        changeContentMultiSelect(chartData, "partner", partnerDropdown, partnerChart);
      });
    }
  }

  if (chartDataExsits.motionType) {
    const convasMotionType = document.getElementById("motion_scatter");
    const motionTypeDropdown = document.getElementById('motion-type-dropdown');

    if (convasMotionType && motionTypeDropdown) {
      const getInitalMotionType = motionTypeDropdown.selectedOptions[0].value;
      const initialMotionTypeData = dataBySelection(chartData, "motion_type", getInitalMotionType);

      motionTypeChart = new Chart(convasMotionType, {
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

      motionTypeDropdown.addEventListener('change', () => {
        changeContent(chartData, "motion_type", motionTypeDropdown, motionTypeChart);
      });
    }
  }

  /**
   * Update all charts with filtered data
   * @param {Array} filteredData - The filtered dataset
   */
  function updateWithFilteredData(filteredData) {
    // Update the internal data reference
    chartData = filteredData;

    // Prepare Speaks over time data
    const speaksVsTime = filteredData
      .filter(entry => entry.date && entry.speaker_score)
      .map(entry => ({
        x: entry.date,
        y: entry.speaker_score,
        round: entry.round,
        speaker_position: entry.speaker_position,
        tournament: entry.tournament
      }));

    // Update main chart
    if (mainChart) {
      mainChart.data.datasets[0].data = speaksVsTime;
      mainChart.update();
    }

    // Update position charts
    if (positionChart) {
      const dropdown = document.getElementById('position-dropdown');
      if (dropdown) {
        changeContent(filteredData, "speaker_position", dropdown, positionChart);
      }
    }

    if (positionGroupedChart) {
      const dropdown = document.getElementById('position-grouped-dropdown');
      if (dropdown) {
        changeContentGrouped(filteredData, dropdown, positionGroupedChart);
      }
    }

    // Update room points chart
    if (roomPointsChart) {
      const dropdown = document.getElementById('room-points-dropdown');
      if (dropdown) {
        changeContent(filteredData, "room_points", dropdown, roomPointsChart);
      }
    }

    // Update partner chart
    if (partnerChart) {
      const dropdown = document.getElementById('partner-dropdown');
      if (dropdown) {
        changeContent(filteredData, "partner", dropdown, partnerChart);
      }
    }

    // Update motion type chart
    if (motionTypeChart) {
      const dropdown = document.getElementById('motion-type-dropdown');
      if (dropdown) {
        changeContent(filteredData, "motion_type", dropdown, motionTypeChart);
      }
    }
  }

  // Register with FilterState if available
  if (typeof FilterState !== 'undefined') {
    FilterState.onFilterChange(updateWithFilteredData);
  }

  // Expose update function globally
  return {
    updateWithFilteredData
  };
}();
