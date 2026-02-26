/**
 * Speaker Score Charts Module
 * 
 * Handles bar chart visualizations for speaker analysis data.
 * Updated to support average points chart with y-axis toggle.
 */

const positionSpeaks = (function(){
  'use strict';

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
    // Filter out zeros properly (avoiding splice bug during iteration)
    const speaksNozero = speaks.speaks.filter(val => val !== 0);

    // If all values are zero or array is empty, return default range
    if (speaksNozero.length === 0) {
      return {"max": 85, "min": 0};
    }

    const max = Math.max(...speaksNozero);
    const min = Math.min(...speaksNozero);

    const lowBound = Math.floor(min/5)*5;
    const heighBound = Math.ceil(max/5)*5;

    return {"max": heighBound, "min": lowBound};
  }

  function makeChart(convasName, dataSet) {
    const minAndmax = getMinandMax(dataSet);

    return new Chart(convasName, {
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
  }

  const canvases = {
    'speaker_postion_chart': 'position_speak_avg',
    'position_grouped_chart': 'grouped_position_avg',
    'room_points_chart': 'room_points_avg',
    'partner_chart': 'partner_avg',
    'motion_chart': 'motion_avg',
  };

  // Store chart instances for updates
  const chartInstances = {};

  function loopChats() {
    for (const [key, value] of Object.entries(canvases)){
      const dataElement = document.getElementById(value);
      const chartCanvas = document.getElementById(key);
      
      if (!dataElement || !chartCanvas) continue;
      
      const chartData = JSON.parse(dataElement.textContent);
      const plotData = getSpeaks(chartData);

      chartInstances[key] = makeChart(chartCanvas, plotData);
    }
  }
  
  // Initialize charts on page load
  loopChats();
  
  // Public API for chart updates
  return {
    instances: chartInstances,
    updateChart: function(chartKey, newData) {
      if (chartInstances[chartKey]) {
        chartInstances[chartKey].data.labels = newData.position;
        chartInstances[chartKey].data.datasets[0].data = newData.speaks;
        chartInstances[chartKey].update();
      }
    }
  };
})();


/**
 * Average Points Chart Module
 * 
 * Handles the new average points visualization with toggleable y-axis.
 */
const AveragePointsChart = (function() {
  'use strict';
  
  let chart = null;
  let currentYAxis = 'speaker_score'; // 'speaker_score' or 'team_points'
  let speakerData = null;
  let teamPointsData = null;
  let bestFitLine = null;
  
  /**
   * Calculate average points data from full dataset
   * Returns individual data points (no bucketing/averaging)
   */
  function calculateAveragePointsData(data) {
    // Check if data is already processed (has x, y properties)
    if (data.length > 0 && data[0].hasOwnProperty('x') && data[0].hasOwnProperty('y')) {
      // Data is already processed, use as-is
      speakerData = data.filter(d => d.y !== undefined && d.y !== null);
      // For team points, we need to get it from the backend
      teamPointsData = [];
      return { speakerData, teamPointsData };
    }
    
    // Calculate individual points from raw data
    speakerData = [];
    teamPointsData = [];
    
    data.forEach(entry => {
      // Calculate Speaks by average points of room (matches Python model: average_points_so_far)
      // Formula: room_points / (round - 1) for round > 1
      // Returns 1.5 for round 1 or if round/room_points is None
      const round = entry.round;
      const roomPoints = entry.room_points;
      
      let avgPoints;
      if (round === null || round === undefined || round === 1) {
        avgPoints = 1.5;
      } else if (roomPoints === null || roomPoints === undefined) {
        avgPoints = 1.5;
      } else {
        avgPoints = roomPoints / (round - 1);
      }
      
      // Add speaker score point if available
      if (entry.speaker_score !== null && entry.speaker_score !== undefined) {
        speakerData.push({
          x: Math.round(avgPoints * 1000) / 1000,
          y: entry.speaker_score
        });
      }
      
      // Add team points point if available
      if (entry.team_points !== null && entry.team_points !== undefined) {
        teamPointsData.push({
          x: Math.round(avgPoints * 1000) / 1000,
          y: entry.team_points
        });
      }
    });
    
    return { speakerData, teamPointsData };
  }
  
  /**
   * Calculate best fit line using linear regression
   * Returns slope, intercept, and error bars
   */
  function calculateBestFitLine(data) {
    if (!data || data.length < 2) return null;
    
    const x_vals = data.map(d => d.x);
    const y_vals = data.map(d => d.y);
    
    const n = x_vals.length;
    const sum_x = x_vals.reduce((a, b) => a + b, 0);
    const sum_y = y_vals.reduce((a, b) => a + b, 0);
    const sum_xy = x_vals.reduce((sum, x, i) => sum + x * y_vals[i], 0);
    const sum_x2 = x_vals.reduce((sum, x) => sum + x * x, 0);
    
    const slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x);
    const intercept = (sum_y - slope * sum_x) / n;
    
    // Calculate standard error and error bars
    let sumSquaredResiduals = 0;
    for (let i = 0; i < data.length; i++) {
      const predicted = slope * data[i].x + intercept;
      const residual = data[i].y - predicted;
      sumSquaredResiduals += residual * residual;
    }
    
    const stdError = Math.sqrt(sumSquaredResiduals / (n - 2));
    const meanX = sum_x / n;
    const sumSquaredDevX = x_vals.reduce((sum, x) => sum + Math.pow(x - meanX, 2), 0);
    
    const x_min = Math.min(...x_vals);
    const x_max = Math.max(...x_vals);
    const multiplier = 1.96; // 95% confidence interval
    const numPoints = 50;
    const step = (x_max - x_min) / (numPoints - 1);
    
    const errorBars = [];
    for (let i = 0; i < numPoints; i++) {
      const x = x_min + i * step;
      const predicted = slope * x + intercept;
      const margin = multiplier * stdError * Math.sqrt(1 / n + Math.pow(x - meanX, 2) / sumSquaredDevX);
      
      errorBars.push({
        x: x,
        yUpper: predicted + margin,
        yLower: predicted - margin
      });
    }
    
    return {
      slope: slope,
      intercept: intercept,
      line: {
        low: [x_min, slope * x_min + intercept],
        high: [x_max, slope * x_max + intercept]
      },
      errorBars: errorBars
    };
  }
  
  /**
   * Get current data based on y-axis selection
   */
  function getCurrentData() {
    return currentYAxis === 'speaker_score' ? speakerData : teamPointsData;
  }
  
  /**
   * Plugin to draw best fit line and error bars (similar to Speaks over time chart)
   */
  const scatterBestFitLinePlugin = {
    id: 'scatterBestFitLine',
    beforeDatasetsDraw(chart, args, pluginOptions) {
      const { ctx, chartArea: { top, bottom, left, right, width, height },
        scales: { x, y } } = chart;
      ctx.save();

      const chartData = chart.data.datasets[0].data;

      if (!chartData || chartData.length === 0) {
        ctx.restore();
        return;
      }

      // Get current best fit line data
      const currentBestFit = currentYAxis === 'speaker_score' 
        ? (bestFitLine && bestFitLine.speaker ? bestFitLine.speaker : null)
        : (bestFitLine && bestFitLine.team ? bestFitLine.team : null);

      if (!currentBestFit || !currentBestFit.line) {
        ctx.restore();
        return;
      }

      // Get the chart's x-axis range for proper alignment
      const xAxisMin = x.min;
      const xAxisMax = x.max;

      // Draw error bars (upper bound) as dotted line
      if (currentBestFit.errorBars && currentBestFit.errorBars.length > 0) {
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(54, 162, 235, 0.5)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([5, 5]);

        for (let i = 0; i < currentBestFit.errorBars.length; i++) {
          const point = currentBestFit.errorBars[i];
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

        for (let i = 0; i < currentBestFit.errorBars.length; i++) {
          const point = currentBestFit.errorBars[i];
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
      ctx.moveTo(x.getPixelForValue(currentBestFit.line.low[0]), y.getPixelForValue(currentBestFit.line.low[1]));
      ctx.lineTo(x.getPixelForValue(currentBestFit.line.high[0]), y.getPixelForValue(currentBestFit.line.high[1]));
      ctx.stroke();
      ctx.closePath();

      ctx.restore();
    }
  };
  
  /**
   * Initialize or update the chart
   */
  function initChart(data) {
    const canvas = document.getElementById('avg_points_chart');
    if (!canvas) return;
    
    // Set explicit dimensions to prevent expansion
    const chartContainer = canvas.parentElement;
    if (chartContainer && chartContainer.classList.contains('avg-points-chart-container')) {
      chartContainer.style.height = '300px';
      chartContainer.style.maxHeight = '300px';
      chartContainer.style.minHeight = '300px';
      chartContainer.style.overflow = 'hidden';
    }
    
    canvas.style.width = '100%';
    canvas.style.height = '300px';
    canvas.style.maxHeight = '300px';
    canvas.height = 300;
    
    // Check if data is already processed (pre-calculated from backend)
    if (data.length > 0 && data[0].hasOwnProperty('x') && data[0].hasOwnProperty('y')) {
      // Use pre-calculated speaker data directly
      speakerData = data;
      // Try to get team points data from separate element
      const teamDataElement = document.getElementById('avg_points_team_data');
      if (teamDataElement && teamDataElement.textContent.trim()) {
        try {
          teamPointsData = JSON.parse(teamDataElement.textContent);
        } catch (e) {
          console.warn('Could not parse team points data:', e);
          teamPointsData = [];
        }
      } else {
        // Fallback: try to calculate from full_data_list
        const fullDataElement = document.getElementById('full_data_list');
        if (fullDataElement) {
          try {
            const fullData = JSON.parse(fullDataElement.textContent);
            const teamData = calculateAveragePointsData(fullData);
            teamPointsData = teamData.teamPointsData;
          } catch (e) {
            console.warn('Could not calculate team points data:', e);
            teamPointsData = [];
          }
        } else {
          teamPointsData = [];
        }
      }
      
      // Get best fit line from backend
      const bestFitElement = document.getElementById('avg_points_best_fit');
      if (bestFitElement && bestFitElement.textContent.trim()) {
        try {
          const backendBestFit = JSON.parse(bestFitElement.textContent);
          // Recalculate with error bars if backend only provides points
          bestFitLine = {
            speaker: backendBestFit.speaker && backendBestFit.speaker.errorBars 
              ? backendBestFit.speaker 
              : calculateBestFitLine(speakerData),
            team: backendBestFit.team && backendBestFit.team.errorBars 
              ? backendBestFit.team 
              : calculateBestFitLine(teamPointsData)
          };
        } catch (e) {
          console.warn('Could not parse best fit line data:', e);
          // Calculate best fit line from data
          bestFitLine = {
            speaker: calculateBestFitLine(speakerData),
            team: calculateBestFitLine(teamPointsData)
          };
        }
      } else {
        // Calculate best fit line from data
        bestFitLine = {
          speaker: calculateBestFitLine(speakerData),
          team: calculateBestFitLine(teamPointsData)
        };
      }
    } else {
      // Calculate from raw data
      const chartData = calculateAveragePointsData(data);
      speakerData = chartData.speakerData;
      teamPointsData = chartData.teamPointsData;
      
      // Calculate best fit lines
      bestFitLine = {
        speaker: calculateBestFitLine(speakerData),
        team: calculateBestFitLine(teamPointsData)
      };
    }
    
    if (chart) {
      // Update existing chart
      chart.data.datasets[0].data = getCurrentData();
      
      // Recalculate best fit line for current data if needed
      const currentData = getCurrentData();
      if (currentData && currentData.length >= 2) {
        const recalculated = calculateBestFitLine(currentData);
        if (currentYAxis === 'speaker_score') {
          bestFitLine = bestFitLine || {};
          bestFitLine.speaker = recalculated;
        } else {
          bestFitLine = bestFitLine || {};
          bestFitLine.team = recalculated;
        }
      }
      
      // Update y-axis bounds
      let yMin, yMax;
      if (currentYAxis === 'speaker_score') {
        const scores = speakerData.map(d => d.y).filter(y => y !== null && y !== undefined);
        if (scores.length > 0) {
          yMin = Math.floor(Math.min(...scores) / 5) * 5;
          yMax = Math.ceil(Math.max(...scores) / 5) * 5;
          chart.options.scales.y.min = yMin;
          chart.options.scales.y.max = yMax;
        }
      } else {
        const points = teamPointsData.map(d => d.y).filter(y => y !== null && y !== undefined);
        if (points.length > 0) {
          yMin = 0;
          yMax = 3;
          chart.options.scales.y.min = yMin;
          chart.options.scales.y.max = yMax;
        }
      }
      
      chart.update();
      return;
    }
    
    // Check if we have data to display
    const currentData = getCurrentData();
    if (!currentData || currentData.length === 0) {
      console.warn('No data available for average points chart');
      return;
    }
    
    // Determine y-axis bounds based on data type
    let yMin, yMax;
    if (currentYAxis === 'speaker_score') {
      const scores = speakerData.map(d => d.y).filter(y => y !== null && y !== undefined);
      if (scores.length === 0) {
        console.warn('No speaker score data available');
        return;
      }
      yMin = Math.floor(Math.min(...scores) / 5) * 5;
      yMax = Math.ceil(Math.max(...scores) / 5) * 5;
    } else {
      const points = teamPointsData.map(d => d.y).filter(y => y !== null && y !== undefined);
      if (points.length === 0) {
        console.warn('No team points data available');
        return;
      }
      yMin = 0;
      yMax = 3;
    }
    
    // Recalculate best fit line for current data
    const recalculated = calculateBestFitLine(currentData);
    if (currentYAxis === 'speaker_score') {
      bestFitLine = bestFitLine || {};
      bestFitLine.speaker = recalculated;
    } else {
      bestFitLine = bestFitLine || {};
      bestFitLine.team = recalculated;
    }
    
    // Prepare datasets
    const datasets = [{
      label: currentYAxis === 'speaker_score' ? 'speaks' : 'team_points',
      data: getCurrentData(),
      borderWidth: 1
    }];
    
    chart = new Chart(canvas, {
      type: 'scatter',
      data: {
        datasets: datasets
      },
      plugins: [scatterBestFitLinePlugin],
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          x: {
            type: 'linear',
            min: 0,
            max: 3,
            ticks: {
              stepSize: 0.5
            }
          },
          y: {
            min: yMin,
            max: yMax
          }
        }
      }
    });
  }
  
  /**
   * Toggle Y-axis between speaker score and team points
   */
  function toggleYAxis() {
    currentYAxis = currentYAxis === 'speaker_score' ? 'team_points' : 'speaker_score';
    
    if (!chart) return;
    
    const data = getCurrentData();
    chart.data.datasets[0].data = data;
    chart.data.datasets[0].label = currentYAxis === 'speaker_score' 
      ? 'Avg Speaker Score' 
      : 'Avg Team Points';
    
    chart.options.scales.y.title.text = currentYAxis === 'speaker_score' 
      ? 'Speaker Score' 
      : 'Team Points';
    
    // Update best fit line
    const currentBestFit = currentYAxis === 'speaker_score' 
      ? (bestFitLine && bestFitLine.speaker ? bestFitLine.speaker : null)
      : (bestFitLine && bestFitLine.team ? bestFitLine.team : null);
    
    if (currentBestFit && currentBestFit.points) {
      if (chart.data.datasets.length > 1) {
        chart.data.datasets[1].data = currentBestFit.points;
      } else {
        chart.data.datasets.push({
          label: 'Best Fit Line',
          data: currentBestFit.points,
          type: 'line',
          borderColor: 'rgba(255, 99, 132, 1)',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 0,
          fill: false,
          tension: 0
        });
      }
    } else if (chart.data.datasets.length > 1) {
      chart.data.datasets.pop();
    }
    
    // Update y-axis bounds
    if (currentYAxis === 'speaker_score') {
      const scores = speakerData.map(d => d.y).filter(y => y !== null && y !== undefined);
      if (scores.length > 0) {
        chart.options.scales.y.min = Math.floor(Math.min(...scores) / 5) * 5;
        chart.options.scales.y.max = Math.ceil(Math.max(...scores) / 5) * 5;
      }
    } else {
      chart.options.scales.y.min = 0;
      chart.options.scales.y.max = 3;
    }
    
    chart.update();
    
    return currentYAxis;
  }
  
  /**
   * Update chart with filtered data
   */
  function updateWithData(data) {
    const chartData = calculateAveragePointsData(data);
    speakerData = chartData.speakerData;
    teamPointsData = chartData.teamPointsData;
    
    // Recalculate best fit lines
    bestFitLine = {
      speaker: calculateBestFitLine(speakerData),
      team: calculateBestFitLine(teamPointsData)
    };
    
    if (chart) {
      chart.data.datasets[0].data = getCurrentData();
      
      // Update y-axis title
      chart.options.scales.y.title.text = currentYAxis === 'speaker_score' 
        ? 'Speaker Score' 
        : 'Team Points';
      
      // Update y-axis bounds
      if (currentYAxis === 'speaker_score') {
        const scores = speakerData.map(d => d.y).filter(y => y !== null && y !== undefined);
        if (scores.length > 0) {
          chart.options.scales.y.min = Math.floor(Math.min(...scores) / 5) * 5;
          chart.options.scales.y.max = Math.ceil(Math.max(...scores) / 5) * 5;
        }
      } else {
        chart.options.scales.y.min = 0;
        chart.options.scales.y.max = 3;
      }
      
      // Update best fit line
      const currentBestFit = currentYAxis === 'speaker_score' 
        ? (bestFitLine && bestFitLine.speaker ? bestFitLine.speaker : null)
        : (bestFitLine && bestFitLine.team ? bestFitLine.team : null);
      
      if (currentBestFit && currentBestFit.points) {
        if (chart.data.datasets.length > 1) {
          chart.data.datasets[1].data = currentBestFit.points;
        } else {
          chart.data.datasets.push({
            label: 'Best Fit Line',
            data: currentBestFit.points,
            type: 'line',
            borderColor: 'rgba(255, 99, 132, 1)',
            backgroundColor: 'rgba(255, 99, 132, 0.1)',
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 0,
            fill: false,
            tension: 0
          });
        }
      } else if (chart.data.datasets.length > 1) {
        chart.data.datasets.pop();
      }
      
      chart.update();
    }
  }
  
  // Initialize toggle button handler
  document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('avg-points-toggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const newAxis = toggleYAxis();
        toggleBtn.textContent = newAxis === 'speaker_score' 
          ? 'Show Team Points' 
          : 'Show Speaker Score';
        
        // Update title based on selected display
        const titleElement = document.getElementById('avg-points-title');
        if (titleElement) {
          titleElement.textContent = newAxis === 'speaker_score' 
            ? 'Speaks by average points of room' 
            : 'Team points by average points of room';
        }
      });
    }
    
    // Initialize chart if data element exists
    const dataElement = document.getElementById('avg_points_data');
    if (dataElement && dataElement.textContent.trim()) {
      try {
        const data = JSON.parse(dataElement.textContent);
        if (Array.isArray(data) && data.length > 0) {
          initChart(data);
        } else if (data === null) {
          // Data is null, don't initialize chart
          console.log('Average points data is null, skipping chart initialization');
        }
      } catch (e) {
        console.error('Failed to initialize average points chart:', e);
      }
    } else {
      // Also try to initialize from full_data_list if avg_points_data is not available
      const fullDataElement = document.getElementById('full_data_list');
      if (fullDataElement && fullDataElement.textContent.trim()) {
        try {
          const data = JSON.parse(fullDataElement.textContent);
          if (Array.isArray(data) && data.length > 0) {
            initChart(data);
          }
        } catch (e) {
          console.error('Failed to initialize average points chart from full data:', e);
        }
      }
    }
  });
  
  // Register with filter state if available
  if (typeof FilterState !== 'undefined') {
    FilterState.onFilterChange(updateWithData);
  }
  
  return {
    init: initChart,
    toggle: toggleYAxis,
    update: updateWithData,
    getCurrentYAxis: () => currentYAxis
  };
})();
