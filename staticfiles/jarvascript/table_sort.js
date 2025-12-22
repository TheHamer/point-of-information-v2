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
    function parseCellValue(cell, customSortOrder = null, forceStringSort = false) {
        // Check for data-sort-value attribute first (for cells with HTML that should sort by specific value)
        const sortValue = cell.getAttribute('data-sort-value');
        const text = sortValue ? sortValue.trim() : cell.textContent.trim();
        
        // If forced to string sort (e.g., for Comp column), return immediately
        if (forceStringSort) {
            return text.toLowerCase();
        }
        
        // If custom sort order is provided, use it
        if (customSortOrder) {
            return getPositionSortIndex(text, customSortOrder);
        }
        
        // Try parsing as number (only if it's a pure number, not mixed with text)
        const num = parseFloat(text);
        if (!isNaN(num) && text !== '' && /^-?\d*\.?\d+$/.test(text.trim())) {
            return num;
        }
        
        // Return as lowercase string for text comparison
        // Note: Date column uses data-sort-value with ISO format (YYYY-MM-DD) which sorts correctly as string
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
        
        // Force string sorting for Comp column to ensure alphabetical sorting
        const headerTextLower = headerText.toLowerCase();
        const forceStringSort = headerTextLower === 'comp';
        
        // Sort rows
        rows.sort((a, b) => {
            const aCell = a.cells[columnIndex];
            const bCell = b.cells[columnIndex];
            
            if (!aCell || !bCell) return 0;
            
            const aValue = parseCellValue(aCell, customSortOrder, forceStringSort);
            const bValue = parseCellValue(bCell, customSortOrder, forceStringSort);
            
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

