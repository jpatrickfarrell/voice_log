// Voice Log - Main JavaScript

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeMobileMenu();
    initializeSearch();
    initializeAudioPlayers();
    initializeForms();
});

// Mobile menu functionality
function initializeMobileMenu() {
    const mobileToggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            
            // Toggle icon
            const icon = this.querySelector('i');
            if (sidebar.classList.contains('show')) {
                icon.className = 'bi bi-x';
            } else {
                icon.className = 'bi bi-list';
            }
        });
        
        // Close sidebar when clicking outside
        document.addEventListener('click', function(e) {
            if (!sidebar.contains(e.target) && !mobileToggle.contains(e.target)) {
                sidebar.classList.remove('show');
                mobileToggle.querySelector('i').className = 'bi bi-list';
            }
        });
    }
}

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchClear = document.getElementById('searchClear');
    
    if (searchInput && searchClear) {
        searchInput.addEventListener('input', function() {
            if (this.value.length > 0) {
                searchClear.classList.remove('d-none');
            } else {
                searchClear.classList.add('d-none');
            }
            
            // Implement search functionality here
            performSearch(this.value);
        });
        
        searchClear.addEventListener('click', function() {
            searchInput.value = '';
            this.classList.add('d-none');
            clearSearch();
        });
        
        // Search on Enter key
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch(this.value);
            }
        });
    }
}

// Audio player enhancements
function initializeAudioPlayers() {
    const audioElements = document.querySelectorAll('audio');
    
    audioElements.forEach(audio => {
        // Add play event tracking
        audio.addEventListener('play', function() {
            const postSlug = this.dataset.postSlug;
            if (postSlug) {
                trackPlayEvent(postSlug);
            }
        });
        
        // Add custom controls
        enhanceAudioPlayer(audio);
    });
}

