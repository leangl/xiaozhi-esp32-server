// Background image loading check
(function() {
    const backgroundContainer = document.getElementById('backgroundContainer');

    // Extract the background image URL
    let bgImageUrl = window.getComputedStyle(backgroundContainer).backgroundImage;
    const urlMatch = bgImageUrl && bgImageUrl.match(/url\(["']?(.*?)["']?\)/);
    
    if (!urlMatch || !urlMatch[1]) {
        console.warn('No valid background image URL found');
        return;
    }
    
    bgImageUrl = urlMatch[1];
    
    const bgImage = new Image();
    bgImage.onerror = function() {
        console.error('Background image failed to load:', bgImageUrl);
    };

    // Show model loading after the background loads
    bgImage.onload = function() {
        modelLoading.style.display = 'flex';
    };

    bgImage.src = bgImageUrl;
})();
