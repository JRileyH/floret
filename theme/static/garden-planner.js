/**
 * Garden Planner
 * Interactive canvas for placing plants in a garden layout
 */

class GardenPlanner {
    constructor() {
        this.canvas = document.getElementById('garden-canvas');
        if (!this.canvas) return;

        this.ctx = this.canvas.getContext('2d');
        this.gardenState = window.gardenState;
        
        // Canvas dimensions
        this.canvasWidth = 800;
        this.canvasHeight = 400;
        
        // Plant data (fetched from API)
        this.plantsData = new Map();
        
        // Drag state
        this.draggedPlant = null;
        this.dragOffset = { x: 0, y: 0 };
        
        // View mode
        this.viewMode = 'bloom'; // 'bloom' or 'topographical'
        
        this.init();
    }

    async init() {
        // Load dimensions from localStorage
        this.updateDimensionsFromStorage();
        
        // Load plant data from API
        await this.loadPlantData();
        
        // Render plant cards
        this.renderPlantCards();
        
        // Draw canvas
        this.draw();
        
        // Event listeners
        this.setupEventListeners();
    }

    updateDimensionsFromStorage() {
        const state = this.gardenState.state;
        document.getElementById('garden-name').value = state.name || 'My Garden';
        document.getElementById('garden-width').value = state.width || 25;
        document.getElementById('garden-length').value = state.length || 10;
    }

    setupEventListeners() {
        // Dimension inputs
        document.getElementById('garden-name').addEventListener('input', (e) => {
            this.gardenState.updateName(e.target.value);
        });

        document.getElementById('garden-width').addEventListener('input', (e) => {
            this.gardenState.updateDimensions(
                parseFloat(e.target.value),
                parseFloat(document.getElementById('garden-length').value)
            );
            this.draw();
        });

        document.getElementById('garden-length').addEventListener('input', (e) => {
            this.gardenState.updateDimensions(
                parseFloat(document.getElementById('garden-width').value),
                parseFloat(e.target.value)
            );
            this.draw();
        });

        // Canvas mouse events
        this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
        this.canvas.addEventListener('dblclick', (e) => this.onDoubleClick(e));

        // Save button
        document.getElementById('save-garden-btn').addEventListener('click', () => {
            this.saveGarden();
        });

        // View mode toggle
        document.getElementById('view-mode-toggle').addEventListener('click', () => {
            this.toggleViewMode();
        });

        // Plant filters (min/max range)
        ['filter-height-min', 'filter-height-max', 'filter-spread-min', 'filter-spread-max'].forEach(id => {
            document.getElementById(id).addEventListener('input', () => {
                this.renderPlantCards();
            });
        });
    }

