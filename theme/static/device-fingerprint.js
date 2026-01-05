function getDeviceFingerprint() {
    const signals = {
        // navigator.platform is deprecated but provides consistent values across browsers
        platform: navigator.platform || '',
        
        // GPU vendor normalized to consistent keyword
        webgl: normalizeGPU(getWebGLInfo()),

        // Hardware specs collected for display only, not used in device fingerprint
        hardwareConcurrency: navigator.hardwareConcurrency || '',
        deviceMemory: navigator.deviceMemory || '',
        
        // Volatile display fields (not used in fingerprint hash)
        screenResolution: `${screen.width}x${screen.height}`,
        screenColorDepth: screen.colorDepth,
        browserTimezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        language: navigator.language,
    };
    
    return signals;
}

function getWebGLInfo() {
    try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (!gl) return '';
        
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
            const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
            const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
            return `${vendor}|${renderer}`;
        }
        return '';
    } catch (e) {
        return '';
    }
}

function normalizeGPU(gpuString) {
    // Extract vendor keyword from WebGL info for consistent device identification
    if (!gpuString) return '';
    
    const lower = gpuString.toLowerCase();
    
    // Check for major vendors in order of specificity
    if (lower.includes('apple')) return 'Apple';
    if (lower.includes('nvidia')) return 'NVIDIA';
    if (lower.includes('amd')) return 'AMD';
    if (lower.includes('intel')) return 'Intel';
    if (lower.includes('qualcomm')) return 'Qualcomm';
    if (lower.includes('arm')) return 'ARM';
    
    // Fallback: return first 20 chars of original string
    return gpuString.substring(0, 20);
}

// Add fingerprint data to login form
document.addEventListener('DOMContentLoaded', function() {
    // Find login or signup forms (any form with email/password fields)
    const forms = document.querySelectorAll('form[method="post"]');
    
    if (!forms.length) return;
    
    const fingerprint = getDeviceFingerprint();
    
    // Add to all POST forms (login, signup, etc.)
    forms.forEach(form => {
        // Skip if already added (check for existing fingerprint field)
        if (form.querySelector('input[name="client_platform"]')) return;
        
        // Add hidden inputs for each signal
        Object.entries(fingerprint).forEach(([key, value]) => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = `client_${key}`;
            input.value = String(value);
            form.appendChild(input);
        });
    });
});
