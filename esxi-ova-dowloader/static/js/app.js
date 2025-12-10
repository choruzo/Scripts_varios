// ESXi OVA Downloader - JavaScript Frontend

// Estado de la aplicación
const app = {
    connected: false,
    vms: [],
    selectedVms: new Set(),
    filters: {
        host: '',
        cluster: '',
        power_state: '',
        folder: ''
    },
    statusInterval: null
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    console.log('ESXi OVA Downloader inicializado');
});

// Event Listeners
function initializeEventListeners() {
    // Conexión
    document.getElementById('connectionForm').addEventListener('submit', handleConnect);
    document.getElementById('disconnectBtn').addEventListener('click', handleDisconnect);
    
    // Filtros
    document.getElementById('filterHost').addEventListener('change', applyFilters);
    document.getElementById('filterCluster').addEventListener('change', applyFilters);
    document.getElementById('filterPowerState').addEventListener('change', applyFilters);
    document.getElementById('filterFolder').addEventListener('change', applyFilters);
    document.getElementById('refreshBtn').addEventListener('click', loadVMs);
    
    // Selección
    document.getElementById('selectAll').addEventListener('change', handleSelectAll);
    
    // Exportación
    document.getElementById('exportBtn').addEventListener('click', handleExport);
    document.getElementById('cancelBtn').addEventListener('click', handleCancel);
}

// Conexión a vCenter
async function handleConnect(event) {
    event.preventDefault();
    
    const vcenterHost = document.getElementById('vcenterHost').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    const connectBtn = document.getElementById('connectBtn');
    const statusDiv = document.getElementById('connectionStatus');
    
    connectBtn.disabled = true;
    connectBtn.textContent = 'Conectando...';
    
    try {
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                vcenter_host: vcenterHost,
                username: username,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus(statusDiv, data.message, 'success');
            app.connected = true;
            
            // Mostrar botón de desconectar
            document.getElementById('connectBtn').style.display = 'none';
            document.getElementById('disconnectBtn').style.display = 'inline-block';
            
            // Deshabilitar campos del formulario
            document.getElementById('vcenterHost').disabled = true;
            document.getElementById('username').disabled = true;
            document.getElementById('password').disabled = true;
            
            // Cargar VMs
            await loadVMs();
            
            // Mostrar panel de VMs
            document.getElementById('vmPanel').style.display = 'block';
            
            // Iniciar polling de estado
            startStatusPolling();
            
        } else {
            showStatus(statusDiv, data.error, 'error');
        }
        
    } catch (error) {
        showStatus(statusDiv, `Error de conexión: ${error.message}`, 'error');
    } finally {
        connectBtn.disabled = false;
        connectBtn.textContent = 'Conectar';
    }
}

// Desconexión
async function handleDisconnect() {
    try {
        const response = await fetch('/api/disconnect', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            app.connected = false;
            app.vms = [];
            app.selectedVms.clear();
            
            // Resetear UI
            document.getElementById('connectBtn').style.display = 'inline-block';
            document.getElementById('disconnectBtn').style.display = 'none';
            document.getElementById('vcenterHost').disabled = false;
            document.getElementById('username').disabled = false;
            document.getElementById('password').disabled = false;
            document.getElementById('password').value = '';
            
            document.getElementById('vmPanel').style.display = 'none';
            document.getElementById('queuePanel').style.display = 'none';
            
            const statusDiv = document.getElementById('connectionStatus');
            showStatus(statusDiv, data.message, 'success');
            
            // Detener polling
            stopStatusPolling();
        }
        
    } catch (error) {
        console.error('Error desconectando:', error);
    }
}

// Cargar VMs
async function loadVMs() {
    if (!app.connected) return;
    
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.disabled = true;
    refreshBtn.textContent = '⏳ Cargando...';
    
    try {
        // Construir query string con filtros
        const params = new URLSearchParams();
        if (app.filters.host) params.append('host', app.filters.host);
        if (app.filters.cluster) params.append('cluster', app.filters.cluster);
        if (app.filters.power_state) params.append('power_state', app.filters.power_state);
        if (app.filters.folder) params.append('folder', app.filters.folder);
        
        const response = await fetch(`/api/vms?${params.toString()}`);
        const data = await response.json();
        
        if (data.success) {
            app.vms = data.vms;
            
            // Actualizar opciones de filtros
            updateFilterOptions(data.filter_options);
            
            // Renderizar tabla
            renderVMTable();
        } else {
            alert(`Error cargando VMs: ${data.error}`);
        }
        
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = '🔄 Actualizar';
    }
}

