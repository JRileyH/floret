/**
 * Garden Summary
 * Fetches plant details from localStorage selections and displays analytics
 */

document.addEventListener('DOMContentLoaded', async () => {
    await loadGardenSummary();
});

async function loadGardenSummary() {
    // Load garden state from localStorage
    const gardenState = JSON.parse(localStorage.getItem('floret_garden_state') || '{"plants":[]}');
    
    if (!gardenState.plants || gardenState.plants.length === 0) {
        showEmptyState();
        return;
    }
    
    // Get API URL from data attribute
    const apiUrl = document.querySelector('[data-api-url]').dataset.apiUrl;
    
    // Fetch plant details from API
    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                plants: gardenState.plants.map(p => ({
                    plant_id: p.plant_id,
                    color_id: p.color_id
                }))
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.plants.length > 0) {
            renderSummary(data.plants);
        } else {
            showEmptyState();
        }
    } catch (error) {
        console.error('Failed to load garden summary:', error);
        showEmptyState();
    }
}

function renderSummary(plants) {
    document.getElementById('empty-state').classList.add('hidden');
    
    // Calculate stats
    const stats = calculateStats(plants);
    
    // Update stat cards
    document.querySelector('[data-summary-plants]').textContent = stats.plantCount;
    document.querySelector('[data-summary-colors]').textContent = stats.colorCount;
    document.querySelector('[data-summary-native]').textContent = stats.nativeCount;
    document.querySelector('[data-summary-niches]').textContent = `${stats.nicheCount}/6`;
    
    // Render sections
    renderColorPalette(stats.colors);
    renderFeatures(stats.features);
    renderHeightDistribution(plants);
    renderBloomCalendar(plants, stats.colors);
    renderPlantsList(plants);
}

function calculateStats(plants) {
    const colors = new Map();
    const niches = new Set();
    const features = new Map();
    let nativeCount = 0;
    
    plants.forEach(plant => {
        // Colors
        if (!colors.has(plant.color_id)) {
            colors.set(plant.color_id, {
                hex: plant.color_hex,
                name: plant.color_name
            });
        }
        
        // Niches
        if (plant.niche_id) {
            niches.add(plant.niche_id);
        }
        
        // Features
        plant.features.forEach(feature => {
            if (features.has(feature.id)) {
                features.get(feature.id).count++;
            } else {
                features.set(feature.id, {
                    name: feature.name,
                    icon: feature.icon,
                    count: 1
                });
            }
        });
        
        // Native
        if (plant.native) {
            nativeCount++;
        }
    });
    
    return {
        plantCount: plants.length,
        colorCount: colors.size,
        nativeCount,
        nicheCount: niches.size,
        colors: Array.from(colors.values()),
        features: Array.from(features.values()).sort((a, b) => b.count - a.count)
    };
}

function renderColorPalette(colors) {
    const container = document.getElementById('color-palette');
    container.innerHTML = colors.map(color => `
        <div class="tooltip" data-tip="${color.name}">
            <div class="w-12 h-12 rounded-lg shadow-md border-2 border-base-300"
                 style="background-color: ${color.hex}"></div>
        </div>
    `).join('');
}

function renderFeatures(features) {
    const container = document.getElementById('features-list');
    
    if (features.length === 0) {
        container.innerHTML = '<p class="text-sm text-base-content/70">No features selected</p>';
        return;
    }
    
    container.innerHTML = features.map(feature => `
        <div class="flex items-center justify-between bg-base-300 px-4 py-2 rounded-lg">
            <div class="flex items-center gap-2">
                ${feature.icon ? `<img src="${feature.icon}" alt="${feature.name}" class="w-5 h-5">` : ''}
                <span>${feature.name}</span>
            </div>
            <div class="badge badge-primary">${feature.count}</div>
        </div>
    `).join('');
}