// Track play events for analytics
function trackPlayEvent(postSlug) {
    fetch(`/posts/increment-play/${postSlug}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    }).catch(err => console.log('Play tracking failed:', err));
}

// Enhance audio player with custom features
function enhanceAudioPlayer(audio) {
    const container = audio.parentElement;
    
    // Add loading state
    audio.addEventListener('loadstart', function() {
        container.classList.add('loading');
    });
    
    audio.addEventListener('canplay', function() {
        container.classList.remove('loading');
    });
    
    // Add error handling
    audio.addEventListener('error', function() {
        container.classList.add('error');
        console.error('Audio loading error:', this.error);
    });
}

// Form enhancements
function initializeForms() {
    // File upload progress
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(initializeFileUpload);
    
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(initializeAutoResize);
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(initializeFormValidation);
}

// File upload enhancements
function initializeFileUpload(fileInput) {
    // Only apply audio validation to inputs that are specifically for audio files
    if (fileInput.name === 'audio_file' || fileInput.accept && fileInput.accept.includes('audio')) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                validateAudioFile(file, this);
                showFilePreview(file, this);
            }
        });
    }
}

// Validate audio files
function validateAudioFile(file, input) {
    const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/mp4', 'audio/aac', 'audio/ogg', 'audio/webm'];
    const maxSize = 50 * 1024 * 1024; // 50MB
    
    let isValid = true;
    let errorMessage = '';
    
    if (!allowedTypes.includes(file.type)) {
        isValid = false;
        errorMessage = 'Please select a valid audio file (MP3, WAV, FLAC, M4A, AAC, OGG, WEBM)';
    } else if (file.size > maxSize) {
        isValid = false;
        errorMessage = 'File size must be less than 50MB';
    }
    
    // Show validation feedback
    const feedback = input.parentElement.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.textContent = errorMessage;
        input.classList.toggle('is-invalid', !isValid);
    } else if (!isValid) {
        showToast(errorMessage, 'error');
        input.value = '';
    }
    
    return isValid;
}

// Show file preview
function showFilePreview(file, input) {
    const preview = input.parentElement.querySelector('.file-preview');
    if (preview) {
        // Only show audio preview for audio files
        if (input.name === 'audio_file' || input.accept && input.accept.includes('audio')) {
            preview.innerHTML = `
                <div class="file-info">
                    <i class="bi bi-music-note-beamed"></i>
                    <div class="file-details">
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${formatFileSize(file.size)}</div>
                    </div>
                </div>
            `;
            preview.style.display = 'block';
        }
    }
}

// Auto-resize textareas
function initializeAutoResize(textarea) {
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    });
    
    // Initial resize
    textarea.dispatchEvent(new Event('input'));
}

// Form validation
function initializeFormValidation(form) {
    form.addEventListener('submit', function(e) {
        if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        form.classList.add('was-validated');
    });
}

// Search functionality
function performSearch(query) {
    if (query.length < 2) {
        clearSearch();
        return;
    }
    
    // Debounce search
    clearTimeout(window.searchTimeout);
    window.searchTimeout = setTimeout(() => {
        executeSearch(query);
    }, 300);
}

function executeSearch(query) {
    // This would typically make an API call to search posts
    console.log('Searching for:', query);
    
    // For now, just filter visible posts on the page
    const posts = document.querySelectorAll('.post-item');
    posts.forEach(post => {
        const title = post.querySelector('.post-title')?.textContent.toLowerCase() || '';
        const summary = post.querySelector('.post-summary')?.textContent.toLowerCase() || '';
        const searchText = title + ' ' + summary;
        
        if (searchText.includes(query.toLowerCase())) {
            post.style.display = '';
        } else {
            post.style.display = 'none';
        }
    });
}

function clearSearch() {
    const posts = document.querySelectorAll('.post-item');
    posts.forEach(post => {
        post.style.display = '';
    });
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to toast container or create one
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1070';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    // Show toast using Bootstrap
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    bsToast.show();
    
    // Remove from DOM after hiding
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Copy to clipboard functionality
function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast(successMessage, 'success');
        }).catch(err => {
            console.error('Failed to copy: ', err);
            showToast('Failed to copy to clipboard', 'error');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showToast(successMessage, 'success');
        } catch (err) {
            console.error('Failed to copy: ', err);
            showToast('Failed to copy to clipboard', 'error');
        }
        document.body.removeChild(textArea);
    }
}

// Share functionality
function sharePost(title, url) {
    if (navigator.share) {
        navigator.share({
            title: title,
            text: 'Check out this voice post on Voice Log',
            url: url
        }).catch(err => {
            console.log('Error sharing:', err);
            copyToClipboard(url, 'Link copied to clipboard!');
        });
    } else {
        copyToClipboard(url, 'Link copied to clipboard!');
    }
}

// Post processing functionality
function processPost(slug) {
    const button = document.querySelector(`[data-process-slug="${slug}"]`);
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="bi bi-hourglass-split"></i> Processing...';
    }
    
    fetch(`/posts/process/${slug}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Post processed successfully!', 'success');
            
            // Update transcript if available
            if (data.transcript) {
                const transcriptElement = document.getElementById('transcript');
                if (transcriptElement) {
                    transcriptElement.textContent = data.transcript;
                }
            }
            
            // Update summary if available
            if (data.summary) {
                const summaryElement = document.getElementById('summary');
                if (summaryElement) {
                    summaryElement.textContent = data.summary;
                }
            }
            
            // Suggest title update
            if (data.suggested_title && confirm(`Update title to "${data.suggested_title}"?`)) {
                const titleInput = document.getElementById('title');
                if (titleInput) {
                    titleInput.value = data.suggested_title;
                }
            }
            
            // Hide process button
            if (button) {
                button.style.display = 'none';
            }
        } else {
            showToast(`Processing failed: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Processing error:', error);
        showToast('Processing failed. Please try again.', 'error');
    })
    .finally(() => {
        if (button) {
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-cpu"></i> Process';
        }
    });
}

// Quick upload functionality for mobile
function quickUpload(file, privacy = 'public') {
    const formData = new FormData();
    formData.append('audio', file);
    formData.append('privacy_level', privacy);
    
    return fetch('/posts/upload-quick', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Upload successful!', 'success');
            return data;
        } else {
            throw new Error(data.error);
        }
    })
    .catch(error => {
        showToast(`Upload failed: ${error.message}`, 'error');
        throw error;
    });
}

// Export functions for use in other scripts
window.VoiceLog = {
    showToast,
    copyToClipboard,
    sharePost,
    processPost,
    quickUpload,
    formatFileSize,
    formatDuration
};