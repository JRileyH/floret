/**
 * Plant Filter - Server-side filtering with HTMX
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeFilters();
});

function initializeFilters() {
    const filtersInput = document.getElementById('filters-json');
    const searchInput = document.getElementById('search-input');
    const nicheFilter = document.getElementById('niche-filter');
    const sunFilter = document.getElementById('sun-filter');
    const bloomFilter = document.getElementById('bloom-filter');
    const nativeFilter = document.getElementById('native-filter');
    const buyableFilter = document.getElementById('buyable-filter');
    const resetButton = document.getElementById('reset-filters');
    const heightMin = document.getElementById('height-min');
    const heightMax = document.getElementById('height-max');
    const spreadMin = document.getElementById('spread-min');
    const spreadMax = document.getElementById('spread-max');
    const colorSwatches = document.querySelectorAll('.filter-color-swatch');
    const featureIcons = document.querySelectorAll('.filter-feature-icon');

    // Initialize dropdowns
    const nicheFilterBtn = document.getElementById('niche-filter-btn');
    const nicheFilterText = document.getElementById('niche-filter-text');
    const nicheOptions = document.querySelectorAll('.niche-option');
    
    const sunFilterBtn = document.getElementById('sun-filter-btn');
    const sunFilterText = document.getElementById('sun-filter-text');
    const sunOptions = document.querySelectorAll('.sun-option');
    
    const bloomFilterBtn = document.getElementById('bloom-filter-btn');
    const bloomFilterText = document.getElementById('bloom-filter-text');
    const bloomOptions = document.querySelectorAll('.bloom-option');
    
    let activeFilters = {
        search: '',
        niche: '',
        sun: '',
        bloom: '',
        native: false,
        buyable: false,
        heightMin: null,
        heightMax: null,
        spreadMin: null,
        spreadMax: null,
        colors: [],
        features: []
    };

    let debounceTimer = null;

    function triggerFilterUpdate() {
        // Update hidden input with JSON-encoded filters
        filtersInput.value = JSON.stringify(activeFilters);
        
        // Debounce: wait 500ms after last change before triggering
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            // Trigger HTMX to reload plant list
            htmx.trigger(document.body, 'filterUpdate');
        }, 500);
    }

    // Niche dropdown handlers
    nicheOptions.forEach(option => {
        option.addEventListener('click', (e) => {
            e.preventDefault();
            const value = option.dataset.value;
            const text = option.textContent.trim();
            
            nicheFilter.value = value;
            nicheFilterText.textContent = text;
            
            nicheOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');
            
            if (nicheFilterBtn) {
                nicheFilterBtn.blur();
            }
            
            activeFilters.niche = value;
            triggerFilterUpdate();
        });
    });

    // Sun dropdown handlers
    sunOptions.forEach(option => {
        option.addEventListener('click', (e) => {
            e.preventDefault();
            const value = option.dataset.value;
            const text = option.textContent.trim();
            
            sunFilter.value = value;
            sunFilterText.textContent = text;
            
            sunOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');
            
            if (sunFilterBtn) {
                sunFilterBtn.blur();
            }
            
            activeFilters.sun = value;
            triggerFilterUpdate();
        });
    });

    // Bloom dropdown handlers
    bloomOptions.forEach(option => {
        option.addEventListener('click', (e) => {
            e.preventDefault();
            const value = option.dataset.value;
            const text = option.textContent.trim();
            
            bloomFilter.value = value;
            bloomFilterText.textContent = text;
            
            bloomOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');
            
            if (bloomFilterBtn) {
                bloomFilterBtn.blur();
            }
            
            activeFilters.bloom = value;
            triggerFilterUpdate();
        });
    });

    // Search input
    searchInput?.addEventListener('input', (e) => {
        activeFilters.search = e.target.value;
        triggerFilterUpdate();
    });

    // Checkbox filters
    nativeFilter?.addEventListener('change', (e) => {
        activeFilters.native = e.target.checked;
        triggerFilterUpdate();
    });

    buyableFilter?.addEventListener('change', (e) => {
        activeFilters.buyable = e.target.checked;
        triggerFilterUpdate();
    });

    // Number inputs
    heightMin?.addEventListener('input', (e) => {
        activeFilters.heightMin = e.target.value ? parseFloat(e.target.value) : null;
        triggerFilterUpdate();
    });

    heightMax?.addEventListener('input', (e) => {
        activeFilters.heightMax = e.target.value ? parseFloat(e.target.value) : null;
        triggerFilterUpdate();
    });

    spreadMin?.addEventListener('input', (e) => {
        activeFilters.spreadMin = e.target.value ? parseFloat(e.target.value) : null;
        triggerFilterUpdate();
    });

    spreadMax?.addEventListener('input', (e) => {
        activeFilters.spreadMax = e.target.value ? parseFloat(e.target.value) : null;
        triggerFilterUpdate();
    });

    // Color swatches
    colorSwatches.forEach(swatch => {
        swatch.addEventListener('click', () => {
            const colorId = swatch.dataset.color;
            const index = activeFilters.colors.indexOf(colorId);
            
            if (index > -1) {
                activeFilters.colors.splice(index, 1);
                swatch.classList.remove('active');
            } else {
                activeFilters.colors.push(colorId);
                swatch.classList.add('active');
            }
            triggerFilterUpdate();
        });
    });

    // Feature icons
    featureIcons.forEach(icon => {
        icon.addEventListener('click', () => {
            const featureId = icon.dataset.feature;
            const index = activeFilters.features.indexOf(featureId);
            
            if (index > -1) {
                activeFilters.features.splice(index, 1);
                icon.classList.remove('active');
            } else {
                activeFilters.features.push(featureId);
                icon.classList.add('active');
            }
            triggerFilterUpdate();
        });
    });

    // Reset button
    resetButton?.addEventListener('click', () => {
        // Reset form inputs
        searchInput.value = '';
        nicheFilter.value = '';
        sunFilter.value = '';
        bloomFilter.value = '';
        nativeFilter.checked = false;
        buyableFilter.checked = false;
        heightMin.value = '';
        heightMax.value = '';
        spreadMin.value = '';
        spreadMax.value = '';

        // Reset dropdowns
        if (nicheFilterText) {
            nicheFilterText.textContent = 'Any Niche';
        }
        nicheOptions.forEach(opt => {
            opt.classList.remove('active');
            if (opt.dataset.value === '') {
                opt.classList.add('active');
            }
        });
        
        if (sunFilterText) {
            sunFilterText.textContent = 'Any Sun';
        }
        sunOptions.forEach(opt => {
            opt.classList.remove('active');
            if (opt.dataset.value === '') {
                opt.classList.add('active');
            }
        });
        
        if (bloomFilterText) {
            bloomFilterText.textContent = 'Any Bloom Month';
        }
        bloomOptions.forEach(opt => {
            opt.classList.remove('active');
            if (opt.dataset.value === '') {
                opt.classList.add('active');
            }
        });

        // Reset color and feature selections
        colorSwatches.forEach(swatch => swatch.classList.remove('active'));
        featureIcons.forEach(icon => icon.classList.remove('active'));

        // Reset active filters
        activeFilters = {
            search: '',
            niche: '',
            sun: '',
            bloom: '',
            native: false,
            buyable: false,
            heightMin: null,
            heightMax: null,
            spreadMin: null,
            spreadMax: null,
            colors: [],
            features: []
        };

        triggerFilterUpdate();
    });
}
