/**
 * Global Filter State Management for Analysis Tab
 * 
 * Provides a centralized state for all filters and triggers chart updates
 * when filters change.
 */

const FilterState = (function() {
  'use strict';
  
  // Internal state
  let state = {
    teamPositions: [],      // OG, OO, CG, CO
    speakerPositions: [],   // PM, DPM, LO, DLO, MG, GW, MO, OW
    partners: [],
    motionTypes: [],        // Motion type filter
    avgPointsRange: [0, 3], // Average points range [min, max]
    dateRange: [null, null] // [startDate, endDate]
  };
  
  // Registered chart update callbacks
  const callbacks = [];
  
  // Get full dataset from DOM
  function getFullDataset() {
    const element = document.getElementById('full_data_list');
    if (!element) return [];
    try {
      return JSON.parse(element.textContent);
    } catch (e) {
      console.error('Failed to parse full_data_list:', e);
      return [];
    }
  }
  
  /**
   * Calculate average points so far for an entry
   * Matches Python model property: average_points_so_far
   * Formula: room_points / (round - 1) for round > 1
   * Returns 1.5 for round 1 or if round/room_points is None
   */
  function calcAvgPoints(entry) {
    const round = entry.round;
    const roomPoints = entry.room_points;
    
    if (round === null || round === undefined || round === 1) {
      return 1.5;
    }
    if (roomPoints === null || roomPoints === undefined) {
      return 1.5;
    }
    return roomPoints / (round - 1);
  }
  
  /**
   * Check if an entry matches all current filters
   */
  function matchesFilters(entry) {
    // Team position filter
    if (state.teamPositions.length > 0) {
      if (!entry.team_position || !state.teamPositions.includes(entry.team_position)) {
        return false;
      }
    }
    
    // Speaker position filter
    if (state.speakerPositions.length > 0) {
      if (!entry.speaker_position || !state.speakerPositions.includes(entry.speaker_position)) {
        return false;
      }
    }
    
    // Partner filter
    if (state.partners.length > 0) {
      if (!entry.partner || !state.partners.includes(entry.partner)) {
        return false;
      }
    }
    
    // Motion type filter
    if (state.motionTypes.length > 0) {
      if (!entry.motion_type || !state.motionTypes.includes(entry.motion_type)) {
        return false;
      }
    }
    
    // Average points range filter
    const avgPoints = calcAvgPoints(entry);
    if (avgPoints < state.avgPointsRange[0] || avgPoints > state.avgPointsRange[1]) {
      return false;
    }
    
    // Date range filter
    if (state.dateRange[0] || state.dateRange[1]) {
      if (!entry.date) return false;
      
      const entryDate = new Date(entry.date);
      
      if (state.dateRange[0]) {
        const startDate = new Date(state.dateRange[0]);
        if (entryDate < startDate) return false;
      }
      
      if (state.dateRange[1]) {
        const endDate = new Date(state.dateRange[1]);
        if (entryDate > endDate) return false;
      }
    }
    
    return true;
  }
  
  /**
   * Get filtered dataset based on current state
   */
  function getFilteredData() {
    const fullData = getFullDataset();
    return fullData.filter(matchesFilters);
  }
  
  /**
   * Notify all registered callbacks of filter changes
   */
  function notifyCallbacks() {
    const filteredData = getFilteredData();
    callbacks.forEach(callback => {
      try {
        callback(filteredData, state);
      } catch (e) {
        console.error('Filter callback error:', e);
      }
    });
  }
  
  /**
   * Register a callback to be called when filters change
   */
  function onFilterChange(callback) {
    if (typeof callback === 'function') {
      callbacks.push(callback);
    }
  }
  
  /**
   * Update team position filter
   */
  function setTeamPositions(positions) {
    state.teamPositions = Array.isArray(positions) ? [...positions] : [];
    notifyCallbacks();
  }
  
  /**
   * Toggle a team position in the filter
   */
  function toggleTeamPosition(position) {
    const index = state.teamPositions.indexOf(position);
    if (index > -1) {
      state.teamPositions.splice(index, 1);
    } else {
      state.teamPositions.push(position);
    }
    notifyCallbacks();
    return state.teamPositions.includes(position);
  }
  
  /**
   * Update speaker position filter
   */
  function setSpeakerPositions(positions) {
    state.speakerPositions = Array.isArray(positions) ? [...positions] : [];
    notifyCallbacks();
  }
  
  /**
   * Toggle a speaker position in the filter
   */
  function toggleSpeakerPosition(position) {
    const index = state.speakerPositions.indexOf(position);
    if (index > -1) {
      state.speakerPositions.splice(index, 1);
    } else {
      state.speakerPositions.push(position);
    }
    notifyCallbacks();
    return state.speakerPositions.includes(position);
  }
  
  /**
   * Update partner filter
   */
  function setPartners(partners) {
    state.partners = Array.isArray(partners) ? [...partners] : [];
    notifyCallbacks();
  }
  
  /**
   * Toggle a partner in the filter
   */
  function togglePartner(partner) {
    const index = state.partners.indexOf(partner);
    if (index > -1) {
      state.partners.splice(index, 1);
    } else {
      state.partners.push(partner);
    }
    notifyCallbacks();
    return state.partners.includes(partner);
  }
  
  /**
   * Update motion type filter
   */
  function setMotionTypes(motionTypes) {
    state.motionTypes = Array.isArray(motionTypes) ? [...motionTypes] : [];
    notifyCallbacks();
  }
  
  /**
   * Toggle a motion type in the filter
   */
  function toggleMotionType(motionType) {
    const index = state.motionTypes.indexOf(motionType);
    if (index > -1) {
      state.motionTypes.splice(index, 1);
    } else {
      state.motionTypes.push(motionType);
    }
    notifyCallbacks();
    return state.motionTypes.includes(motionType);
  }
  
  /**
   * Update average points range
   */
  function setAvgPointsRange(min, max) {
    state.avgPointsRange = [
      Math.max(0, min || 0),
      Math.min(3, max || 3)
    ];
    notifyCallbacks();
  }
  
  /**
   * Update date range
   */
  function setDateRange(startDate, endDate) {
    state.dateRange = [startDate || null, endDate || null];
    notifyCallbacks();
  }
  
  /**
   * Clear all filters
   */
  function clearAll() {
    state = {
      teamPositions: [],
      speakerPositions: [],
      partners: [],
      motionTypes: [],
      avgPointsRange: [0, 3],
      dateRange: [null, null]
    };
    notifyCallbacks();
  }
  
  /**
   * Get current filter state (read-only copy)
   */
  function getState() {
    return JSON.parse(JSON.stringify(state));
  }
  
  /**
   * Check if any filters are active
   */
  function hasActiveFilters() {
    return (
      state.teamPositions.length > 0 ||
      state.speakerPositions.length > 0 ||
      state.partners.length > 0 ||
      state.motionTypes.length > 0 ||
      state.avgPointsRange[0] > 0 ||
      state.avgPointsRange[1] < 3 ||
      state.dateRange[0] !== null ||
      state.dateRange[1] !== null
    );
  }
  
  /**
   * Get unique values for filter dropdowns from dataset
   */
  function getFilterOptions() {
    const data = getFullDataset();
    
    const teamPositions = new Set();
    const speakerPositions = new Set();
    const partners = new Set();
    const motionTypes = new Set();
    const dates = [];
    let maxRoomPoints = 0;
    
    data.forEach(entry => {
      if (entry.team_position) teamPositions.add(entry.team_position);
      if (entry.speaker_position) speakerPositions.add(entry.speaker_position);
      if (entry.partner) partners.add(entry.partner);
      if (entry.motion_type) motionTypes.add(entry.motion_type);
      if (entry.date) dates.push(new Date(entry.date));
      if (entry.room_points !== null) {
        maxRoomPoints = Math.max(maxRoomPoints, entry.room_points);
      }
    });
    
    // Sort dates
    dates.sort((a, b) => a - b);
    
    // Custom sort order for team positions: OG, OO, CG, CO
    const teamPositionOrder = ['OG', 'OO', 'CG', 'CO'];
    const sortedTeamPositions = Array.from(teamPositions).sort((a, b) => {
      const indexA = teamPositionOrder.indexOf(a);
      const indexB = teamPositionOrder.indexOf(b);
      // If both are in the order list, sort by their index
      if (indexA !== -1 && indexB !== -1) return indexA - indexB;
      // If only one is in the list, prioritize it
      if (indexA !== -1) return -1;
      if (indexB !== -1) return 1;
      // If neither is in the list, sort alphabetically
      return a.localeCompare(b);
    });
    
    return {
      teamPositions: sortedTeamPositions,
      speakerPositions: Array.from(speakerPositions),
      partners: Array.from(partners).sort(),
      motionTypes: Array.from(motionTypes).sort(),
      dateRange: {
        min: dates.length > 0 ? dates[0].toISOString().split('T')[0] : null,
        max: dates.length > 0 ? dates[dates.length - 1].toISOString().split('T')[0] : null
      },
      maxRoomPoints: maxRoomPoints
    };
  }
  
  // Public API
  return {
    onFilterChange,
    getFilteredData,
    getState,
    hasActiveFilters,
    getFilterOptions,
    clearAll,
    
    // Team position
    setTeamPositions,
    toggleTeamPosition,
    
    // Speaker position
    setSpeakerPositions,
    toggleSpeakerPosition,
    
    // Partner
    setPartners,
    togglePartner,
    
    // Motion type
    setMotionTypes,
    toggleMotionType,
    
    // Ranges
    setAvgPointsRange,
    setDateRange,
    
    // Utility
    calcAvgPoints
  };
})();


