/**
 * Positional Win-Rate Heatmap Module
 * 
 * Creates a 4x4 grid showing win rates between BP positions.
 * The left side (rows) shows your position.
 * The columns show how often you win against each opponent position.
 * For example, when you are CG, it shows how often you beat OG, OO, and CO.
 */

const PositionalHeatmap = (function() {
  'use strict';
  
  const POSITIONS = ['OG', 'OO', 'CG', 'CO'];
  
  let container = null;
  let heatmapData = null;
  
  /**
   * Interpolate between red and green based on win rate value
   * value: 0-100 win rate (0% = red/bad, 50% = yellow, 100% = green/good)
   */
  function getHeatmapColor(value) {
    if (value === null || value === undefined) {
      return '#1a1a2e'; // Dark background for null/self
    }
    
    // Clamp value between 0 and 100
    const v = Math.max(0, Math.min(100, value));
    
    // Color interpolation
    // Red (0% win rate) -> Yellow (50%) -> Green (100% win rate)
    let r, g, b;
    
    if (v < 50) {
      // Red to Yellow (low win rates)
      const t = v / 50;
      r = 220;
      g = Math.round(80 + t * 140); // 80 -> 220
      b = 60;
    } else {
      // Yellow to Green (high win rates)
      const t = (v - 50) / 50;
      r = Math.round(220 - t * 160); // 220 -> 60
      g = 180;
      b = Math.round(60 + t * 60); // 60 -> 120
    }
    
    return `rgb(${r}, ${g}, ${b})`;
  }
  
  /**
   * Get text color based on background brightness
   */
  function getTextColor(value) {
    if (value === null || value === undefined) {
      return '#888';
    }
    // Use white text for better contrast
    return value > 60 ? '#1a1a2e' : '#fff';
  }
  
  /**
   * Create the heatmap grid element
   */
  function createGrid() {
    const grid = document.createElement('div');
    grid.className = 'heatmap-grid';
    grid.style.cssText = `
      display: grid;
      grid-template-columns: 60px repeat(4, 1fr);
      grid-template-rows: 40px repeat(4, 1fr);
      gap: 2px;
      max-width: 100%;
      margin: 0;
    `;
    
    // Header row
    const cornerCell = createCell('', 'header');
    grid.appendChild(cornerCell);
    
    POSITIONS.forEach(pos => {
      const headerCell = createCell(pos, 'header');
      headerCell.style.cssText += `
        font-weight: bold;
        background: #2d2d44;
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
      `;
      grid.appendChild(headerCell);
    });
    
    // Data rows
    POSITIONS.forEach(rowPos => {
      // Row label
      const rowLabel = createCell(rowPos, 'row-label');
      rowLabel.style.cssText += `
        font-weight: bold;
        background: #2d2d44;
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
      `;
      grid.appendChild(rowLabel);
      
      // Data cells
      POSITIONS.forEach(colPos => {
        const cell = createCell('', 'data');
        cell.id = `heatmap-cell-${rowPos}-${colPos}`;
        cell.dataset.row = rowPos;
        cell.dataset.col = colPos;
        cell.style.cssText += `
          display: flex;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          min-height: 60px;
          transition: all 0.3s ease;
        `;
        grid.appendChild(cell);
      });
    });
    
    return grid;
  }
  
  /**
   * Create a single cell element
   */
  function createCell(content, type) {
    const cell = document.createElement('div');
    cell.className = `heatmap-cell heatmap-${type}`;
    cell.textContent = content;
    cell.style.cssText = `
      padding: 8px;
      text-align: center;
      border-radius: 4px;
    `;
    return cell;
  }
  
  /**
   * Update cell with value and color
   */
  function updateCell(rowPos, colPos, value) {
    const cell = document.getElementById(`heatmap-cell-${rowPos}-${colPos}`);
    if (!cell) return;
    
    const bgColor = getHeatmapColor(value);
    const textColor = getTextColor(value);
    
    cell.style.backgroundColor = bgColor;
    cell.style.color = textColor;
    
    if (value === null || value === undefined) {
      cell.innerHTML = `<span style="font-size: 0.8em;">—</span>`;
    } else {
      cell.innerHTML = `
        <span style="font-size: 1.2em; font-weight: bold;">${value.toFixed(0)}%</span>
      `;
    }
  }
  
  /**
   * Calculate heatmap data from filtered dataset (frontend calculation)
   * @param {Array} filteredData - The filtered dataset
   * @returns {Object} Heatmap data structure
   */
  function calculateHeatmap(filteredData) {
    // Points to rank mapping (3 points = 1st, 2 = 2nd, 1 = 3rd, 0 = 4th)
    const POINTS_TO_RANK = {3: 1, 2: 2, 1: 3, 0: 4};
    
    // Filter to entries with team position and team points
    const validEntries = filteredData.filter(entry => 
      entry.team_position && 
      entry.team_points !== null && 
      entry.team_points !== undefined &&
      POSITIONS.includes(entry.team_position)
    );
    
    if (validEntries.length === 0) {
      return null;
    }
    
    // Initialize result structure
    const result = {};
    POSITIONS.forEach(pos => {
      result[pos] = {};
      POSITIONS.forEach(opp => {
        result[pos][opp] = null;
      });
    });
    
    // Track wins and total matchups
    // Key: (my_position, opponent_position) -> {wins: count, total: count}
    const matchups = {};
    
    function getMatchupKey(myPos, oppPos) {
      return `${myPos}-${oppPos}`;
    }
    
    function initMatchup(key) {
      if (!matchups[key]) {
        matchups[key] = {wins: 0, total: 0};
      }
    }
    
    validEntries.forEach(entry => {
      const myPosition = entry.team_position;
      const myPoints = entry.team_points;
      const myRank = POINTS_TO_RANK[myPoints];
      
      if (!myPosition || myRank === undefined) {
        return;
      }
      
      // Get full call from opponent_positions (stored as JSON string)
      let fullCall = [];
      if (entry.opponent_positions) {
        try {
          if (typeof entry.opponent_positions === 'string') {
            fullCall = JSON.parse(entry.opponent_positions);
          } else if (Array.isArray(entry.opponent_positions)) {
            fullCall = entry.opponent_positions;
          }
        } catch (e) {
          // Invalid JSON, ignore
        }
      }
      
      // If we have a full call (4 positions), use it to determine exact rankings
      if (fullCall.length === 4 && fullCall.includes(myPosition)) {
        // Find my position in the call to get my rank index
        const myIndex = fullCall.indexOf(myPosition);
        
        // All positions ranked higher than me (lower index) beat me (no win)
        for (let i = 0; i < myIndex; i++) {
          const opponentPos = fullCall[i];
          if (opponentPos !== myPosition && POSITIONS.includes(opponentPos)) {
            const key = getMatchupKey(myPosition, opponentPos);
            initMatchup(key);
            matchups[key].total += 1;
            // No win (they beat me)
          }
        }
        
        // All positions ranked lower than me (higher index) lost to me (win)
        for (let i = myIndex + 1; i < fullCall.length; i++) {
          const opponentPos = fullCall[i];
          if (opponentPos !== myPosition && POSITIONS.includes(opponentPos)) {
            const key = getMatchupKey(myPosition, opponentPos);
            initMatchup(key);
            matchups[key].total += 1;
            matchups[key].wins += 1;
          }
        }
      } else {
        // Fallback: If we don't have full call, use points-based estimation
        // In BP, if I got N points, I beat (N) teams
        // We distribute wins proportionally across opponent positions
        const opponentPositions = POSITIONS.filter(p => p !== myPosition);
        
        if (opponentPositions.length === 0) {
          return;
        }
        
        // Number of teams I beat = my_points
        const teamsIBeat = myPoints;
        
        opponentPositions.forEach(opponentPos => {
          const key = getMatchupKey(myPosition, opponentPos);
          initMatchup(key);
          matchups[key].total += 1;
          
          // Distribute wins proportionally
          if (teamsIBeat > 0) {
            // Each opponent has equal chance of being beaten by me
            matchups[key].wins += teamsIBeat / opponentPositions.length;
          }
        });
      }
    });
    
    // Calculate win percentages
    Object.keys(matchups).forEach(key => {
      const [myPos, oppPos] = key.split('-');
      const data = matchups[key];
      if (data.total > 0) {
        const winRate = Math.round((data.wins / data.total) * 100 * 10) / 10;
        result[myPos][oppPos] = winRate;
      }
    });
    
    // Diagonal should be null (can't play against yourself)
    POSITIONS.forEach(pos => {
      result[pos][pos] = null;
    });
    
    return result;
  }
  
  /**
   * Render the heatmap with current data
   */
  function renderHeatmap(data) {
    if (!data) return;
    
    POSITIONS.forEach(rowPos => {
      POSITIONS.forEach(colPos => {
        const value = data[rowPos] ? data[rowPos][colPos] : null;
        updateCell(rowPos, colPos, value);
      });
    });
  }
  
  /**
   * Initialize the heatmap in a container element
   */
  function init(containerId, initialData) {
    container = document.getElementById(containerId);
    if (!container) {
      console.error('Heatmap container not found:', containerId);
      return;
    }
    
    // Create grid
    const grid = createGrid();
    container.innerHTML = '';
    container.appendChild(grid);
    
    // Initialize with data if provided
    if (initialData) {
      heatmapData = initialData;
      renderHeatmap(initialData);
    } else {
      // Calculate from full dataset if available
      if (typeof FilterState !== 'undefined') {
        const fullData = FilterState.getFilteredData();
        if (fullData && fullData.length > 0) {
          heatmapData = calculateHeatmap(fullData);
          if (heatmapData) {
            renderHeatmap(heatmapData);
          }
        }
      }
    }
  }
  
  /**
   * Update with new data (e.g., after filtering)
   */
  function update(newData) {
    heatmapData = newData;
    renderHeatmap(newData);
  }
  
  return {
    init,
    update,
    calculateHeatmap
  };
})();


