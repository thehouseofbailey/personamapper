/**
 * PersonaMap Client Library
 * A lightweight JavaScript library for interacting with the PersonaMap API
 * Designed for use with Google Tag Manager or direct website integration
 */

(function(window) {
    'use strict';

    // Configuration
    const CONFIG = {
        apiBaseUrl: window.PERSONAMAP_API_URL || '/api',
        sessionStorageKey: 'personamap_session',
        visitedPagesKey: 'personamap_visited_pages',
        predictedPersonaKey: 'personamap_predicted_persona',
        maxStoredPages: 50,
        debounceDelay: 1000,
        retryAttempts: 3,
        retryDelay: 1000
    };

    // Utility functions
    const utils = {
        // Simple debounce function
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Generate simple session ID
        generateSessionId: function() {
            return 'pm_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        },

        // Get current page URL (normalized)
        getCurrentUrl: function() {
            return window.location.href.split('?')[0].split('#')[0];
        },

        // Storage helpers
        getFromStorage: function(key, defaultValue = null) {
            try {
                const item = sessionStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                console.warn('PersonaMap: Error reading from storage:', e);
                return defaultValue;
            }
        },

        setToStorage: function(key, value) {
            try {
                sessionStorage.setItem(key, JSON.stringify(value));
            } catch (e) {
                console.warn('PersonaMap: Error writing to storage:', e);
            }
        },

        // HTTP request helper
        makeRequest: function(url, options = {}) {
            return new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                const method = options.method || 'GET';
                const headers = options.headers || {};
                
                xhr.open(method, url);
                
                // Set headers
                Object.keys(headers).forEach(key => {
                    xhr.setRequestHeader(key, headers[key]);
                });

                xhr.onload = function() {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        try {
                            const response = JSON.parse(xhr.responseText);
                            resolve(response);
                        } catch (e) {
                            reject(new Error('Invalid JSON response'));
                        }
                    } else {
                        reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
                    }
                };

                xhr.onerror = function() {
                    reject(new Error('Network error'));
                };

                xhr.ontimeout = function() {
                    reject(new Error('Request timeout'));
                };

                xhr.timeout = options.timeout || 10000;

                if (options.body) {
                    xhr.send(JSON.stringify(options.body));
                } else {
                    xhr.send();
                }
            });
        }
    };

    // Main PersonaMap class
    function PersonaMap(config = {}) {
        this.config = Object.assign({}, CONFIG, config);
        this.sessionId = this.getOrCreateSessionId();
        this.visitedPages = this.getVisitedPages();
        this.currentPagePersonas = null;
        this.predictedPersonas = null;
        this.callbacks = {
            onPagePersonas: [],
            onPersonaPrediction: [],
            onError: []
        };

        // Initialize debounced functions
        this.debouncedUpdatePrediction = utils.debounce(
            this.updatePersonaPrediction.bind(this), 
            this.config.debounceDelay
        );

        // Initialize
        this.init();
    }

    PersonaMap.prototype = {
        init: function() {
            // Track current page visit
            this.trackPageVisit();
            
            // Set up automatic page tracking for SPAs
            this.setupPageTracking();
        },

        getOrCreateSessionId: function() {
            let sessionId = utils.getFromStorage(this.config.sessionStorageKey);
            if (!sessionId) {
                sessionId = utils.generateSessionId();
                utils.setToStorage(this.config.sessionStorageKey, sessionId);
            }
            return sessionId;
        },

        getVisitedPages: function() {
            return utils.getFromStorage(this.config.visitedPagesKey, []);
        },

        saveVisitedPages: function() {
            // Keep only the most recent pages
            if (this.visitedPages.length > this.config.maxStoredPages) {
                this.visitedPages = this.visitedPages.slice(-this.config.maxStoredPages);
            }
            utils.setToStorage(this.config.visitedPagesKey, this.visitedPages);
        },

        trackPageVisit: function() {
            const currentUrl = utils.getCurrentUrl();
            const timestamp = Date.now();
            
            // Add to visited pages if not already the last entry
            if (this.visitedPages.length === 0 || 
                this.visitedPages[this.visitedPages.length - 1].url !== currentUrl) {
                
                this.visitedPages.push({
                    url: currentUrl,
                    timestamp: timestamp,
                    title: document.title
                });
                
                this.saveVisitedPages();
            }

            // Get personas for current page
            this.getPagePersonas(currentUrl);
            
            // Update persona prediction
            this.debouncedUpdatePrediction();
        },

        setupPageTracking: function() {
            // Track history changes for SPAs
            const originalPushState = history.pushState;
            const originalReplaceState = history.replaceState;
            const self = this;

            history.pushState = function() {
                originalPushState.apply(history, arguments);
                setTimeout(() => self.trackPageVisit(), 100);
            };

            history.replaceState = function() {
                originalReplaceState.apply(history, arguments);
                setTimeout(() => self.trackPageVisit(), 100);
            };

            window.addEventListener('popstate', function() {
                setTimeout(() => self.trackPageVisit(), 100);
            });
        },

        getPagePersonas: function(url, options = {}) {
            const params = new URLSearchParams({
                url: url || utils.getCurrentUrl(),
                min_confidence: options.minConfidence || 0.6,
                limit: options.limit || 10
            });

            const apiUrl = `${this.config.apiBaseUrl}/personas/page?${params}`;
            
            return utils.makeRequest(apiUrl)
                .then(response => {
                    this.currentPagePersonas = response;
                    this.triggerCallbacks('onPagePersonas', response);
                    return response;
                })
                .catch(error => {
                    this.triggerCallbacks('onError', error);
                    throw error;
                });
        },

        updatePersonaPrediction: function(options = {}) {
            if (this.visitedPages.length === 0) {
                return Promise.resolve(null);
            }

            const visitedUrls = this.visitedPages.map(page => page.url);
            const requestData = {
                visited_urls: visitedUrls,
                session_id: this.sessionId,
                min_confidence: options.minConfidence || 0.1,
                prediction_method: options.predictionMethod || 'weighted'
            };

            const apiUrl = `${this.config.apiBaseUrl}/personas/predict`;
            
            return utils.makeRequest(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: requestData
            })
            .then(response => {
                this.predictedPersonas = response;
                this.handlePersonaPrediction(response);
                this.triggerCallbacks('onPersonaPrediction', response);
                return response;
            })
            .catch(error => {
                this.triggerCallbacks('onError', error);
                throw error;
            });
        },

        handlePersonaPrediction: function(response) {
            if (!response || !response.predicted_personas || response.predicted_personas.length === 0) {
                return;
            }

            const topPersona = response.predicted_personas[0];
            const currentPrediction = {
                persona: topPersona.title,
                confidence: response.confidence,
                timestamp: Date.now(),
                session_id: response.session_id,
                pages_analyzed: response.pages_analyzed
            };

            // Get previous prediction from session storage
            const previousPrediction = utils.getFromStorage(this.config.predictedPersonaKey);

            // Check if prediction has changed
            const hasChanged = !previousPrediction || 
                previousPrediction.persona !== currentPrediction.persona ||
                Math.abs(previousPrediction.confidence - currentPrediction.confidence) > 0.05;

            if (hasChanged) {
                // Update session storage
                utils.setToStorage(this.config.predictedPersonaKey, currentPrediction);

                // Push to DataLayer
                this.pushToDataLayer(currentPrediction);

                // Log the change
                console.log('PersonaMap: Persona prediction updated', currentPrediction);
            }
        },

        pushToDataLayer: function(prediction) {
            // Initialize dataLayer if it doesn't exist
            window.dataLayer = window.dataLayer || [];

            // Push the prediction to dataLayer
            window.dataLayer.push({
                'event': 'personaPredictionUpdate',
                'predictedPersona': prediction.persona,
                'personaConfidence': prediction.confidence,
                'personaTimestamp': prediction.timestamp,
                'personaSessionId': prediction.session_id,
                'personaPagesAnalyzed': prediction.pages_analyzed
            });

            // Also push as a simple variable for easy access
            window.dataLayer.push({
                'predictedPersona': prediction.persona
            });
        },

        getCurrentPrediction: function() {
            return utils.getFromStorage(this.config.predictedPersonaKey);
        },

        // Event handling
        on: function(event, callback) {
            if (this.callbacks[event]) {
                this.callbacks[event].push(callback);
            }
        },

        off: function(event, callback) {
            if (this.callbacks[event]) {
                const index = this.callbacks[event].indexOf(callback);
                if (index > -1) {
                    this.callbacks[event].splice(index, 1);
                }
            }
        },

        triggerCallbacks: function(event, data) {
            if (this.callbacks[event]) {
                this.callbacks[event].forEach(callback => {
                    try {
                        callback(data);
                    } catch (e) {
                        console.error('PersonaMap callback error:', e);
                    }
                });
            }
        },

        // Public API methods
        getCurrentPagePersonas: function() {
            return this.currentPagePersonas;
        },

        getPredictedPersonas: function() {
            return this.predictedPersonas;
        },

        getSessionId: function() {
            return this.sessionId;
        },

        getVisitedPagesData: function() {
            return this.visitedPages.slice(); // Return copy
        },

        clearSession: function() {
            sessionStorage.removeItem(this.config.sessionStorageKey);
            sessionStorage.removeItem(this.config.visitedPagesKey);
            sessionStorage.removeItem(this.config.predictedPersonaKey);
            this.sessionId = this.getOrCreateSessionId();
            this.visitedPages = [];
            this.currentPagePersonas = null;
            this.predictedPersonas = null;
        },

        // Manual refresh methods
        refreshCurrentPage: function() {
            return this.getPagePersonas(utils.getCurrentUrl());
        },

        refreshPrediction: function() {
            return this.updatePersonaPrediction();
        }
    };

    // Static methods
    PersonaMap.isSupported = function() {
        return !!(window.sessionStorage && window.XMLHttpRequest);
    };

    // Export to global scope
    window.PersonaMap = PersonaMap;

    // Auto-initialize if configured
    if (window.PERSONAMAP_AUTO_INIT !== false) {
        document.addEventListener('DOMContentLoaded', function() {
            if (!window.personaMapInstance) {
                window.personaMapInstance = new PersonaMap();
            }
        });
    }

})(window);
