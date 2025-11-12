// Lumina Web App - Main JavaScript

const API_BASE = '/api';

class LuminaApp {
    constructor() {
        this.requests = [];
        this.currentRequest = null;
        this.init();
    }

    async init() {
        await this.loadRequests();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Send 버튼
        document.getElementById('btn-send').addEventListener('click', () => this.sendRequest());

        // New Request 버튼
        document.getElementById('btn-new-request').addEventListener('click', () => this.createNewRequest());

        // Clear Response 버튼
        document.getElementById('btn-clear-response').addEventListener('click', () => this.clearResponse());

        // Import/Export 버튼
        document.getElementById('btn-import-md').addEventListener('click', () => this.showImportModal());
        document.getElementById('btn-export-md').addEventListener('click', () => this.showExportModal());

        // Import Modal
        document.getElementById('btn-close-import').addEventListener('click', () => this.hideImportModal());
        document.getElementById('btn-cancel-import').addEventListener('click', () => this.hideImportModal());
        document.getElementById('btn-confirm-import').addEventListener('click', () => this.importMarkdown());

        // Export Modal
        document.getElementById('btn-close-export').addEventListener('click', () => this.hideExportModal());
        document.getElementById('btn-close-export2').addEventListener('click', () => this.hideExportModal());
        document.getElementById('btn-copy-export').addEventListener('click', () => this.copyExportToClipboard());

        // Tabs
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const target = e.target.closest('.tab');
                if (target) this.switchTab(target.dataset.tab);
            });
        });

        // Response Tabs
        document.querySelectorAll('.response-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const target = e.target.closest('.response-tab');
                if (target) this.switchResponseTab(target.dataset.tab);
            });
        });

        // Auth Type 변경
        document.getElementById('auth-type').addEventListener('change', (e) => this.onAuthTypeChange(e.target.value));

        // Auth 입력 필드 변경
        ['auth-basic-username', 'auth-basic-password', 'auth-bearer-token',
         'auth-apikey-name', 'auth-apikey-value', 'auth-apikey-location'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener('change', () => this.saveCurrentRequest());
            }
        });

        // URL 입력 변경
        document.getElementById('input-url').addEventListener('change', () => this.saveCurrentRequest());

        // Method 선택 변경
        document.getElementById('select-method').addEventListener('change', () => this.saveCurrentRequest());
    }

    async loadRequests() {
        try {
            const response = await fetch(`${API_BASE}/requests`);
            this.requests = await response.json();
            this.renderRequestList();
        } catch (error) {
            console.error('Failed to load requests:', error);
        }
    }

    renderRequestList() {
        const listEl = document.getElementById('request-list');
        listEl.innerHTML = '';

        this.requests.forEach(req => {
            const li = document.createElement('li');
            li.className = 'request-item';
            if (this.currentRequest && this.currentRequest.id === req.id) {
                li.classList.add('active');
            }

            li.innerHTML = `
                <span class="request-method method-${req.method}">${req.method}</span>
                <span class="request-name">${req.name}</span>
            `;

            li.addEventListener('click', () => this.selectRequest(req.id));
            listEl.appendChild(li);
        });
    }

    async selectRequest(requestId) {
        try {
            const response = await fetch(`${API_BASE}/requests/${requestId}`);
            this.currentRequest = await response.json();
            this.renderRequestEditor();
            this.renderRequestList(); // 활성 상태 업데이트
            this.clearResponse();
        } catch (error) {
            console.error('Failed to load request:', error);
        }
    }

    renderRequestEditor() {
        if (!this.currentRequest) return;

        // Method & URL
        document.getElementById('select-method').value = this.currentRequest.method;
        document.getElementById('input-url').value = this.currentRequest.url;

        // Headers
        this.renderKeyValueTable('headers', this.currentRequest.headers);

        // Params
        this.renderKeyValueTable('params', this.currentRequest.params);

        // Body
        document.getElementById('body-raw').value = this.currentRequest.body_raw || '';

        // Auth
        this.renderAuth();

        // Load history
        this.loadHistory();
    }

    renderAuth() {
        const authType = this.currentRequest.auth_type || 'none';
        document.getElementById('auth-type').value = authType;

        // Show/hide auth sections
        this.onAuthTypeChange(authType);

        // Set auth values
        if (authType === 'basic') {
            document.getElementById('auth-basic-username').value = this.currentRequest.auth_basic_username || '';
            document.getElementById('auth-basic-password').value = this.currentRequest.auth_basic_password || '';
        } else if (authType === 'bearer') {
            document.getElementById('auth-bearer-token').value = this.currentRequest.auth_bearer_token || '';
        } else if (authType === 'apikey') {
            document.getElementById('auth-apikey-name').value = this.currentRequest.auth_api_key_name || '';
            document.getElementById('auth-apikey-value').value = this.currentRequest.auth_api_key_value || '';
            document.getElementById('auth-apikey-location').value = this.currentRequest.auth_api_key_location || 'header';
        }
    }

    onAuthTypeChange(authType) {
        // Hide all auth sections
        document.querySelectorAll('.auth-section').forEach(section => {
            section.classList.add('hidden');
        });

        // Show selected auth section
        if (authType === 'basic') {
            document.getElementById('auth-basic').classList.remove('hidden');
        } else if (authType === 'bearer') {
            document.getElementById('auth-bearer').classList.remove('hidden');
        } else if (authType === 'apikey') {
            document.getElementById('auth-apikey').classList.remove('hidden');
        }

        this.saveCurrentRequest();
    }

    renderKeyValueTable(type, data) {
        const tbody = document.getElementById(`${type}-tbody`);
        tbody.innerHTML = '';

        // 기존 데이터 렌더링
        Object.entries(data || {}).forEach(([key, value]) => {
            this.addKeyValueRow(type, key, value);
        });

        // 빈 행 추가
        this.addKeyValueRow(type, '', '');
    }

    addKeyValueRow(type, key = '', value = '') {
        const tbody = document.getElementById(`${type}-tbody`);
        const tr = document.createElement('tr');

        tr.innerHTML = `
            <td><input type="text" class="kv-key" value="${key}" placeholder="Key"></td>
            <td><input type="text" class="kv-value" value="${value}" placeholder="Value"></td>
            <td><button class="btn-remove" onclick="this.parentElement.parentElement.remove()">×</button></td>
        `;

        // 입력 시 새 행 추가
        const inputs = tr.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                // 마지막 행에 입력이 있으면 새 빈 행 추가
                const rows = tbody.querySelectorAll('tr');
                const lastRow = rows[rows.length - 1];
                const lastInputs = lastRow.querySelectorAll('input');
                const hasValue = Array.from(lastInputs).some(inp => inp.value.trim());

                if (hasValue) {
                    this.addKeyValueRow(type, '', '');
                }

                this.saveCurrentRequest();
            });
        });

        tbody.appendChild(tr);
    }

    getKeyValueData(type) {
        const tbody = document.getElementById(`${type}-tbody`);
        const data = {};

        tbody.querySelectorAll('tr').forEach(tr => {
            const key = tr.querySelector('.kv-key')?.value.trim();
            const value = tr.querySelector('.kv-value')?.value.trim();
            if (key) {
                data[key] = value;
            }
        });

        return data;
    }

    async saveCurrentRequest() {
        if (!this.currentRequest) return;

        // Get auth data
        const authType = document.getElementById('auth-type').value;
        const authData = {
            auth_type: authType
        };

        if (authType === 'basic') {
            authData.auth_basic_username = document.getElementById('auth-basic-username').value;
            authData.auth_basic_password = document.getElementById('auth-basic-password').value;
        } else if (authType === 'bearer') {
            authData.auth_bearer_token = document.getElementById('auth-bearer-token').value;
        } else if (authType === 'apikey') {
            authData.auth_api_key_name = document.getElementById('auth-apikey-name').value;
            authData.auth_api_key_value = document.getElementById('auth-apikey-value').value;
            authData.auth_api_key_location = document.getElementById('auth-apikey-location').value;
        }

        const updatedData = {
            name: this.currentRequest.name,
            url: document.getElementById('input-url').value,
            method: document.getElementById('select-method').value,
            headers: this.getKeyValueData('headers'),
            params: this.getKeyValueData('params'),
            body_raw: document.getElementById('body-raw').value,
            body_type: 'raw',
            ...authData
        };

        try {
            await fetch(`${API_BASE}/requests/${this.currentRequest.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedData)
            });
        } catch (error) {
            console.error('Failed to save request:', error);
        }
    }

    async createNewRequest() {
        const name = prompt('Enter request name:');
        if (!name) return;

        try {
            const response = await fetch(`${API_BASE}/requests`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, url: '', method: 'GET' })
            });

            const newRequest = await response.json();
            await this.loadRequests();
            await this.selectRequest(newRequest.id);
        } catch (error) {
            console.error('Failed to create request:', error);
        }
    }

    async sendRequest() {
        if (!this.currentRequest) {
            alert('Please select a request first');
            return;
        }

        // 현재 상태 저장
        await this.saveCurrentRequest();

        // 로딩 표시
        const btn = document.getElementById('btn-send');
        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span> Sending...';

        try {
            const response = await fetch(`${API_BASE}/requests/${this.currentRequest.id}/execute`, {
                method: 'POST'
            });

            const result = await response.json();
            this.renderResponse(result);

            // 히스토리 새로고침
            await this.loadHistory();
        } catch (error) {
            console.error('Failed to send request:', error);
            this.renderResponse({
                error: error.message,
                status_code: 0
            });
        } finally {
            btn.disabled = false;
            btn.textContent = 'Send';
        }
    }

    renderResponse(response) {
        const statusEl = document.getElementById('response-status');
        const metaEl = document.getElementById('response-meta');
        const bodyEl = document.getElementById('response-body');

        // Store current response for headers tab
        this.currentResponse = response;

        // Status
        if (response.error) {
            statusEl.className = 'response-status status-error';
            statusEl.textContent = `Error: ${response.error}`;
            metaEl.textContent = '';
            bodyEl.textContent = response.error;
        } else {
            const statusClass = response.status_code >= 200 && response.status_code < 300 ? 'status-success' : 'status-error';
            statusEl.className = `response-status ${statusClass}`;
            statusEl.textContent = `${response.status_code} ${response.status_text}`;

            metaEl.textContent = `Time: ${response.elapsed_ms.toFixed(0)} ms | Size: ${response.size_bytes} bytes`;

            // Body (Pretty JSON if possible)
            try {
                const jsonData = JSON.parse(response.body);
                bodyEl.textContent = JSON.stringify(jsonData, null, 2);
            } catch {
                bodyEl.textContent = response.body;
            }
        }

        // Render headers
        this.renderResponseHeaders(response.headers || {});

        // Response 패널 표시
        document.getElementById('response-panel').classList.remove('hidden');

        // 히스토리 새로고침 (응답 히스토리)
        this.loadHistory();
    }

    renderResponseHeaders(headers) {
        const tbody = document.getElementById('response-headers-tbody');
        tbody.innerHTML = '';

        if (!headers || Object.keys(headers).length === 0) {
            tbody.innerHTML = '<tr><td colspan="2" style="text-align: center; color: #999;">No headers to display</td></tr>';
            return;
        }

        Object.entries(headers).forEach(([key, value]) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${key}</strong></td>
                <td>${value}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    clearResponse() {
        document.getElementById('response-panel').classList.add('hidden');
    }

    switchTab(tabName) {
        // 모든 탭 비활성화
        document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        // 선택된 탭 활성화
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`tab-${tabName}`).classList.add('active');
    }

    switchResponseTab(tabName) {
        // 모든 응답 탭 비활성화
        document.querySelectorAll('.response-tab').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.response-tab-content').forEach(content => content.classList.remove('active'));

        // 선택된 탭 활성화
        document.querySelector(`.response-tab[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`response-tab-${tabName}`).classList.add('active');
    }

    async loadHistory() {
        if (!this.currentRequest) return;

        try {
            const response = await fetch(`${API_BASE}/history/${this.currentRequest.id}?limit=20`);
            const result = await response.json();

            if (result.success && result.history.length > 0) {
                this.renderInputHistory(result.history);
                this.renderOutputHistory(result.history);
            } else {
                // No history
                document.getElementById('history-input-list').innerHTML =
                    '<p class="history-empty">No history yet. Send a request to start tracking!</p>';
                document.getElementById('history-output-list').innerHTML =
                    '<p class="history-empty">No response history yet. Send a request to see responses!</p>';
            }
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    renderInputHistory(history) {
        const historyList = document.getElementById('history-input-list');
        historyList.innerHTML = '';

        history.forEach((entry, index) => {
            const item = document.createElement('div');
            item.className = 'history-item';

            const timestamp = new Date(entry.timestamp);
            const timeStr = timestamp.toLocaleString();

            item.innerHTML = `
                <div class="history-item-header">
                    <span class="history-timestamp">📤 ${timeStr}</span>
                </div>
                <div class="history-request-info">
                    <strong>${entry.request.method}</strong> ${entry.request.url}
                </div>
                <div class="history-meta">
                    ${entry.request.params && Object.keys(entry.request.params).length > 0 ? `Params: ${Object.keys(entry.request.params).length}` : 'No params'} |
                    ${entry.request.headers && Object.keys(entry.request.headers).length > 0 ? `Headers: ${Object.keys(entry.request.headers).length}` : 'No headers'}
                </div>
            `;

            item.addEventListener('click', () => {
                this.loadHistoryRequest(entry);
            });

            historyList.appendChild(item);
        });
    }

    renderOutputHistory(history) {
        const historyList = document.getElementById('history-output-list');
        historyList.innerHTML = '';

        history.forEach(entry => {
            const item = document.createElement('div');
            item.className = 'history-item';

            const timestamp = new Date(entry.timestamp);
            const timeStr = timestamp.toLocaleString();

            const statusClass = entry.response.status_code >= 200 && entry.response.status_code < 300
                ? 'success' : 'error';

            item.innerHTML = `
                <div class="history-item-header">
                    <span class="history-timestamp">📥 ${timeStr}</span>
                    <span class="history-status ${statusClass}">
                        ${entry.response.status_code} ${entry.response.status_text || ''}
                    </span>
                </div>
                <div class="history-request-info">
                    <strong>${entry.request.method}</strong> ${entry.request.url}
                </div>
                <div class="history-meta">
                    Time: ${entry.response.elapsed_ms.toFixed(0)} ms |
                    Size: ${entry.response.size_bytes} bytes
                </div>
            `;

            item.addEventListener('click', () => {
                this.showHistoryDetail(entry);
            });

            historyList.appendChild(item);
        });
    }

    loadHistoryRequest(entry) {
        // Load a previous request configuration
        if (confirm('Load this request configuration? Current unsaved changes will be lost.')) {
            // Update current request with historical data
            this.currentRequest.url = entry.request.url;
            this.currentRequest.method = entry.request.method;
            this.currentRequest.params = entry.request.params || {};
            this.currentRequest.headers = entry.request.headers || {};
            this.currentRequest.body_raw = entry.request.body_raw || '';

            // Re-render the editor
            this.renderRequestEditor();
        }
    }

    showHistoryDetail(entry) {
        // Store current response for headers tab
        this.currentResponse = entry.response;

        // 응답 탭으로 전환하고 히스토리 응답 표시
        this.switchResponseTab('response');

        const bodyEl = document.getElementById('response-body');
        const statusEl = document.getElementById('response-status');
        const metaEl = document.getElementById('response-meta');

        const statusClass = entry.response.status_code >= 200 && entry.response.status_code < 300
            ? 'status-success' : 'status-error';

        statusEl.className = `response-status ${statusClass}`;
        statusEl.textContent = `${entry.response.status_code} ${entry.response.status_text || ''}`;

        metaEl.textContent = `Time: ${entry.response.elapsed_ms.toFixed(0)} ms | Size: ${entry.response.size_bytes} bytes`;

        // Body
        if (entry.response.body) {
            try {
                const jsonData = JSON.parse(entry.response.body);
                bodyEl.textContent = JSON.stringify(jsonData, null, 2);
            } catch {
                bodyEl.textContent = entry.response.body;
            }
        } else {
            bodyEl.textContent = entry.response.error || 'No response body';
        }

        // Render headers
        this.renderResponseHeaders(entry.response.headers || {});

        document.getElementById('response-panel').classList.remove('hidden');
    }

    // Import/Export 기능
    showImportModal() {
        document.getElementById('import-modal').classList.add('active');
        document.getElementById('import-markdown-textarea').value = '';
        document.getElementById('import-markdown-textarea').focus();
    }

    hideImportModal() {
        document.getElementById('import-modal').classList.remove('active');
    }

    async importMarkdown() {
        const content = document.getElementById('import-markdown-textarea').value.trim();
        if (!content) {
            alert('Please paste markdown content');
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/import/markdown`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            });

            const result = await response.json();

            if (result.success) {
                alert(`Successfully imported ${result.imported_count} requests from "${result.folder_name}"`);
                this.hideImportModal();
                await this.loadRequests();
            } else {
                alert(`Import failed: ${result.error}`);
            }
        } catch (error) {
            console.error('Failed to import markdown:', error);
            alert(`Import failed: ${error.message}`);
        }
    }

    async showExportModal() {
        try {
            const response = await fetch(`${API_BASE}/export/markdown`);
            const result = await response.json();

            if (result.success) {
                document.getElementById('export-markdown-textarea').value = result.content;
                document.getElementById('export-modal').classList.add('active');
            } else {
                alert(`Export failed: ${result.error}`);
            }
        } catch (error) {
            console.error('Failed to export markdown:', error);
            alert(`Export failed: ${error.message}`);
        }
    }

    hideExportModal() {
        document.getElementById('export-modal').classList.remove('active');
    }

    async copyExportToClipboard() {
        const textarea = document.getElementById('export-markdown-textarea');
        try {
            await navigator.clipboard.writeText(textarea.value);
            alert('Markdown copied to clipboard!');
        } catch (error) {
            // Fallback for older browsers
            textarea.select();
            document.execCommand('copy');
            alert('Markdown copied to clipboard!');
        }
    }
}

// 앱 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.app = new LuminaApp();
});
