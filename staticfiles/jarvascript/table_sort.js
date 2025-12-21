/**
 * Table Sorting Module
 * 
 * Handles column sorting for data tables.
 * Supports text, numbers, dates, and custom position sorting.
 */

(function() {
    'use strict';

    // Custom sort orders for positions
    const TEAM_POSITION_ORDER = ['OG', 'OO', 'CG', 'CO'];
    const SPEAKER_POSITION_ORDER = ['PM', 'DPM', 'LO', 'DLO', 'MG', 'GW', 'MO', 'OW'];

    /**
     * Get custom sort index for team or speaker positions
     */
    function getPositionSortIndex(text, orderArray) {
        const index = orderArray.indexOf(text);
        // If not found in order array, return a high number to sort to end
        return index === -1 ? 9999 : index;
    }

    /**
     * Parse cell value for sorting
     */
    function parseCellValue(cell, customSortOrder = null) {
        const text = cell.textContent.trim();
        
        // If custom sort order is provided, use it
        if (customSortOrder) {
            return getPositionSortIndex(text, customSortOrder);
        }
        
        // Try parsing as number
        const num = parseFloat(text);
        if (!isNaN(num) && text !== '') {
            return num;
        }
        
        // Try parsing as date
        const date = new Date(text);
        if (!isNaN(date.getTime())) {
            return date.getTime();
        }
        
        // Return as lowercase string for text comparison
        return text.toLowerCase();
    }

    /**
     * Get custom sort order for a column based on header text
     */
    function getCustomSortOrder(headerText) {
        const text = headerText.trim().toLowerCase();
        if (text === 'position') {
            return TEAM_POSITION_ORDER;
        }
        if (text === 'speaker') {
            return SPEAKER_POSITION_ORDER;
        }
        return null;
    }

    /**
     * Sort table rows
     */
    function sortTable(table, columnIndex, ascending) {
        const rows = Array.from(table.querySelectorAll('tr.data-row'));
        
        // Remove existing sort indicators
        const headers = table.querySelectorAll('th');
        headers.forEach(header => {
            header.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Add sort indicator to current column
        const currentHeader = headers[columnIndex];
        if (currentHeader) {
            currentHeader.classList.add(ascending ? 'sort-asc' : 'sort-desc');
        }
        
        // Get custom sort order if applicable
        const headerText = currentHeader ? currentHeader.textContent.trim() : '';
        const customSortOrder = getCustomSortOrder(headerText);
        
        // Sort rows
        rows.sort((a, b) => {
            const aCell = a.cells[columnIndex];
            const bCell = b.cells[columnIndex];
            
            if (!aCell || !bCell) return 0;
            
            const aValue = parseCellValue(aCell, customSortOrder);
            const bValue = parseCellValue(bCell, customSortOrder);
            
            if (aValue < bValue) return ascending ? -1 : 1;
            if (aValue > bValue) return ascending ? 1 : -1;
            return 0;
        });
        
        // Remove all data rows
        rows.forEach(row => row.remove());
        
        // Re-append sorted rows to the table
        rows.forEach(row => table.appendChild(row));
    }

    /**
     * Initialize table sorting
     */
    function initTableSorting() {
        const tables = document.querySelectorAll('.wide-speaks-table');
        
        tables.forEach(table => {
            const headers = table.querySelectorAll('th');
            const sortStates = {}; // Track sort state per column
            
            headers.forEach((header, index) => {
                // Skip non-sortable columns (buttons/actions)
                const headerText = header.textContent.trim().toLowerCase();
                if (headerText === 'motion' || headerText === 'include' || 
                    headerText === 'update' || headerText === 'delete') {
                    return;
                }
                
                // Make header clickable
                header.style.cursor = 'pointer';
                header.style.userSelect = 'none';
                header.classList.add('sortable');
                
                // Initialize sort state for this column
                sortStates[index] = true; // Start with ascending
                
                header.addEventListener('click', () => {
                    const ascending = sortStates[index];
                    sortTable(table, index, ascending);
                    sortStates[index] = !ascending; // Toggle for next click
                });
            });
        });
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTableSorting);
    } else {
        initTableSorting();
    }
})();

