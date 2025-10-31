// Scripture Wallpaper Generator - Frontend JavaScript
// Handles user interactions, API calls, and image preview/download

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