// Actualizar opciones de filtros
function updateFilterOptions(options) {
    updateSelectOptions('filterHost', options.hosts);
    updateSelectOptions('filterCluster', options.clusters);
    updateSelectOptions('filterPowerState', options.power_states);
    updateSelectOptions('filterFolder', options.folders);
}

function updateSelectOptions(selectId, values) {
    const select = document.getElementById(selectId);
    const currentValue = select.value;
    
    // Limpiar opciones excepto la primera (Todos)
    while (select.options.length > 1) {
        select.remove(1);
    }
    
    // Agregar nuevas opciones
    values.forEach(value => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value;
        select.appendChild(option);
    });
    
    // Restaurar valor seleccionado si existe
    if (currentValue && values.includes(currentValue)) {
        select.value = currentValue;
    }
}

// Aplicar filtros
function applyFilters() {
    app.filters.host = document.getElementById('filterHost').value;
    app.filters.cluster = document.getElementById('filterCluster').value;
    app.filters.power_state = document.getElementById('filterPowerState').value;
    app.filters.folder = document.getElementById('filterFolder').value;
    
    loadVMs();
}

// Renderizar tabla de VMs
function renderVMTable() {
    const tbody = document.getElementById('vmTableBody');
    tbody.innerHTML = '';
    
    if (app.vms.length === 0) {
        const row = tbody.insertRow();
        const cell = row.insertCell();
        cell.colSpan = 10;
        cell.textContent = 'No se encontraron VMs con los filtros aplicados';
        cell.style.textAlign = 'center';
        cell.style.padding = '20px';
        return;
    }
    
    app.vms.forEach(vm => {
        const row = tbody.insertRow();
        
        // Mantener selección si existía
        if (app.selectedVms.has(vm.name)) {
            row.classList.add('selected');
        }
        
        // Checkbox
        const checkCell = row.insertCell();
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = app.selectedVms.has(vm.name);
        checkbox.addEventListener('change', () => handleVMSelection(vm.name, checkbox.checked));
        checkCell.appendChild(checkbox);
        
        // Nombre
        row.insertCell().textContent = vm.name;
        
        // Estado con badge
        const stateCell = row.insertCell();
        const stateBadge = document.createElement('span');
        stateBadge.className = `power-state ${vm.power_state}`;
        stateBadge.textContent = vm.power_state;
        stateCell.appendChild(stateBadge);
        
        // Host
        row.insertCell().textContent = vm.host;
        
        // Cluster
        row.insertCell().textContent = vm.cluster;
        
        // Folder
        row.insertCell().textContent = vm.folder;
        
        // CPU
        row.insertCell().textContent = vm.num_cpu;
        
        // RAM
        row.insertCell().textContent = (vm.memory_mb / 1024).toFixed(2);
        
        // Disco
        row.insertCell().textContent = vm.storage_gb.toFixed(2);
        
        // SO
        row.insertCell().textContent = vm.guest_os;
    });
    
    updateSelectionCount();
}

// Manejar selección de VM
function handleVMSelection(vmName, isSelected) {
    if (isSelected) {
        app.selectedVms.add(vmName);
    } else {
        app.selectedVms.delete(vmName);
    }
    
    updateSelectionCount();
    
    // Actualizar clase de fila
    const tbody = document.getElementById('vmTableBody');
    const rows = tbody.getElementsByTagName('tr');
    for (let row of rows) {
        const cells = row.getElementsByTagName('td');
        if (cells.length > 1 && cells[1].textContent === vmName) {
            if (isSelected) {
                row.classList.add('selected');
            } else {
                row.classList.remove('selected');
            }
            break;
        }
    }
}

// Seleccionar todas las VMs
function handleSelectAll(event) {
    const isChecked = event.target.checked;
    
    if (isChecked) {
        app.vms.forEach(vm => app.selectedVms.add(vm.name));
    } else {
        app.selectedVms.clear();
    }
    
    renderVMTable();
}

// Actualizar contador de selección
function updateSelectionCount() {
    document.getElementById('selectionCount').textContent = 
        `${app.selectedVms.size} VM${app.selectedVms.size !== 1 ? 's' : ''} seleccionada${app.selectedVms.size !== 1 ? 's' : ''}`;
    
    const exportBtn = document.getElementById('exportBtn');
    exportBtn.disabled = app.selectedVms.size === 0;
}

