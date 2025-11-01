// Scripture Wallpaper Generator - Frontend JavaScript
// Handles user interactions, API calls, and image preview/download

// Tab Management
class TabManager {
    constructor() {
        this.initializeTabs();
    }

    initializeTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.getAttribute('data-tab');
                
                // Remove active class from all buttons and contents
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked button and corresponding content
                button.classList.add('active');
                document.getElementById(targetTab).classList.add('active');
            });
        });

        // Set default active tab (Canvas Editor)
        const defaultButton = document.querySelector('.tab-button[data-tab="canvas-tab"]');
        const defaultContent = document.getElementById('canvas-tab');
        if (defaultButton && defaultContent) {
            defaultButton.classList.add('active');
            defaultContent.classList.add('active');
        }
    }
}

class ScriptureWallpaperGenerator {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.currentImageBlob = null;
        this.currentFilename = null;
        
        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        this.form = document.getElementById('wallpaper-form');
        this.verseInput = document.getElementById('verse-input');
        this.versionSelect = document.getElementById('version-select');
        this.screenHeightInput = document.getElementById('screen-height');
        this.topBoundaryPercentInput = document.getElementById('top-boundary-percent');
        this.bottomBoundaryPercentInput = document.getElementById('bottom-boundary-percent');
        this.previewCanvas = document.getElementById('preview-canvas');
        this.textAreaInfo = document.getElementById('text-area-info');
        this.previewBtn = document.getElementById('preview-btn');
        this.downloadBtn = document.getElementById('download-btn');
        this.previewContainer = document.getElementById('preview-container');
        this.previewImage = document.getElementById('preview-image');
        this.previewPlaceholder = document.querySelector('.preview-placeholder');
        
        // Loading and error elements (fix variable naming)
        this.loadingEl = document.getElementById('loading');
        this.loadingDiv = this.loadingEl; // Keep both for compatibility
        this.errorEl = document.getElementById('error');
        this.errorDiv = this.errorEl; // Keep both for compatibility
        this.errorMessage = document.getElementById('error-message');
        this.resultDiv = document.getElementById('result');
        
