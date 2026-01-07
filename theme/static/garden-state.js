/**
 * Garden State Management
 * Manages garden plant selections in localStorage for unauthenticated users
 * Syncs with database for authenticated users
 */

class GardenState {
    constructor() {
        this.storageKey = 'floret_garden_state';
        this.state = this.load();
    }

    /**
     * Load garden state from localStorage
     * @returns {Object} Garden state with plants array, dimensions, and name
     */
    load() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                return JSON.parse(stored);
            }
            // Default garden state
            return {
                name: 'My Garden',
                width: 25,
                length: 10,
                plants: []
            };
        } catch (e) {
            console.error('Failed to load garden state:', e);
            return {
                name: 'My Garden',
                width: 25,
                length: 10,
                plants: []
            };
        }
    }

    /**
     * Save garden state to localStorage
     */
    save() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.state));
            this.updateSummary();
        } catch (e) {
            console.error('Failed to save garden state:', e);
        }
    }

    /**
     * Toggle a plant/color combination (add if not present, remove if present)
     * @param {string} plantId - Plant UUID
     * @param {string} colorId - Color UUID
     * @param {string} nicheId - Niche UUID (for summary calculation)
     */
    togglePlant(plantId, colorId, nicheId) {
        const index = this.state.plants.findIndex(
            p => p.plant_id === plantId && p.color_id === colorId
        );

        if (index >= 0) {
            // Remove if already selected
            this.state.plants.splice(index, 1);
        } else {
            // Add if not selected
            this.state.plants.push({
                plant_id: plantId,
                color_id: colorId,
                niche_id: nicheId,
                positions: []
            });
        }

        this.save();
    }

    /**
     * Check if a plant/color combination is selected
     * @param {string} plantId - Plant UUID
     * @param {string} colorId - Color UUID
     * @returns {boolean} Is selected
     */
    isSelected(plantId, colorId) {
        return this.state.plants.some(
            p => p.plant_id === plantId && p.color_id === colorId
        );
    }

    /**
     * Get total plant selection count
     * @returns {number} Total count of selected plant/color combinations
     */
    getTotalCount() {
        return this.state.plants.length;
    }

    /**
     * Get unique niche count
     * @returns {number} Unique niche count
     */
    getUniqueNicheCount() {
        const uniqueNiches = new Set(
            this.state.plants.map(p => p.niche_id).filter(Boolean)
        );
        return uniqueNiches.size;
    }

    /**
     * Update garden dimensions
     * @param {number} width - Garden width in feet
     * @param {number} length - Garden length in feet
     */
    updateDimensions(width, length) {
        this.state.width = parseFloat(width);
        this.state.length = parseFloat(length);
        this.save();
    }

    /**
     * Update garden name
     * @param {string} name - Garden name
     */
    updateName(name) {
        this.state.name = name;
        this.save();
    }

    /**
     * Add a position for a plant
     * @param {string} plantId - Plant UUID
     * @param {string} colorId - Color UUID
     * @param {number} x - X coordinate in feet
     * @param {number} y - Y coordinate in feet
     * @returns {number} Position index (for tracking)
     */
    addPosition(plantId, colorId, x, y) {
        const plant = this.state.plants.find(
            p => p.plant_id === plantId && p.color_id === colorId
        );

        if (plant) {
            plant.positions.push({ x, y });
            this.save();
            return plant.positions.length - 1;
        }

        return -1;
    }

    /**
     * Update a position for a plant
     * @param {string} plantId - Plant UUID
     * @param {string} colorId - Color UUID
     * @param {number} index - Position index
     * @param {number} x - X coordinate in feet
     * @param {number} y - Y coordinate in feet
     */
    updatePosition(plantId, colorId, index, x, y) {
        const plant = this.state.plants.find(
            p => p.plant_id === plantId && p.color_id === colorId
        );

        if (plant && plant.positions[index]) {
            plant.positions[index] = { x, y };
            this.save();
        }
    }

    /**
     * Remove a position for a plant
     * @param {string} plantId - Plant UUID
     * @param {string} colorId - Color UUID
     * @param {number} index - Position index
     */
    removePosition(plantId, colorId, index) {
        const plant = this.state.plants.find(
            p => p.plant_id === plantId && p.color_id === colorId
        );

        if (plant && plant.positions[index] !== undefined) {
            plant.positions.splice(index, 1);
            this.save();
        }
    }

    /**
     * Get all positions for a plant
     * @param {string} plantId - Plant UUID
     * @param {string} colorId - Color UUID
     * @returns {Array} Positions array
     */
    getPositions(plantId, colorId) {
        const plant = this.state.plants.find(
            p => p.plant_id === plantId && p.color_id === colorId
        );
        return plant ? plant.positions : [];
    }

    /**
     * Update the mini summary display
     */
    updateSummary() {
        const totalCount = this.getTotalCount();
        const nicheCount = this.getUniqueNicheCount();

        // Update total plants count
        const plantCountEl = document.querySelector('[data-garden-total]');
        if (plantCountEl) {
            plantCountEl.textContent = totalCount;
        }

        // Update niche count (format: X/6)
        const nicheCountEl = document.querySelector('[data-garden-niches]');
        if (nicheCountEl) {
            nicheCountEl.textContent = `${nicheCount}/6`;
        }

        // Update all color swatch states
        this.updateColorSwatches();
    }

    /**
     * Update all color swatch visual states
     */
    updateColorSwatches() {
        document.querySelectorAll('[data-plant-id]').forEach(card => {
            const plantId = card.dataset.plantId;
            card.querySelectorAll('[data-color-id]').forEach(swatch => {
                const colorId = swatch.dataset.colorId;
                const isSelected = this.isSelected(plantId, colorId);
                
                if (isSelected) {
                    swatch.classList.add('active');
                } else {
                    swatch.classList.remove('active');
                }
            });
        });
    }

    /**
     * Clear all selections
     */
    clear() {
        this.state = { plants: [] };
        this.save();
    }
}

// Initialize global garden state
window.gardenState = new GardenState();

// Delegate click events for garden color swatches
document.addEventListener('click', (e) => {
    const swatch = e.target.closest('.garden-color-swatch');
    if (swatch) {
        const plantCard = swatch.closest('[data-plant-id]');
        if (plantCard) {
            const plantId = plantCard.dataset.plantId;
            const colorId = swatch.dataset.colorId;
            const nicheId = swatch.dataset.plantNiche || '';
            window.gardenState.togglePlant(plantId, colorId, nicheId);
        }
    }
});

// Initialize summary on page load
document.addEventListener('DOMContentLoaded', () => {
    window.gardenState.updateSummary();
});

// Re-initialize after HTMX swaps new content
document.body.addEventListener('htmx:afterSwap', () => {
    window.gardenState.updateSummary();
});