// Exportar VMs
async function handleExport() {
    if (app.selectedVms.size === 0) return;
    
    const vmNames = Array.from(app.selectedVms);
    const poweroffBefore = document.getElementById('poweroffBeforeExport').checked;
    
    const confirmMsg = `¿Descargar ${vmNames.length} VM(s) como OVA?\n\n` +
                       `VMs: ${vmNames.join(', ')}\n` +
                       (poweroffBefore ? '\n⚠️ Las VMs serán apagadas antes de exportar.' : '');
    
    if (!confirm(confirmMsg)) return;
    
    const exportBtn = document.getElementById('exportBtn');
    exportBtn.disabled = true;
    exportBtn.textContent = '⏳ Agregando a cola...';
    
    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                vm_names: vmNames,
                poweroff_before_export: poweroffBefore
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            
            // Limpiar selección
            app.selectedVms.clear();
            document.getElementById('selectAll').checked = false;
            renderVMTable();
            
            // Mostrar panel de cola
            document.getElementById('queuePanel').style.display = 'block';
            
        } else {
            alert(`Error: ${data.error}`);
        }
        
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        exportBtn.disabled = false;
        exportBtn.textContent = '⬇️ Descargar Seleccionadas';
    }
}

// Cancelar descargas
async function handleCancel() {
    if (!confirm('¿Cancelar todas las descargas pendientes?')) return;
    
    try {
        const response = await fetch('/api/cancel', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
        }
        
    } catch (error) {
        console.error('Error cancelando:', error);
    }
}

// Polling de estado de descargas
function startStatusPolling() {
    stopStatusPolling(); // Detener cualquier polling previo
    
    app.statusInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.success) {
                updateDownloadStatus(data);
            }
            
        } catch (error) {
            console.error('Error obteniendo estado:', error);
        }
    }, 2000); // Actualizar cada 2 segundos
}

function stopStatusPolling() {
    if (app.statusInterval) {
        clearInterval(app.statusInterval);
        app.statusInterval = null;
    }
}

// Actualizar UI con estado de descargas
function updateDownloadStatus(status) {
    const currentDiv = document.getElementById('currentDownload');
    const queueDiv = document.getElementById('queueList');
    const historyDiv = document.getElementById('historyList');
    
    // Descarga actual
    if (status.current_download) {
        currentDiv.style.display = 'block';
        
        const download = status.current_download;
        document.getElementById('currentVmName').textContent = download.vm_name;
        document.getElementById('currentStatus').textContent = download.status;
        document.getElementById('currentStatus').className = `download-status ${download.status}`;
        
        const progress = download.progress || 0;
        document.getElementById('currentProgress').style.width = `${progress}%`;
        document.getElementById('currentProgressText').textContent = `${progress}%`;
        document.getElementById('currentMessage').textContent = download.message || '';
        
    } else {
        currentDiv.style.display = 'none';
    }
    
    // Cola
    if (status.queue && status.queue.length > 0) {
        queueDiv.style.display = 'block';
        document.getElementById('queueCount').textContent = status.queue.length;
        
        const queueItems = document.getElementById('queueItems');
        queueItems.innerHTML = '';
        
        status.queue.forEach(item => {
            const div = document.createElement('div');
            div.className = 'download-item';
            div.innerHTML = `
                <div class="download-info">
                    <span class="vm-name">${item.vm_name}</span>
                    <span class="download-status ${item.status}">${item.status}</span>
                </div>
            `;
            queueItems.appendChild(div);
        });
        
    } else {
        queueDiv.style.display = 'none';
    }
    
    // Historial
    if (status.history && status.history.length > 0) {
        historyDiv.style.display = 'block';
        
        const historyItems = document.getElementById('historyItems');
        historyItems.innerHTML = '';
        
        status.history.forEach(item => {
            const div = document.createElement('div');
            div.className = 'download-item';
            
            let details = '';
            if (item.status === 'completed' && item.file_path) {
                details = `<div class="download-message">✅ ${item.file_path}</div>`;
            } else if (item.status === 'failed' && item.error) {
                details = `<div class="download-message">❌ ${item.error}</div>`;
            }
            
            div.innerHTML = `
                <div class="download-info">
                    <span class="vm-name">${item.vm_name}</span>
                    <span class="download-status ${item.status}">${item.status}</span>
                </div>
                ${details}
            `;
            historyItems.appendChild(div);
        });
        
    } else {
        historyDiv.style.display = 'none';
    }
}

// Mostrar mensaje de estado
function showStatus(element, message, type) {
    element.textContent = message;
    element.className = `status-message ${type}`;
    element.style.display = 'block';
    
    // Auto-ocultar después de 5 segundos para mensajes de éxito
    if (type === 'success') {
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}