/**
 * Filter UI Controller
 * 
 * Handles the UI elements for filters
 */
const FilterUI = (function() {
  'use strict';
  
  /**
   * Initialize filter UI elements
   */
  function init() {
    initTeamPositionButtons();
    initSpeakerPositionButtons();
    initPartnerSelect();
    initMotionTypeSelect();
    initDateRangeSlider();
    initAvgPointsRangeSlider();
    initClearButton();
  }
  
  /**
   * Initialize team position toggle buttons
   */
  function initTeamPositionButtons() {
    const container = document.getElementById('team-position-filters');
    if (!container) return;
    
    const positions = ['OG', 'OO', 'CG', 'CO'];
    const options = FilterState.getFilterOptions();
    
    positions.forEach(pos => {
      const btn = document.createElement('button');
      btn.className = 'filter-btn';
      btn.textContent = pos;
      btn.dataset.position = pos;
      
      // Disable if no data for this position
      if (!options.teamPositions.includes(pos)) {
        btn.disabled = true;
        btn.classList.add('disabled');
      }
      
      btn.addEventListener('click', () => {
        const isActive = FilterState.toggleTeamPosition(pos);
        btn.classList.toggle('active', isActive);
      });
      
      container.appendChild(btn);
    });
  }
  
  /**
   * Initialize speaker position toggle buttons
   */
  function initSpeakerPositionButtons() {
    const container = document.getElementById('speaker-position-filters');
    if (!container) return;
    
    // Order for 2-column grid: PM LO / DPM DLO / MG MO / GW OW
    const positions = ['PM', 'LO', 'DPM', 'DLO', 'MG', 'MO', 'GW', 'OW'];
    const options = FilterState.getFilterOptions();
    
    positions.forEach(pos => {
      const btn = document.createElement('button');
      btn.className = 'filter-btn';
      btn.textContent = pos;
      btn.dataset.position = pos;
      
      if (!options.speakerPositions.includes(pos)) {
        btn.disabled = true;
        btn.classList.add('disabled');
      }
      
      btn.addEventListener('click', () => {
        const isActive = FilterState.toggleSpeakerPosition(pos);
        btn.classList.toggle('active', isActive);
      });
      
      container.appendChild(btn);
    });
  }
  
  /**
   * Initialize partner multi-select
   */
  function initPartnerSelect() {
    const container = document.getElementById('partner-filters');
    if (!container) return;
    
    const options = FilterState.getFilterOptions();
    
    if (options.partners.length === 0) {
      container.innerHTML = '<span class="no-data">No partner data</span>';
      return;
    }
    
    const select = document.createElement('select');
    select.id = 'partner-select';
    select.multiple = true;
    select.className = 'filter-select';
    
    options.partners.forEach(partner => {
      const option = document.createElement('option');
      option.value = partner;
      option.textContent = partner;
      select.appendChild(option);
    });
    
    select.addEventListener('change', () => {
      const selected = Array.from(select.selectedOptions).map(opt => opt.value);
      FilterState.setPartners(selected);
    });
    
    container.appendChild(select);
  }
  
  /**
   * Initialize motion type multi-select
   */
  function initMotionTypeSelect() {
    const container = document.getElementById('motion-type-filters');
    if (!container) return;
    
    const options = FilterState.getFilterOptions();
    
    if (options.motionTypes.length === 0) {
      container.innerHTML = '<span class="no-data">No motion type data</span>';
      return;
    }
    
    const select = document.createElement('select');
    select.id = 'motion-type-select';
    select.multiple = true;
    select.className = 'filter-select';
    
    options.motionTypes.forEach(motionType => {
      const option = document.createElement('option');
      option.value = motionType;
      option.textContent = motionType;
      select.appendChild(option);
    });
    
    select.addEventListener('change', () => {
      const selected = Array.from(select.selectedOptions).map(opt => opt.value);
      FilterState.setMotionTypes(selected);
    });
    
    container.appendChild(select);
  }
  
  /**
   * Initialize date range slider
   */
  function initDateRangeSlider() {
    const container = document.getElementById('date-range-filters');
    if (!container) return;
    
    const options = FilterState.getFilterOptions();
    
    if (!options.dateRange.min || !options.dateRange.max) {
      container.innerHTML = '<span class="no-data">No date data</span>';
      return;
    }
    
    // Start date input
    const startLabel = document.createElement('label');
    startLabel.textContent = 'From: ';
    const startInput = document.createElement('input');
    startInput.type = 'date';
    startInput.id = 'date-start';
    startInput.className = 'filter-date';
    startInput.min = options.dateRange.min;
    startInput.max = options.dateRange.max;
    startLabel.appendChild(startInput);
    
    // End date input
    const endLabel = document.createElement('label');
    endLabel.textContent = ' To: ';
    const endInput = document.createElement('input');
    endInput.type = 'date';
    endInput.id = 'date-end';
    endInput.className = 'filter-date';
    endInput.min = options.dateRange.min;
    endInput.max = options.dateRange.max;
    endLabel.appendChild(endInput);
    
    const updateDates = () => {
      FilterState.setDateRange(startInput.value || null, endInput.value || null);
    };
    
    startInput.addEventListener('change', updateDates);
    endInput.addEventListener('change', updateDates);
    
    container.appendChild(startLabel);
    container.appendChild(endLabel);
  }

  /**
   * Initialize average points per room range slider
   */
  function initAvgPointsRangeSlider() {
    const container = document.getElementById('avg-points-range-filters');
    if (!container) return;
    
    // Create range inputs
    const minLabel = document.createElement('label');
    minLabel.textContent = 'Min: ';
    const minInput = document.createElement('input');
    minInput.type = 'number';
    minInput.id = 'avg-points-min';
    minInput.className = 'filter-range';
    minInput.min = '0';
    minInput.max = '3';
    minInput.step = '0.1';
    minInput.value = '0';
    minInput.style.width = '80px';
    minLabel.appendChild(minInput);
    
    const maxLabel = document.createElement('label');
    maxLabel.textContent = ' Max: ';
    const maxInput = document.createElement('input');
    maxInput.type = 'number';
    maxInput.id = 'avg-points-max';
    maxInput.className = 'filter-range';
    maxInput.min = '0';
    maxInput.max = '3';
    maxInput.step = '0.1';
    maxInput.value = '3';
    maxInput.style.width = '80px';
    maxLabel.appendChild(maxInput);
    
    const updateRange = () => {
      const min = parseFloat(minInput.value) || 0;
      const max = parseFloat(maxInput.value) || 3;
      FilterState.setAvgPointsRange(min, max);
    };
    
    minInput.addEventListener('change', updateRange);
    minInput.addEventListener('input', updateRange);
    maxInput.addEventListener('change', updateRange);
    maxInput.addEventListener('input', updateRange);
    
    container.appendChild(minLabel);
    container.appendChild(maxLabel);
  }
  
  /**
   * Initialize clear all button
   */
  function initClearButton() {
    const btn = document.getElementById('clear-filters');
    if (!btn) return;
    
    btn.addEventListener('click', () => {
      FilterState.clearAll();
      
      // Reset UI elements
      document.querySelectorAll('.filter-btn.active').forEach(b => {
        b.classList.remove('active');
      });
      
      const partnerSelect = document.getElementById('partner-select');
      if (partnerSelect) {
        Array.from(partnerSelect.options).forEach(opt => opt.selected = false);
      }
      
      const motionTypeSelect = document.getElementById('motion-type-select');
      if (motionTypeSelect) {
        Array.from(motionTypeSelect.options).forEach(opt => opt.selected = false);
      }
      
      const dateStart = document.getElementById('date-start');
      const dateEnd = document.getElementById('date-end');
      if (dateStart) dateStart.value = '';
      if (dateEnd) dateEnd.value = '';
      
      const avgPointsMin = document.getElementById('avg-points-min');
      const avgPointsMax = document.getElementById('avg-points-max');
      if (avgPointsMin) avgPointsMin.value = '0';
      if (avgPointsMax) avgPointsMax.value = '3';
    });
  }
  
  return {
    init
  };
})();