// Track if callback is already registered to avoid duplicates
let callbackRegistered = false;

// Function to register filter callback
function registerFilterCallback() {
  // Only register once
  if (callbackRegistered) {
    return true;
  }
  
  if (typeof FilterState !== 'undefined') {
    FilterState.onFilterChange((filteredData, filterState) => {
      // Only update if container exists
      const container = document.getElementById('positional-heatmap');
      if (container) {
        // Calculate heatmap from filtered data (frontend calculation)
        const newHeatmapData = PositionalHeatmap.calculateHeatmap(filteredData);
        if (newHeatmapData) {
          PositionalHeatmap.update(newHeatmapData);
        } else {
          // No data - clear the heatmap
          const POSITIONS = ['OG', 'OO', 'CG', 'CO'];
          POSITIONS.forEach(rowPos => {
            POSITIONS.forEach(colPos => {
              const cell = document.getElementById(`heatmap-cell-${rowPos}-${colPos}`);
              if (cell) {
                cell.style.backgroundColor = '#1a1a2e';
                cell.style.color = '#888';
                cell.innerHTML = '<span style="font-size: 0.8em;">—</span>';
              }
            });
          });
        }
      }
    });
    callbackRegistered = true;
    return true;
  }
  return false;
}

// Initialize heatmap when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('positional-heatmap');
  if (container) {
    // Try to get initial data from page
    const dataElement = document.getElementById('heatmap_data');
    let initialData = null;
    
    if (dataElement) {
      try {
        initialData = JSON.parse(dataElement.textContent);
      } catch (e) {
        console.error('Failed to parse heatmap data:', e);
      }
    }
    
    PositionalHeatmap.init('positional-heatmap', initialData);
  }
  
  // Register with filter state - try multiple times if needed
  if (!registerFilterCallback()) {
    // If FilterState isn't available yet, try again after a short delay
    let attempts = 0;
    const maxAttempts = 10;
    const checkInterval = setInterval(() => {
      attempts++;
      if (registerFilterCallback() || attempts >= maxAttempts) {
        clearInterval(checkInterval);
      }
    }, 100);
  }
});

