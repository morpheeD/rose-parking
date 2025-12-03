/**
 * Parking Management System - Frontend Application
 * Handles real-time updates via WebSocket and user interactions
 */

// Socket.IO connection
const socket = io();

// DOM Elements
const elements = {
    occupiedCount: document.getElementById('occupiedCount'),
    availableCount: document.getElementById('availableCount'),
    maxCapacity: document.getElementById('maxCapacity'),
    occupancyPercent: document.getElementById('occupancyPercent'),
    occupancyFill: document.getElementById('occupancyFill'),
    occupancyStatus: document.getElementById('occupancyStatus'),
    totalEntries: document.getElementById('totalEntries'),
    totalExits: document.getElementById('totalExits'),
    lastUpdate: document.getElementById('lastUpdate'),
    connectionStatus: document.getElementById('connectionStatus'),
    configForm: document.getElementById('configForm'),
    maxCapacityInput: document.getElementById('maxCapacityInput'),
    resetBtn: document.getElementById('resetBtn')
};

// State
let currentStats = null;
let previousStats = null;
let pollInterval = null;

/**
 * Poll for changes every 5 seconds
 * Only reload page if entry/exit counts have changed
 */
function startPolling() {
    pollInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/stats');
            const newStats = await response.json();

            // Compare with previous stats
            if (previousStats &&
                (newStats.total_entries !== previousStats.total_entries ||
                    newStats.total_exits !== previousStats.total_exits)) {
                // There was a change, reload the page
                console.log('Parking event detected, reloading page...');
                location.reload();
            }

            previousStats = newStats;
        } catch (error) {
            console.error('Error polling stats:', error);
        }
    }, 5000); // 5 seconds
}

/**
 * Initialize application
 */
function init() {
    setupEventListeners();
    loadInitialData();
    startPolling(); // Start monitoring for changes
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Socket events
    socket.on('connect', handleConnect);
    socket.on('disconnect', handleDisconnect);
    socket.on('parking_update', handleParkingUpdate);

    // Form submission
    elements.configForm.addEventListener('submit', handleConfigSubmit);

    // Reset button
    elements.resetBtn.addEventListener('click', handleReset);
}

/**
 * Handle socket connection
 */
function handleConnect() {
    console.log('Connected to server');
    updateConnectionStatus(true);
    socket.emit('request_update');
}

/**
 * Handle socket disconnection
 */
function handleDisconnect() {
    console.log('Disconnected from server');
    updateConnectionStatus(false);
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const statusDot = elements.connectionStatus.querySelector('.status-dot');
    const statusText = elements.connectionStatus.querySelector('.status-text');

    if (connected) {
        statusDot.classList.add('connected');
        statusText.textContent = 'Connecté';
    } else {
        statusDot.classList.remove('connected');
        statusText.textContent = 'Déconnecté';
    }
}

/**
 * Load initial data from API
 */
async function loadInitialData() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        handleParkingUpdate(data);

        // Load config
        const configResponse = await fetch('/api/config');
        const configData = await configResponse.json();
        elements.maxCapacityInput.value = configData.max_capacity;
    } catch (error) {
        console.error('Error loading initial data:', error);
    }
}

/**
 * Handle parking update from WebSocket
 */
function handleParkingUpdate(data) {
    console.log('Parking update:', data);
    currentStats = data;

    // Update stats with animation
    updateStatValue(elements.occupiedCount, data.occupied);
    updateStatValue(elements.availableCount, data.available);
    updateStatValue(elements.maxCapacity, data.max_capacity);
    updateStatValue(elements.occupancyPercent, data.occupancy_percent + '%');

    // Update totals
    updateStatValue(elements.totalEntries, data.total_entries);
    updateStatValue(elements.totalExits, data.total_exits);

    // Update occupancy bar
    updateOccupancyBar(data.occupancy_percent);

    // Update status message
    updateStatusMessage(data.occupancy_percent, data.available);

    // Update timestamp
    updateTimestamp(data.timestamp);
}

/**
 * Update stat value with animation
 */
function updateStatValue(element, newValue) {
    if (element.textContent !== String(newValue)) {
        element.classList.add('updating');
        element.textContent = newValue;

        setTimeout(() => {
            element.classList.remove('updating');
        }, 500);
    }
}

/**
 * Update occupancy bar
 */
function updateOccupancyBar(percent) {
    const fill = elements.occupancyFill;

    // Update width
    fill.style.width = percent + '%';

    // Update color based on occupancy level
    fill.classList.remove('warning', 'danger');

    if (percent >= 90) {
        fill.classList.add('danger');
    } else if (percent >= 70) {
        fill.classList.add('warning');
    }
}

/**
 * Update status message
 */
function updateStatusMessage(percent, available) {
    const statusContainer = elements.occupancyStatus;
    const indicator = statusContainer.querySelector('.status-indicator');
    const message = statusContainer.querySelector('.status-message');

    // Remove existing classes
    indicator.classList.remove('warning', 'danger');

    // Update based on occupancy
    if (percent >= 90) {
        indicator.classList.add('danger');
        message.textContent = `Parking presque plein ! Seulement ${available} place(s) disponible(s)`;
    } else if (percent >= 70) {
        indicator.classList.add('warning');
        message.textContent = `Occupation élevée - ${available} place(s) disponible(s)`;
    } else if (percent > 0) {
        message.textContent = `Occupation normale - ${available} place(s) disponible(s)`;
    } else {
        message.textContent = 'Parking vide';
    }
}

/**
 * Update timestamp
 */
function updateTimestamp(isoString) {
    const date = new Date(isoString);
    const formatted = date.toLocaleString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    elements.lastUpdate.textContent = formatted;
}

/**
 * Handle config form submission
 */
async function handleConfigSubmit(e) {
    e.preventDefault();

    const maxCapacity = parseInt(elements.maxCapacityInput.value);

    if (maxCapacity < 1) {
        alert('La capacité doit être au moins 1');
        return;
    }

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                max_capacity: maxCapacity
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Configuration mise à jour avec succès', 'success');
        } else {
            showNotification('Erreur lors de la mise à jour', 'error');
        }
    } catch (error) {
        console.error('Error updating config:', error);
        showNotification('Erreur de connexion', 'error');
    }
}

/**
 * Handle reset button click
 */
async function handleReset() {
    if (!confirm('Êtes-vous sûr de vouloir réinitialiser le compteur à 0 ?')) {
        return;
    }

    try {
        const response = await fetch('/api/reset', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Compteur réinitialisé', 'success');
        } else {
            showNotification('Erreur lors de la réinitialisation', 'error');
        }
    } catch (error) {
        console.error('Error resetting count:', error);
        showNotification('Erreur de connexion', 'error');
    }
}

/**
 * Show notification (simple alert for now, can be enhanced)
 */
function showNotification(message, type) {
    // Simple implementation - can be enhanced with a toast library
    alert(message);
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