        // Load static phone background image
        this.loadPhoneBackground();
    }

    bindEvents() {
        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit(e);
        });

        // Button events
        this.previewBtn.addEventListener('click', () => this.handlePreview());
        this.downloadBtn.addEventListener('click', () => this.handleDownload());

        // Input validation
        this.verseInput.addEventListener('input', () => this.validateInput());
        
        // Reactive preview updates
        this.screenHeightInput.addEventListener('input', () => this.updatePreview());
        this.topBoundaryPercentInput.addEventListener('input', () => this.updatePreview());
        this.bottomBoundaryPercentInput.addEventListener('input', () => this.updatePreview());
        this.verseInput.addEventListener('input', () => this.updatePreview());
        this.versionSelect.addEventListener('change', () => this.updatePreview());
    }

    validateInput() {
        const verse = this.verseInput.value.trim();
        if (verse.length === 0) {
            this.showError('Please enter a Bible reference');
            return false;
        } else {
            this.hideError();
            return true;
        }
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        if (!this.validateInput()) {
            return;
        }
        
        const verse = this.verseInput.value.trim();
        const version = this.versionSelect.value;
        
        try {
            this.showLoading();
            this.hideError();
            
            const blob = await this.fetchWallpaper(verse, version);
            
            if (blob) {
                this.showResult(blob);
            }
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }

    async handlePaste() {
        try {
            // Check if clipboard API is available
            if (!navigator.clipboard || !navigator.clipboard.readText) {
                this.showError('Clipboard access is not available in this browser. Please paste manually.');
                return;
            }

            const text = await navigator.clipboard.readText();
            if (text.trim()) {
                this.verseInput.value = text.trim();
                this.validateInput();
                
                // Visual feedback
                this.pasteBtn.style.background = 'rgba(74, 158, 255, 0.3)';
                setTimeout(() => {
                    this.pasteBtn.style.background = '';
                }, 200);
            }
        } catch (error) {
            console.error('Failed to read clipboard:', error);
            this.showError('Failed to access clipboard. Please ensure you have granted permission or paste manually.');
        }
    }

    async handlePreview() {
        const verse = this.verseInput.value.trim();
        const version = this.versionSelect.value;

        if (!verse) {
            this.showError('Please enter a Bible reference.');
            return;
        }

        try {
            this.showLoading();
            this.hideError();
            this.hidePreview();

            const { blob, filename } = await this.fetchWallpaper(verse, version);
            
            this.currentImageBlob = blob;
            this.currentFilename = filename;
            
            this.showPreview(blob);
            this.downloadBtn.disabled = false;
            
        } catch (error) {
            console.error('Preview failed:', error);
            this.showError(error.message || 'Failed to generate wallpaper. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    async handleDownload() {
        if (!this.currentImageBlob) {
            await this.handlePreview();
            return;
        }

        try {
            this.downloadImage(this.currentImageBlob, this.currentFilename);
        } catch (error) {
            console.error('Download failed:', error);
            this.showError('Failed to download image. Please try again.');
        }
    }

    async fetchWallpaper(verse, version) {
        // Construct API URL
        // Calculate pixel boundaries from percentages
        const screenHeight = parseInt(this.screenHeightInput.value);
        const topPercent = parseFloat(this.topBoundaryPercentInput.value);
        const bottomPercent = parseFloat(this.bottomBoundaryPercentInput.value);
        
        const topBoundary = Math.round(screenHeight * (topPercent / 100));
        const bottomBoundary = Math.round(screenHeight * ((100 - bottomPercent) / 100));
        
        const params = new URLSearchParams({
            q: verse,
            version: version,
            screen_height: screenHeight,
            top_boundary_percent: topPercent,
            bottom_boundary_percent: bottomPercent,
            top_boundary: topBoundary,
            bottom_boundary: bottomBoundary
        });
        
        const url = `${this.apiBaseUrl}?${params.toString()}`;
        
        // Make API request
        const response = await fetch(url);
        
        if (!response.ok) {
            let errorMessage = 'Failed to generate wallpaper';
            
            try {
                // Try to parse JSON error response
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch {
                // If not JSON, use status text
                errorMessage = `${response.status}: ${response.statusText}`;
            }
            
            throw new Error(errorMessage);
        }

        // Get the image blob
        const blob = await response.blob();
        
        // Extract filename from Content-Disposition header
        let filename = 'scripture-wallpaper.jpg';
        const contentDisposition = response.headers.get('Content-Disposition');
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }

        return { blob, filename };
    }

    downloadImage(blob, filename) {
        // Create object URL
        const url = URL.createObjectURL(blob);
        
        // Create temporary download link
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.style.display = 'none';
        
        // Trigger download
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        // Clean up object URL
        setTimeout(() => URL.revokeObjectURL(url), 100);
    }

    showPreview(blob) {
        const url = URL.createObjectURL(blob);
        this.previewImage.src = url;
        this.previewImage.onload = () => {
            // Clean up previous object URL
            if (this.previewImage.dataset.objectUrl) {
                URL.revokeObjectURL(this.previewImage.dataset.objectUrl);
            }
            this.previewImage.dataset.objectUrl = url;
        };
        
        this.previewContainer.classList.remove('hidden');
        this.previewPlaceholder.style.display = 'none';
    }

    hidePreview() {
        this.previewContainer.classList.add('hidden');
        this.previewPlaceholder.style.display = 'flex';
        
        // Clean up object URL
        if (this.previewImage.dataset.objectUrl) {
            URL.revokeObjectURL(this.previewImage.dataset.objectUrl);
            delete this.previewImage.dataset.objectUrl;
        }
        
        this.previewImage.src = '';
        this.currentImageBlob = null;
        this.currentFilename = null;
    }

    showLoading() {
        this.loadingEl.classList.remove('hidden');
        this.previewBtn.disabled = true;
    }

    hideLoading() {
        this.loadingEl.classList.add('hidden');
        this.previewBtn.disabled = false;
    }
    
    showResult(blob) {
        // Create download link
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `scripture-wallpaper-${Date.now()}.jpg`;
        
        // Create result display
        this.resultDiv.innerHTML = `
            <div class="result-content">
                <h3>Wallpaper Generated Successfully!</h3>
                <img src="${url}" alt="Generated Wallpaper" style="max-width: 200px; border-radius: 8px; margin: 1rem 0;">
                <br>
                <button onclick="this.parentElement.querySelector('a').click()" class="download-btn">
                    Download Wallpaper
                </button>
                <a href="${url}" download="scripture-wallpaper-${Date.now()}.jpg" style="display: none;"></a>
            </div>
        `;
        this.resultDiv.style.display = 'block';
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorEl.classList.remove('hidden');
    }

    hideError() {
        this.errorEl.classList.add('hidden');
        this.errorMessage.textContent = '';
    }
    
    loadPhoneBackground() {
        this.phoneBackgroundImage = new Image();
        this.phoneBackgroundImage.onload = () => {
            this.updatePreview();
        };
        this.phoneBackgroundImage.onerror = () => {
            console.log('Could not load phone background image');
        };
        this.phoneBackgroundImage.src = 'phone_home_wallpaper.jpeg';
    }
    
    updatePreview() {
         if (!this.phoneBackgroundImage) return;
         
         const canvas = this.previewCanvas;
         const ctx = canvas.getContext('2d');
         
         // Get boundary values
        const topPercentValue = parseFloat(this.topBoundaryPercentInput.value) || 31;
        const bottomPercentValue = parseFloat(this.bottomBoundaryPercentInput.value) || 38;
         const screenHeight = parseInt(this.screenHeightInput.value) || 2340;
         
         // Calculate actual pixel boundaries
         const topBoundaryPx = (topPercentValue / 100) * screenHeight;
         const bottomBoundaryPx = screenHeight - (bottomPercentValue / 100) * screenHeight;
         const textAreaHeight = bottomBoundaryPx - topBoundaryPx;
         
         // Update text area info
         this.textAreaInfo.textContent = `Text Area: ${Math.round(topBoundaryPx)}px - ${Math.round(bottomBoundaryPx)}px (${Math.round(textAreaHeight)}px height)`;
         
         // Set canvas size to Samsung S25 resolution proportions (1080x2340)
        const s25Width = 1080;
        const s25Height = 2340;
        const s25AspectRatio = s25Height / s25Width;
        
        // Scale down for preview while maintaining S25 proportions
        const canvasWidth = 400; // Base width for preview
        const canvasHeight = canvasWidth * s25AspectRatio;
         canvas.width = canvasWidth;
         canvas.height = canvasHeight;
         
         // Draw phone background
         ctx.drawImage(this.phoneBackgroundImage, 0, 0, canvasWidth, canvasHeight);
         
         // Calculate text area boundaries on canvas (scaled)
         const scale = canvasHeight / screenHeight;
         const canvasTopBoundary = topBoundaryPx * scale;
         const canvasBottomBoundary = bottomBoundaryPx * scale;
         const canvasTextAreaHeight = canvasBottomBoundary - canvasTopBoundary;
         
         // Draw text area rectangle
         ctx.strokeStyle = 'red';
         ctx.lineWidth = 2;
         ctx.strokeRect(0, canvasTopBoundary, canvasWidth, canvasTextAreaHeight);
         
         // Always show placeholder text preview - this is just for positioning
        this.showPlaceholderPreview(ctx, canvasTopBoundary, canvasBottomBoundary, canvasWidth);
     }
     
     showPlaceholderPreview(ctx, topBoundary, bottomBoundary, canvasWidth) {
         // Psalm 1:3 placeholder text
         const placeholderText = `He is like a tree
planted by streams of water,
that yields its fruit in its season,
and its leaf does not wither.
In all that he does, he prospers.`;
         
         // Set text style
         ctx.fillStyle = 'white';
         ctx.font = '10px Arial';
         ctx.textAlign = 'center';
         
         // Split text into lines and draw
         const lines = placeholderText.split('\n');
         const lineHeight = 12;
         const textAreaHeight = bottomBoundary - topBoundary;
         const totalTextHeight = lines.length * lineHeight;
         const startY = topBoundary + (textAreaHeight - totalTextHeight) / 2;
         
         lines.forEach((line, index) => {
             ctx.fillText(line.trim(), canvasWidth / 2, startY + (index * lineHeight));
         });
         
         // Reset text alignment
         ctx.textAlign = 'left';
     }
    
    async updateWallpaperOverlay() {
          const verse = this.verseInput.value.trim();
          if (!verse || !this.phoneBackgroundImage) return;
          
          try {
              // Use a debounce to avoid too many API calls
              clearTimeout(this.previewTimeout);
              this.previewTimeout = setTimeout(async () => {
                  const version = this.versionSelect.value;
                  const wallpaperBlob = await this.fetchWallpaper(verse, version);
                  
                  if (wallpaperBlob) {
                      const wallpaperImage = new Image();
                      wallpaperImage.onload = () => {
                          const canvas = this.previewCanvas;
                          const ctx = canvas.getContext('2d');
                          
                          // Redraw background first
                          const aspectRatio = this.phoneBackgroundImage.height / this.phoneBackgroundImage.width;
                          const canvasWidth = 300;
                          const canvasHeight = canvasWidth * aspectRatio;
                          canvas.width = canvasWidth;
                          canvas.height = canvasHeight;
                          ctx.drawImage(this.phoneBackgroundImage, 0, 0, canvasWidth, canvasHeight);
                          
                          // Draw wallpaper with some transparency over the background
                          ctx.globalAlpha = 0.9;
                          ctx.drawImage(wallpaperImage, 0, 0, canvas.width, canvas.height);
                          ctx.globalAlpha = 1.0;
                      };
                      
                      const url = URL.createObjectURL(wallpaperBlob);
                      wallpaperImage.src = url;
                  }
              }, 1500); // 1.5 second debounce
          } catch (error) {
              console.log('Preview update failed:', error);
          }
      }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TabManager();
    new ScriptureWallpaperGenerator();
});

// Handle page visibility changes to clean up resources
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Clean up any object URLs when page becomes hidden
        const previewImage = document.getElementById('preview-image');
        if (previewImage && previewImage.dataset.objectUrl) {
            URL.revokeObjectURL(previewImage.dataset.objectUrl);
            delete previewImage.dataset.objectUrl;
        }
    }
});