    async loadPlantData() {
        const state = this.gardenState.state;
        if (!state.plants || state.plants.length === 0) {
            return;
        }

        try {
            const apiUrl = document.querySelector('[data-plants-url]').dataset.plantsUrl;
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    plants: state.plants.map(p => ({
                        plant_id: p.plant_id,
                        color_id: p.color_id
                    }))
                })
            });

            const data = await response.json();
            if (data.success && data.plants) {
                data.plants.forEach(plant => {
                    const key = `${plant.plant_id}_${plant.color_id}`;
                    this.plantsData.set(key, plant);
                });
            }
        } catch (error) {
            console.error('Failed to load plant data:', error);
        }
    }

    renderPlantCards() {
        const container = document.getElementById('plant-cards-container');
        const emptyMessage = document.getElementById('empty-plants-message');
        const state = this.gardenState.state;

        if (!state.plants || state.plants.length === 0) {
            container.innerHTML = '';
            emptyMessage.classList.remove('hidden');
            return;
        }

        // Get filter values (min/max ranges)
        const minHeight = parseFloat(document.getElementById('filter-height-min').value) || 0;
        const maxHeight = parseFloat(document.getElementById('filter-height-max').value) || Infinity;
        const minSpread = parseFloat(document.getElementById('filter-spread-min').value) || 0;
        const maxSpread = parseFloat(document.getElementById('filter-spread-max').value) || Infinity;

        emptyMessage.classList.add('hidden');

        const filteredPlants = state.plants.filter(plant => {
            const key = `${plant.plant_id}_${plant.color_id}`;
            const plantData = this.plantsData.get(key);
            
            if (!plantData) return false;
            
            // Apply range filters
            const height = plantData.height || 0;
            const spread = plantData.spread || 0;
            
            if (height < minHeight || height > maxHeight) return false;
            if (spread < minSpread || spread > maxSpread) return false;
            
            return true;
        });

        container.innerHTML = filteredPlants.map(plant => {
            const key = `${plant.plant_id}_${plant.color_id}`;
            const plantData = this.plantsData.get(key);
            
            if (!plantData) return '';

            const count = plant.positions ? plant.positions.length : 0;
            const heightStr = plantData.height ? `${plantData.height}'` : 'N/A';
            const spreadStr = plantData.spread ? `${plantData.spread}'` : 'N/A';

            return `
                <div class="card bg-base-100 shadow-md hover:shadow-lg transition-shadow">
                    <div class="card-body p-4">
                        <div class="w-full h-16 rounded-lg mb-2 border-2 border-base-300"
                             style="background-color: ${plantData.color_hex}"></div>
                        <h3 class="font-semibold text-sm line-clamp-2">${plantData.common_name}</h3>
                        <div class="text-xs opacity-70 mt-1">
                            <div>H: ${heightStr} × S: ${spreadStr}</div>
                        </div>
                        <div class="flex items-center justify-between mt-2">
                            <span class="text-xs opacity-70">${count} placed</span>
                            <button class="btn btn-circle btn-sm btn-primary"
                                    data-add-plant="${plant.plant_id}"
                                    data-add-color="${plant.color_id}">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Add click listeners for add buttons
        container.querySelectorAll('[data-add-plant]').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const plantId = e.currentTarget.dataset.addPlant;
                const colorId = e.currentTarget.dataset.addColor;
                await this.addPlantToCanvas(plantId, colorId);
            });
        });
    }

    async addPlantToCanvas(plantId, colorId) {
        const state = this.gardenState.state;
        const centerX = state.width / 2;
        const centerY = state.length / 2;

        this.gardenState.addPosition(plantId, colorId, centerX, centerY);
        
        // Reload plant data to ensure we have it for rendering
        await this.loadPlantData();
        
        this.draw();
        this.renderPlantCards();
    }

    toggleViewMode() {
        this.viewMode = this.viewMode === 'bloom' ? 'topographical' : 'bloom';
        
        // Update button text
        const btn = document.getElementById('view-mode-toggle');
        btn.textContent = this.viewMode === 'bloom' ? '🗻 Topographical' : '🌸 Bloom Color';
        
        this.draw();
    }

    draw() {
        this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
        
        this.drawGrid();
        this.drawPlants();
    }

    drawGrid() {
        const state = this.gardenState.state;
        const gardenWidth = state.width || 25;
        const gardenLength = state.length || 10;

        // Calculate scale to fit canvas
        const scaleX = this.canvasWidth / gardenWidth;
        const scaleY = this.canvasHeight / gardenLength;
        this.scale = Math.min(scaleX, scaleY) * 0.9; // 90% to leave padding

        // Calculate offsets to center the garden
        this.offsetX = (this.canvasWidth - (gardenWidth * this.scale)) / 2;
        this.offsetY = (this.canvasHeight - (gardenLength * this.scale)) / 2;

        // Draw grid lines every foot
        this.ctx.strokeStyle = '#d4e8d4';
        this.ctx.lineWidth = 1;

        // Vertical lines
        for (let x = 0; x <= gardenWidth; x++) {
            const canvasX = this.offsetX + (x * this.scale);
            this.ctx.beginPath();
            this.ctx.moveTo(canvasX, this.offsetY);
            this.ctx.lineTo(canvasX, this.offsetY + (gardenLength * this.scale));
            this.ctx.stroke();
        }

        // Horizontal lines
        for (let y = 0; y <= gardenLength; y++) {
            const canvasY = this.offsetY + (y * this.scale);
            this.ctx.beginPath();
            this.ctx.moveTo(this.offsetX, canvasY);
            this.ctx.lineTo(this.offsetX + (gardenWidth * this.scale), canvasY);
            this.ctx.stroke();
        }

        // Draw border
        this.ctx.strokeStyle = '#5b855b';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(
            this.offsetX,
            this.offsetY,
            gardenWidth * this.scale,
            gardenLength * this.scale
        );
    }

    drawPlants() {
        const state = this.gardenState.state;
        
        state.plants.forEach(plant => {
            const key = `${plant.plant_id}_${plant.color_id}`;
            const plantData = this.plantsData.get(key);
            
            if (!plantData || !plant.positions) return;

            plant.positions.forEach((pos, index) => {
                this.drawPlantCircle(plantData, pos.x, pos.y, plant.plant_id, plant.color_id, index);
            });
        });
    }

    drawPlantCircle(plantData, gardenX, gardenY, plantId, colorId, posIndex) {
        // Convert garden coordinates to canvas coordinates
        const canvasX = this.offsetX + (gardenX * this.scale);
        const canvasY = this.offsetY + (gardenY * this.scale);

        // Calculate radius based on plant spread (spread is diameter/width, so divide by 2)
        const spread = plantData.spread || 1;
        const radius = (spread / 2) * this.scale;

        // Determine fill color based on view mode
        let fillColor, strokeColor, showLabel = true;
        if (this.viewMode === 'topographical') {
            // Topographical mode: gradient from light to dark based on height (0-8 feet scale)
            const height = Math.min(plantData.height || 0, 8); // Cap at 8 feet
            const intensity = height / 8; // 0-1 scale
            
            // More dramatic gradient: light gray-green to very dark green
            const r = Math.round(200 - (200 - 20) * intensity); // 200 -> 20 (much wider range)
            const g = Math.round(220 - (220 - 50) * intensity); // 220 -> 50
            const b = Math.round(200 - (200 - 20) * intensity); // 200 -> 20
            const alpha = 0.2 + (intensity * 0.7); // 0.2 to 0.9 transparency (wider range)
            
            fillColor = `rgba(${r}, ${g}, ${b}, ${alpha})`;
            strokeColor = 'transparent';
            showLabel = false;
        } else {
            // Bloom color mode: use plant's bloom color
            fillColor = plantData.color_hex + '66'; // Add transparency
            strokeColor = plantData.color_hex;
        }

        // Draw circle
        this.ctx.fillStyle = fillColor;
        this.ctx.beginPath();
        this.ctx.arc(canvasX, canvasY, radius, 0, 2 * Math.PI);
        this.ctx.fill();

        // Draw border (only in bloom mode)
        if (strokeColor !== 'transparent') {
            this.ctx.strokeStyle = strokeColor;
            this.ctx.lineWidth = 2;
            this.ctx.stroke();
        }

        // Draw label (only in bloom mode)
        if (showLabel) {
            this.ctx.fillStyle = '#000000';
            this.ctx.strokeStyle = '#ffffff';
            this.ctx.lineWidth = 3;
            this.ctx.font = '12px sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            
            const label = plantData.common_name;
            this.ctx.strokeText(label, canvasX, canvasY);
            this.ctx.fillText(label, canvasX, canvasY);
        }
    }

    onMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;

        // Find plant at this position
        const plant = this.findPlantAtPosition(canvasX, canvasY);
        
        if (plant) {
            this.draggedPlant = plant;
            const gardenCoords = this.canvasToGarden(canvasX, canvasY);
            this.dragOffset.x = gardenCoords.x - plant.position.x;
            this.dragOffset.y = gardenCoords.y - plant.position.y;
        }
    }

    onMouseMove(e) {
        if (!this.draggedPlant) return;

        const rect = this.canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;

        const gardenCoords = this.canvasToGarden(canvasX, canvasY);
        const newX = gardenCoords.x - this.dragOffset.x;
        const newY = gardenCoords.y - this.dragOffset.y;

        // Update temporary position
        this.draggedPlant.position.x = newX;
        this.draggedPlant.position.y = newY;

        this.draw();
    }

    onMouseUp(e) {
        if (!this.draggedPlant) return;

        // Save final position to localStorage
        this.gardenState.updatePosition(
            this.draggedPlant.plantId,
            this.draggedPlant.colorId,
            this.draggedPlant.posIndex,
            this.draggedPlant.position.x,
            this.draggedPlant.position.y
        );

        this.draggedPlant = null;
        this.draw();
    }

    onDoubleClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;

        const plant = this.findPlantAtPosition(canvasX, canvasY);
        
        if (plant) {
            this.gardenState.removePosition(plant.plantId, plant.colorId, plant.posIndex);
            this.draw();
            this.renderPlantCards();
        }
    }

    findPlantAtPosition(canvasX, canvasY) {
        const state = this.gardenState.state;
        
        for (const plant of state.plants) {
            const key = `${plant.plant_id}_${plant.color_id}`;
            const plantData = this.plantsData.get(key);
            
            if (!plantData || !plant.positions) continue;

            for (let i = plant.positions.length - 1; i >= 0; i--) {
                const pos = plant.positions[i];
                const plantCanvasX = this.offsetX + (pos.x * this.scale);
                const plantCanvasY = this.offsetY + (pos.y * this.scale);
                const spread = plantData.spread || 1;
                const radius = (spread / 2) * this.scale;

                const distance = Math.sqrt(
                    Math.pow(canvasX - plantCanvasX, 2) +
                    Math.pow(canvasY - plantCanvasY, 2)
                );

                if (distance <= radius) {
                    return {
                        plantId: plant.plant_id,
                        colorId: plant.color_id,
                        posIndex: i,
                        position: pos,
                        data: plantData
                    };
                }
            }
        }

        return null;
    }

    canvasToGarden(canvasX, canvasY) {
        return {
            x: (canvasX - this.offsetX) / this.scale,
            y: (canvasY - this.offsetY) / this.scale
        };
    }

    async saveGarden() {
        const saveBtn = document.getElementById('save-garden-btn');
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';

        try {
            const saveUrl = document.querySelector('[data-save-url]').dataset.saveUrl;
            const response = await fetch(saveUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(this.gardenState.state)
            });

            // Check if response is OK before parsing JSON
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    alert('You must be logged in to save a garden.');
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                alert('Garden saved successfully!');
                // Update garden ID in localStorage if this was a new garden
                if (data.garden_id && !this.gardenState.state.garden_id) {
                    this.gardenState.state.garden_id = data.garden_id;
                    this.gardenState.save();
                }
            } else {
                alert('Failed to save garden: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Save error:', error);
            alert('Failed to save garden. Please try again.');
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save Garden';
        }
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    new GardenPlanner();
});
