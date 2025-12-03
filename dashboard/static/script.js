document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('parking-grid');
    const modal = document.getElementById('edit-modal');
    const closeModal = document.querySelector('.close-modal');
    const cancelBtn = document.getElementById('cancel-btn');
    const capacityForm = document.getElementById('capacity-form');

    // Modal elements
    const modalParkingName = document.getElementById('modal-parking-name');
    const modalParkingId = document.getElementById('modal-parking-id');
    const newCapacityInput = document.getElementById('new-capacity');

    // Fetch data every 2 seconds
    fetchData();
    setInterval(fetchData, 2000);

    function fetchData() {
        fetch('/api/dashboard/stats')
            .then(response => response.json())
            .then(data => {
                renderGrid(data);
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    function renderGrid(data) {
        // Clear grid if it was showing loading state
        if (grid.querySelector('.loading-state')) {
            grid.innerHTML = '';
        }

        data.forEach(lot => {
            let card = document.getElementById(`card-${lot.id}`);

            if (!card) {
                card = createCard(lot);
                grid.appendChild(card);
            }

            updateCard(card, lot);
        });
    }

    function createCard(lot) {
        const div = document.createElement('div');
        div.className = 'parking-card';
        div.id = `card-${lot.id}`;

        div.innerHTML = `
            <div class="card-header">
                <div>
                    <div class="parking-name">${lot.name}</div>
                    <div class="parking-url">${lot.url}</div>
                </div>
                <div class="status-badge status-${lot.status}">
                    ${lot.status === 'online' ? 'EN LIGNE' : 'HORS LIGNE'}
                </div>
            </div>
            
            <div class="content-area">
                <!-- Content injected by updateCard -->
            </div>
        `;

        return div;
    }

    function updateCard(card, lot) {
        const contentArea = card.querySelector('.content-area');
        const statusBadge = card.querySelector('.status-badge');

        // Update status
        statusBadge.className = `status-badge status-${lot.status}`;
        statusBadge.textContent = lot.status === 'online' ? 'EN LIGNE' : 'HORS LIGNE';

        if (lot.status === 'online' && lot.data) {
            const stats = lot.data;
            const percent = stats.occupancy_percent;

            // Determine color based on occupancy
            let colorClass = 'bg-green-500';
            let colorHex = '#10b981'; // green

            if (percent >= 90) {
                colorHex = '#ef4444'; // red
            } else if (percent >= 70) {
                colorHex = '#f59e0b'; // orange
            }

            contentArea.innerHTML = `
                <div class="stats-container">
                    <div class="stat-row">
                        <span>Places occupées</span>
                        <span class="stat-value">${stats.occupied}</span>
                    </div>
                    <div class="stat-row">
                        <span>Places disponibles</span>
                        <span class="stat-value">${stats.available}</span>
                    </div>
                    <div class="stat-row">
                        <span>Capacité totale</span>
                        <span class="stat-value">${stats.max_capacity}</span>
                    </div>
                </div>

                <div class="occupancy-display">
                    <div class="progress-bar-container">
                        <div class="progress-bar" style="width: ${percent}%; background-color: ${colorHex}"></div>
                    </div>
                    <div class="progress-text">
                        <span>Occupation</span>
                        <span style="color: ${colorHex}">${percent}%</span>
                    </div>
                </div>

                <div class="card-actions">
                    <button class="btn-edit" onclick="openEditModal('${lot.id}', '${lot.name}', ${stats.max_capacity})">
                        <i class="fa-solid fa-pen-to-square"></i> Modifier Capacité
                    </button>
                </div>
            `;
        } else {
            contentArea.innerHTML = `
                <div style="text-align: center; color: var(--text-secondary); padding: 20px;">
                    <i class="fa-solid fa-triangle-exclamation" style="font-size: 2rem; margin-bottom: 10px; color: var(--warning-color)"></i>
                    <p>Connexion impossible au parking</p>
                </div>
            `;
        }
    }

    // Modal functions
    window.openEditModal = function (id, name, currentCapacity) {
        modalParkingId.value = id;
        modalParkingName.textContent = name;
        newCapacityInput.value = currentCapacity;
        modal.classList.add('active');
    };

    function closeEditModal() {
        modal.classList.remove('active');
    }

    closeModal.addEventListener('click', closeEditModal);
    cancelBtn.addEventListener('click', closeEditModal);

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeEditModal();
        }
    });

    // Form submission
    capacityForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const id = modalParkingId.value;
        const capacity = newCapacityInput.value;
        const btn = capacityForm.querySelector('.btn-save');
        const originalText = btn.textContent;

        btn.textContent = 'Enregistrement...';
        btn.disabled = true;

        fetch('/api/dashboard/update_capacity', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id: id,
                capacity: parseInt(capacity)
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    closeEditModal();
                    fetchData(); // Refresh immediately
                } else {
                    alert('Erreur: ' + (data.error || 'Impossible de mettre à jour'));
                }
            })
            .catch(error => {
                alert('Erreur de communication');
                console.error(error);
            })
            .finally(() => {
                btn.textContent = originalText;
                btn.disabled = false;
            });
    });
});