// Canvas Editor Class
class CanvasWallpaperEditor {
    constructor() {
        this.canvas = document.getElementById('wallpaper-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.currentVerse = '';
        this.currentReference = '';
        this.phoneBackgroundImage = null;
        
        // Set canvas size (full resolution)
        this.actualWidth = 1080;
        this.actualHeight = 2340;
        
        // Set canvas to full resolution
        this.canvas.width = this.actualWidth;
        this.canvas.height = this.actualHeight;
        
        this.initializeControls();
        this.bindEvents();
        this.loadPhoneBackground();
        this.renderCanvas();
    }
    
    initializeControls() {
        this.controls = {
            verseInput: document.getElementById('canvas-verse-input'),
            versionSelect: document.getElementById('canvas-version-select'),
            fetchBtn: document.getElementById('fetch-verse-btn'),
            pasteBtn: document.getElementById('paste-verse-btn'),
            fetchDownloadBtn: document.getElementById('fetch-download-btn'),
            topBoundary: document.getElementById('canvas-top-boundary'),
            topBoundaryValue: document.getElementById('canvas-top-boundary-value'),
            bottomBoundary: document.getElementById('canvas-bottom-boundary'),
            bottomBoundaryValue: document.getElementById('canvas-bottom-boundary-value'),
            fontSizeSlider: document.getElementById('canvas-font-size'),
            fontSizeValue: document.getElementById('canvas-font-size-value'),
            lineSpacingSlider: document.getElementById('canvas-line-spacing'),
            lineSpacingValue: document.getElementById('canvas-line-spacing-value'),
            downloadBtn: document.getElementById('download-canvas-btn'),
            resetBtn: document.getElementById('reset-canvas-btn')
        };
    }
    
    bindEvents() {
        // Fetch verse button
        this.controls.fetchBtn.addEventListener('click', () => this.fetchVerse());
        
        // Paste button
        this.controls.pasteBtn.addEventListener('click', () => this.pasteFromClipboard());
        
        // Download verse button
        this.controls.fetchDownloadBtn.addEventListener('click', () => this.fetchAndDownload());
        
        // Enter key on verse input
        this.controls.verseInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.fetchVerse();
        });
        