function renderHeightDistribution(plants) {
    const container = document.getElementById('height-chart');
    
    // Group plants by height ranges
    const ranges = [
        { min: 0, max: 1, label: "0-1'" },
        { min: 1, max: 2, label: "1-2'" },
        { min: 2, max: 3, label: "2-3'" },
        { min: 3, max: 4, label: "3-4'" },
        { min: 4, max: 5, label: "4-5'" },
        { min: 5, max: 6, label: "5-6'" },
        { min: 6, max: Infinity, label: "6'+'" }
    ];
    
    const distribution = ranges.map(range => ({
        label: range.label,
        count: plants.filter(p => p.height !== null && p.height >= range.min && p.height < range.max).length
    }));
    
    const maxCount = Math.max(...distribution.map(d => d.count), 1);
    
    container.innerHTML = distribution.map(item => {
        const heightPercent = (item.count / maxCount) * 100;
        return `
            <div class="flex-1 flex flex-col items-center gap-2">
                <div class="w-full flex items-end justify-center" style="height: 160px;">
                    ${item.count > 0 ? `
                        <div class="w-full rounded-t-xl border-1 bg-base-300 border-neutral shadow-md"
                             style="height: ${heightPercent}%;"></div>
                    ` : ''}
                </div>
                <div class="text-center">
                    <div class="font-bold text-lg">${item.count}</div>
                    <div class="text-xs opacity-70">${item.label}</div>
                </div>
            </div>
        `;
    }).join('');
}

function renderBloomCalendar(plants, colors) {
    const container = document.getElementById('bloom-calendar');
    
    const months = [
        { key: 'jan', label: 'Jan' },
        { key: 'feb', label: 'Feb' },
        { key: 'mar', label: 'Mar' },
        { key: 'apr', label: 'Apr' },
        { key: 'may', label: 'May' },
        { key: 'jun', label: 'Jun' },
        { key: 'jul', label: 'Jul' },
        { key: 'aug', label: 'Aug' },
        { key: 'sep', label: 'Sep' },
        { key: 'oct', label: 'Oct' },
        { key: 'nov', label: 'Nov' },
        { key: 'dec', label: 'Dec' }
    ];
    
    // Build bloom data by month
    const bloomData = new Map();
    months.forEach(month => {
        bloomData.set(month.key, new Set());
    });
    
    plants.forEach(plant => {
        if (plant.bloom && Array.isArray(plant.bloom)) {
            plant.bloom.forEach(monthKey => {
                if (bloomData.has(monthKey)) {
                    bloomData.get(monthKey).add(plant.color_hex);
                }
            });
        }
    });
    
    container.innerHTML = months.map(month => {
        const colorSet = bloomData.get(month.key);
        const hasBloom = colorSet && colorSet.size > 0;
        
        return `
            <div class="bg-base-300 p-4 rounded-lg border-2 ${hasBloom ? 'border-primary' : 'border-transparent'}">
                <div class="font-semibold mb-2">${month.label}</div>
                <div class="flex flex-wrap gap-1">
                    ${hasBloom ? 
                        Array.from(colorSet).map(hex => 
                            `<div class="w-4 h-4 rounded-full shadow" style="background-color: ${hex}"></div>`
                        ).join('') 
                        : '<span class="text-xs opacity-50">—</span>'}
                </div>
            </div>
        `;
    }).join('');
}

function renderPlantsList(plants) {
    const container = document.getElementById('selected-plants-list');
    
    container.innerHTML = plants.map(plant => `
        <div class="bg-base-300 p-3 rounded-lg flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg shadow-md border-2 border-base-100"
                 style="background-color: ${plant.color_hex}"></div>
            <div class="flex-1">
                <div class="font-semibold">${plant.common_name} 🌸</div>
                <div class="text-xs italic opacity-70">${plant.scientific_name}</div>
            </div>
            <div class="text-sm opacity-70">${plant.color_name}</div>
        </div>
    `).join('');
}

function showEmptyState() {
    document.getElementById('empty-state').classList.remove('hidden');
    document.querySelectorAll('.grid').forEach(el => el.classList.add('hidden'));
}

function getCookie(name) {
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
