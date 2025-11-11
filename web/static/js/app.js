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

        // Tabs
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
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
            listEl.appendChild(li));
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

        const updatedData = {
            name: this.currentRequest.name,
            url: document.getElementById('input-url').value,
            method: document.getElementById('select-method').value,
            headers: this.getKeyValueData('headers'),
            params: this.getKeyValueData('params'),
            body_raw: document.getElementById('body-raw').value,
            body_type: 'raw'
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

        // Response 패널 표시
        document.getElementById('response-panel').classList.remove('hidden');
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
}

// 앱 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.app = new LuminaApp();
});