        // Boundary controls
        this.controls.topBoundary.addEventListener('input', (e) => {
            this.controls.topBoundaryValue.textContent = e.target.value + '%';
            this.renderCanvas();
        });
        
        this.controls.bottomBoundary.addEventListener('input', (e) => {
            this.controls.bottomBoundaryValue.textContent = e.target.value + '%';
            this.renderCanvas();
        });
        
        // Sliders with real-time updates
        this.controls.fontSizeSlider.addEventListener('input', (e) => {
            this.controls.fontSizeValue.textContent = e.target.value + 'px';
            this.renderCanvas();
        });
        
        this.controls.lineSpacingSlider.addEventListener('input', (e) => {
            this.controls.lineSpacingValue.textContent = e.target.value;
            this.renderCanvas();
        });
        
        // Action buttons
        this.controls.downloadBtn.addEventListener('click', () => this.downloadCanvas());
        this.controls.resetBtn.addEventListener('click', () => this.resetCanvas());
    }
    
    loadPhoneBackground() {
        this.phoneBackgroundImage = new Image();
        this.phoneBackgroundImage.src = 'phone_home_wallpaper.jpeg';
    }
    
    async pasteFromClipboard() {
        try {
            const text = await navigator.clipboard.readText();
            if (text.trim()) {
                this.controls.verseInput.value = text.trim();
            }
        } catch (err) {
            console.error('Failed to read clipboard:', err);
            // Fallback: focus the input for manual paste
            this.controls.verseInput.focus();
        }
    }
    
    async fetchVerse() {
        const verse = this.controls.verseInput.value.trim();
        const version = this.controls.versionSelect.value;
        if (!verse) return;
        
        try {
            this.controls.fetchBtn.textContent = 'Fetching and Previewing...';
            this.controls.fetchBtn.disabled = true;
            
            // Get current boundary settings to calculate optimal font size
            const topBoundaryPercent = parseFloat(this.controls.topBoundary.value);
            const bottomBoundaryPercent = parseFloat(this.controls.bottomBoundary.value);
            const screenHeight = 2340; // Default screen height
            
            // Calculate boundaries in pixels
            const topBoundaryPixels = Math.round(screenHeight * (topBoundaryPercent / 100));
            const bottomBoundaryPixels = Math.round(screenHeight * ((100 - bottomBoundaryPercent) / 100));
            
            // Use the new verse-data endpoint with boundary parameters
            const url = `http://localhost:8000/api/verse-data?q=${encodeURIComponent(verse)}&version=${version}&screen_height=${screenHeight}&top_boundary_percent=${topBoundaryPercent}&bottom_boundary_percent=${bottomBoundaryPercent}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Failed to fetch verse: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.currentVerse = data.text;
            this.currentReference = data.reference;
            
            // Set the font size slider to the optimal font size from API
            if (data.optimal_font_size) {
                const optimalSize = data.optimal_font_size;
                const minSize = Math.max(20, Math.round(optimalSize * 0.5)); // Ensure minimum is 20px
                const maxSize = Math.round(optimalSize * 2);
                
                // Update slider range
                this.controls.fontSizeSlider.min = minSize;
                this.controls.fontSizeSlider.max = maxSize;
                this.controls.fontSizeSlider.value = optimalSize;
                this.controls.fontSizeValue.textContent = optimalSize + 'px';
            }
            
            this.renderCanvas();
            
        } catch (error) {
            console.error('Error fetching verse:', error);
            alert('Failed to fetch verse. Please try again.');
        } finally {
            this.controls.fetchBtn.textContent = 'Fetch and Preview';
            this.controls.fetchBtn.disabled = false;
        }
    }
    
    async fetchAndDownload() {
        const verse = this.controls.verseInput.value.trim();
        const version = this.controls.versionSelect.value;
        if (!verse) return;
        
        try {
            this.controls.fetchDownloadBtn.textContent = 'Fetching and Downloading...';
            this.controls.fetchDownloadBtn.disabled = true;
            
            // Get current boundary settings to calculate optimal font size
            const topBoundaryPercent = parseFloat(this.controls.topBoundary.value);
            const bottomBoundaryPercent = parseFloat(this.controls.bottomBoundary.value);
            const screenHeight = 2340; // Default screen height
            
            // Calculate boundaries in pixels
            const topBoundaryPixels = Math.round(screenHeight * (topBoundaryPercent / 100));
            const bottomBoundaryPixels = Math.round(screenHeight * ((100 - bottomBoundaryPercent) / 100));
            
            // Use the new verse-data endpoint with boundary parameters
            const url = `http://localhost:8000/api/verse-data?q=${encodeURIComponent(verse)}&version=${version}&screen_height=${screenHeight}&top_boundary_percent=${topBoundaryPercent}&bottom_boundary_percent=${bottomBoundaryPercent}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Failed to fetch verse: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.currentVerse = data.text;
            this.currentReference = data.reference;
            
            // Set the font size slider to the optimal font size from API
            if (data.optimal_font_size) {
                const optimalSize = data.optimal_font_size;
                const minSize = Math.max(20, Math.round(optimalSize * 0.5)); // Ensure minimum is 20px
                const maxSize = Math.round(optimalSize * 2);
                
                // Update slider range
                this.controls.fontSizeSlider.min = minSize;
                this.controls.fontSizeSlider.max = maxSize;
                this.controls.fontSizeSlider.value = optimalSize;
                this.controls.fontSizeValue.textContent = optimalSize + 'px';
            }
            
            // Render the canvas first
            this.renderCanvas();
            
            // Then download it with readiness check
            setTimeout(() => {
                this.downloadCanvasWithReadyCheck();
            }, 100);
            
        } catch (error) {
            console.error('Error fetching verse:', error);
            alert('Failed to fetch verse. Please try again.');
        } finally {
            this.controls.fetchDownloadBtn.textContent = 'Fetch and Download';
            this.controls.fetchDownloadBtn.disabled = false;
        }
    }
    
    renderCanvas() {
        // Get canvas dimensions (full resolution)
        const canvasWidth = this.canvas.width;
        const canvasHeight = this.canvas.height;
        
        // Clear canvas with black background
        this.ctx.fillStyle = '#000000';
        this.ctx.fillRect(0, 0, canvasWidth, canvasHeight);
        
        if (!this.currentVerse) {
            // Show placeholder text (full resolution)
            this.ctx.fillStyle = '#666666';
            this.ctx.font = `300 48px "Montserrat", Arial, sans-serif`;
            this.ctx.textAlign = 'center';
            this.ctx.fillText('Enter a Bible verse above', canvasWidth / 2, canvasHeight / 2);
            return;
        }
        
        // Get current settings
        const topBoundaryPercent = parseFloat(this.controls.topBoundary.value);
        const bottomBoundaryPercent = parseFloat(this.controls.bottomBoundary.value);
        let currentFontSize = parseInt(this.controls.fontSizeSlider.value);
        const lineSpacing = parseFloat(this.controls.lineSpacingSlider.value);
        
        // Calculate text area boundaries (full resolution)
        const topBoundary = Math.round(canvasHeight * (topBoundaryPercent / 100));
        const bottomBoundary = Math.round(canvasHeight * ((100 - bottomBoundaryPercent) / 100));
        
        // Add boundary margins (full resolution)
        const boundaryMargin = 40;
        const textAreaTop = topBoundary + boundaryMargin;
        const textAreaBottom = bottomBoundary - boundaryMargin;
        const availableHeight = textAreaBottom - textAreaTop;
        
        // Set text properties with Montserrat Light (full resolution)
        this.ctx.fillStyle = '#ffffff';
        this.ctx.font = `300 ${currentFontSize}px "Montserrat", Arial, sans-serif`; // 300 = Light weight
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'top'; // Changed from 'middle' to 'top' for precise positioning
        
        // Calculate text area with margins (full resolution)
        const margin = 80;
        const maxWidth = canvasWidth - (margin * 2);
        let lines = this.wrapText(this.currentVerse, maxWidth);
        
        // Font size reduction logic (matching image generator exactly)
        let totalContentHeight;
        let actualLineHeight;
        let referenceHeight;
        let referenceFontSize;
        
        // Keep reducing font size until content fits (minimum 20px)
        while (currentFontSize > 20) {
            // Calculate text block height with current font size (full resolution)
            this.ctx.font = `300 ${currentFontSize}px "Montserrat", Arial, sans-serif`;
            const metrics = this.ctx.measureText('Ag');
            actualLineHeight = metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent;
            
            // Re-wrap text with current font size
            lines = this.wrapText(this.currentVerse, maxWidth);
            
            // Calculate verse height with proper line spacing (matching PIL logic)
            let verseHeight = actualLineHeight * lines.length;
            if (lines.length > 1) {
                verseHeight += actualLineHeight * (lineSpacing - 1) * (lines.length - 1);
            }
            
            // Reference uses same font size as verse
            referenceFontSize = currentFontSize;
            this.ctx.font = `300 ${referenceFontSize}px "Montserrat", Arial, sans-serif`;
            const refMetrics = this.ctx.measureText('Ag');
            referenceHeight = refMetrics.actualBoundingBoxAscent + refMetrics.actualBoundingBoxDescent;
            
            const spaceBetween = 40;
            totalContentHeight = verseHeight + spaceBetween + referenceHeight;
            
            // If content fits, break out of loop
            if (totalContentHeight <= availableHeight) {
                break;
            }
            
            // Reduce font size by 2px (matching image generator)
            currentFontSize -= 2;
        }

        // Center content within available area (matching image generator logic)
        const startY = textAreaTop + Math.floor((availableHeight - totalContentHeight) / 2);

        // Draw verse text with proper line spacing using calculated font size (full resolution)
        this.ctx.font = `300 ${currentFontSize}px "Montserrat", Arial, sans-serif`;
        let currentY = startY;
        lines.forEach((line, index) => {
            this.ctx.fillText(line, canvasWidth / 2, currentY);
            // Add line height + spacing for next line (but not for last line)
            if (index < lines.length - 1) {
                currentY += actualLineHeight + (actualLineHeight * (lineSpacing - 1));
            } else {
                currentY += actualLineHeight; // Just line height for last line
            }
        });
 
        // Draw reference with smaller font size (matching image generator)
        if (this.currentReference) {
            this.ctx.font = `300 ${referenceFontSize}px "Montserrat", Arial, sans-serif`;
            currentY += 40; // spaceBetween
            this.ctx.fillText(this.currentReference, canvasWidth / 2, currentY);
        }
    }
    
    wrapText(text, maxWidth) {
        const words = text.split(' ');
        const lines = [];
        let currentLine = '';
        
        for (let word of words) {
            const testLine = currentLine + (currentLine ? ' ' : '') + word;
            const metrics = this.ctx.measureText(testLine);
            
            if (metrics.width > maxWidth && currentLine) {
                lines.push(currentLine);
                currentLine = word;
            } else {
                currentLine = testLine;
            }
        }
        
        if (currentLine) {
            lines.push(currentLine);
        }
        
        return lines;
    }
    
    downloadCanvasWithReadyCheck() {
        if (!this.currentVerse) {
            alert('Please fetch a verse first!');
            return;
        }
        
        // Check if canvas is ready by verifying it has content
        const ctx = this.canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        
        // Check if canvas has any non-transparent pixels (indicating content)
        let hasContent = false;
        for (let i = 3; i < imageData.data.length; i += 4) { // Check alpha channel
            if (imageData.data[i] > 0) {
                hasContent = true;
                break;
            }
        }
        
        if (!hasContent) {
            // Canvas is not ready, wait for next animation frame and try again
            requestAnimationFrame(() => this.downloadCanvasWithReadyCheck());
            return;
        }
        
        // Canvas is ready, proceed with download
        this.downloadCanvas();
    }
    
    downloadCanvas() {
        if (!this.currentVerse) {
            alert('Please fetch a verse first!');
            return;
        }
        
        // Canvas is already at full resolution, so download directly
        this.canvas.toBlob((blob) => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `scripture-wallpaper-${this.currentReference.replace(/[^a-zA-Z0-9]/g, '-')}.png`;
            a.style.display = 'none';
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            setTimeout(() => URL.revokeObjectURL(url), 100);
        }, 'image/png', 1.0);
    }
    
    resetCanvas() {
        // Reset all controls to default values
        this.controls.verseInput.value = 'mt 16:16-18';
        this.controls.versionSelect.value = 'RSVCE - Revised Standard Version Catholic Edition';
        this.controls.topBoundary.value = '38';
        this.controls.topBoundaryValue.textContent = '38%';
        this.controls.bottomBoundary.value = '31';
        this.controls.bottomBoundaryValue.textContent = '31%';
        this.controls.fontSizeSlider.value = '64';
        this.controls.fontSizeValue.textContent = '64pt';
        this.controls.lineSpacingSlider.value = '1.4';
        this.controls.lineSpacingValue.textContent = '1.4';
        
        // Clear verse data
        this.currentVerse = '';
        this.currentReference = '';
        
        // Re-render canvas
        this.renderCanvas();
    }

}

// Initialize Canvas Editor when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const canvasEditor = new CanvasWallpaperEditor();
});