/**
 * Speaks Overview Updater
 * 
 * Calculates and displays statistics for filtered data
 */
const SpeaksOverview = (function() {
  'use strict';
  
  /**
   * Calculate statistics from filtered data
   */
  function calculateStats(filteredData) {
    if (!filteredData || filteredData.length === 0) {
      return {
        avg: null,
        std: null,
        min: null,
        max: null,
        count: 0,
        avgPoints: null
      };
    }
    
    // Extract speaker scores
    const scores = filteredData
      .map(entry => entry.speaker_score)
      .filter(score => score !== null && score !== undefined);
    
    // Extract team points
    const points = filteredData
      .map(entry => entry.team_points)
      .filter(points => points !== null && points !== undefined);
    
    if (scores.length === 0) {
      return {
        avg: null,
        std: null,
        min: null,
        max: null,
        count: 0,
        avgPoints: points.length > 0 ? roundTo(points.reduce((acc, val) => acc + val, 0) / points.length, 2) : null
      };
    }
    
    // Calculate average
    const sum = scores.reduce((acc, val) => acc + val, 0);
    const avg = sum / scores.length;
    
    // Calculate standard deviation
    const variance = scores.reduce((acc, val) => acc + Math.pow(val - avg, 2), 0) / scores.length;
    const std = Math.sqrt(variance);
    
    // Calculate min and max
    const min = Math.min(...scores);
    const max = Math.max(...scores);
    
    // Calculate average points
    const avgPoints = points.length > 0 
      ? roundTo(points.reduce((acc, val) => acc + val, 0) / points.length, 2)
      : null;
    
    return {
      avg: roundTo(avg, 2),
      std: roundTo(std, 2),
      min: min,
      max: max,
      count: scores.length,
      avgPoints: avgPoints
    };
  }
  
  /**
   * Round to specified decimal places
   */
  function roundTo(value, decimals) {
    if (value === null || value === undefined) return null;
    return Math.round(value * Math.pow(10, decimals)) / Math.pow(10, decimals);
  }
  
  /**
   * Update the overview display
   */
  function updateOverview(filteredData) {
    const stats = calculateStats(filteredData);
    
    const avgEl = document.getElementById('overview-avg');
    const stdEl = document.getElementById('overview-std');
    const minEl = document.getElementById('overview-min');
    const maxEl = document.getElementById('overview-max');
    const countEl = document.getElementById('overview-count');
    const avgPointsEl = document.getElementById('overview-avg-points');
    
    if (avgEl) avgEl.textContent = stats.avg !== null ? stats.avg : '-';
    if (stdEl) stdEl.textContent = stats.std !== null ? stats.std : '-';
    if (minEl) minEl.textContent = stats.min !== null ? stats.min : '-';
    if (maxEl) maxEl.textContent = stats.max !== null ? stats.max : '-';
    if (countEl) countEl.textContent = stats.count;
    if (avgPointsEl) avgPointsEl.textContent = stats.avgPoints !== null ? stats.avgPoints : '-';
  }
  
  /**
   * Initialize overview updater
   */
  function init() {
    // Calculate initial overview from full dataset (before any filters)
    // Try to get data directly first, then fall back to FilterState
    const element = document.getElementById('full_data_list');
    let initialData = [];
    
    if (element) {
      try {
        initialData = JSON.parse(element.textContent);
      } catch (e) {
        console.error('Failed to parse full_data_list for overview:', e);
        // Fall back to FilterState
        initialData = FilterState.getFilteredData();
      }
    } else {
      // Element not found, use FilterState
      initialData = FilterState.getFilteredData();
    }
    
    // Update overview with initial data immediately
    updateOverview(initialData);
    
    // Register callback to update overview when filters change
    FilterState.onFilterChange((filteredData) => {
      updateOverview(filteredData);
    });
  }
  
  return {
    init,
    updateOverview
  };
})();

// Initialize filters when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Only initialize on the analysis page
  if (document.getElementById('filter-controls')) {
    FilterUI.init();
    SpeaksOverview.init();
  }
});

