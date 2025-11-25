// Lumina Web App - Main JavaScript

const API_BASE = '/api';

class LuminaApp {
    constructor() {
        this.requests = [];
        this.currentRequest = null;
        this.folderTree = null;
        this.currentFolder = null;
        this.autoSaveTimer = null;
        this.collapsedFolders = new Set();
        this.currentProject = null;
        this.projects = [];
        this.isResizing = false;
        this.init();
    }

    async init() {
        await this.loadProjects();
        await this.loadFolderTree();
        this.setupEventListeners();
        this.startAutoSave();
        this.setupResizers();
    }

    setupEventListeners() {
        // Send 버튼
        document.getElementById('btn-send').addEventListener('click', () => this.sendRequest());

        // New Folder 버튼
        document.getElementById('btn-new-folder').addEventListener('click', () => this.createNewFolder());

        // New Request 버튼
        document.getElementById('btn-new-request').addEventListener('click', () => this.createNewRequest());

        // Clear Response 버튼
        document.getElementById('btn-clear-response').addEventListener('click', () => this.clearResponse());

        // Beautify JSON 버튼
        document.getElementById('btn-beautify-json').addEventListener('click', () => this.beautifyJSON());

        // Toggle Preview 버튼
        document.getElementById('btn-toggle-preview').addEventListener('click', () => this.toggleDocsPreview());

        // Docs 변경 감지
        document.getElementById('docs-markdown').addEventListener('input', () => {
            this.saveCurrentRequest();
        });

        // More Menu
        document.getElementById('btn-more').addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleMoreMenu();
        });
        document.getElementById('menu-import-insomnia').addEventListener('click', () => this.showImportInsomniaModal());
        document.getElementById('menu-export-insomnia').addEventListener('click', () => this.showExportInsomniaModal());
        document.getElementById('menu-import-postman').addEventListener('click', () => this.showImportPostmanModal());
        document.getElementById('menu-export-postman').addEventListener('click', () => this.showExportPostmanModal());
        document.getElementById('menu-clear-all').addEventListener('click', () => this.clearAllData());

        // Request Toolbar
        document.getElementById('btn-copy-url').addEventListener('click', () => this.copyRequestUrl());
        document.getElementById('btn-delete-request').addEventListener('click', () => this.deleteRequest());

        // Click outside to close more menu
        document.addEventListener('click', (e) => {
            const moreMenu = document.getElementById('more-menu');
            const moreBtn = document.getElementById('btn-more');
            if (!moreMenu.contains(e.target) && !moreBtn.contains(e.target)) {
                moreMenu.classList.add('hidden');
            }
        });

        // Import Insomnia Modal
        document.getElementById('btn-close-import-insomnia').addEventListener('click', () => this.hideImportInsomniaModal());
        document.getElementById('btn-cancel-import-insomnia').addEventListener('click', () => this.hideImportInsomniaModal());
        document.getElementById('btn-confirm-import-insomnia').addEventListener('click', () => this.importInsomnia());
        document.getElementById('insomnia-import-file').addEventListener('change', (e) => this.onInsomniaFileSelected(e));

        // Export Insomnia Modal
        document.getElementById('btn-close-export-insomnia').addEventListener('click', () => this.hideExportInsomniaModal());
        document.getElementById('btn-close-export-insomnia2').addEventListener('click', () => this.hideExportInsomniaModal());
        document.getElementById('btn-copy-export-insomnia').addEventListener('click', () => this.copyExportInsomniaToClipboard());
        document.getElementById('btn-download-export-insomnia').addEventListener('click', () => this.downloadExportInsomnia());

        // Import Postman Modal
        document.getElementById('btn-close-import-postman').addEventListener('click', () => this.hideImportPostmanModal());
        document.getElementById('btn-cancel-import-postman').addEventListener('click', () => this.hideImportPostmanModal());
        document.getElementById('btn-confirm-import-postman').addEventListener('click', () => this.importPostman());
        document.getElementById('postman-import-file').addEventListener('change', (e) => this.onPostmanFileSelected(e));

        // Export Postman Modal
        document.getElementById('btn-close-export-postman').addEventListener('click', () => this.hideExportPostmanModal());
        document.getElementById('btn-close-export-postman2').addEventListener('click', () => this.hideExportPostmanModal());
        document.getElementById('btn-copy-export-postman').addEventListener('click', () => this.copyExportPostmanToClipboard());
        document.getElementById('btn-download-export-postman').addEventListener('click', () => this.downloadExportPostman());

        // Share 버튼
        document.getElementById('btn-share-project').addEventListener('click', () => this.showShareModal());

        // Share Modal
        document.getElementById('btn-close-share').addEventListener('click', () => this.hideShareModal());
        document.getElementById('btn-cancel-share').addEventListener('click', () => this.hideShareModal());
        document.getElementById('btn-create-share').addEventListener('click', () => this.createShare());
        document.getElementById('btn-copy-share').addEventListener('click', () => this.copyShareURL());

        // Import Share Modal
        document.getElementById('btn-close-import-share').addEventListener('click', () => this.hideImportShareModal());
        document.getElementById('btn-cancel-import-share').addEventListener('click', () => this.hideImportShareModal());
        document.getElementById('btn-confirm-import-share').addEventListener('click', () => this.importShare());

        // Global Constants 버튼
        document.getElementById('btn-global-constants').addEventListener('click', () => this.showGlobalConstantsModal());

        // Global Constants Modal
        document.getElementById('btn-close-global-constants').addEventListener('click', () => this.hideGlobalConstantsModal());
        document.getElementById('btn-cancel-global-constants').addEventListener('click', () => this.hideGlobalConstantsModal());
        document.getElementById('btn-save-global-constants').addEventListener('click', () => this.saveGlobalConstants());
        document.getElementById('btn-add-global-constant').addEventListener('click', () => this.addGlobalConstantRow());

        // Project Management
        document.getElementById('project-dropdown').addEventListener('change', (e) => this.onProjectChange(e.target.value));
        document.getElementById('btn-new-project').addEventListener('click', () => this.showNewProjectModal());
        document.getElementById('btn-manage-projects').addEventListener('click', () => this.showManageProjectsModal());

        // New Project Modal
        document.getElementById('btn-close-new-project').addEventListener('click', () => this.hideNewProjectModal());
        document.getElementById('btn-cancel-new-project').addEventListener('click', () => this.hideNewProjectModal());
        document.getElementById('btn-confirm-new-project').addEventListener('click', () => this.createNewProject());

        // Manage Projects Modal
        document.getElementById('btn-close-manage-projects').addEventListener('click', () => this.hideManageProjectsModal());
        document.getElementById('btn-close-manage-projects2').addEventListener('click', () => this.hideManageProjectsModal());

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

        // Resizer
        this.setupResizer();
    }

    setupResizer() {
        const resizer = document.getElementById('resizer');
        const requestEditor = document.querySelector('.request-editor');
        const responsePanel = document.querySelector('.response-panel');
        const container = document.querySelector('.container');

        let startX = 0;
        let startWidth = 0;

        resizer.addEventListener('mousedown', (e) => {
            this.isResizing = true;
            startX = e.clientX;
            startWidth = requestEditor.offsetWidth;
            resizer.classList.add('resizing');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!this.isResizing) return;

            const delta = e.clientX - startX;
            const newWidth = startWidth + delta;
            const containerWidth = container.offsetWidth;
            const sidebarWidth = 320; // sidebar width
            const resizerWidth = 5;
            const minWidth = 400;
            const maxWidth = containerWidth - sidebarWidth - resizerWidth - minWidth;

            if (newWidth >= minWidth && newWidth <= maxWidth) {
                requestEditor.style.flex = 'none';
                requestEditor.style.width = newWidth + 'px';
            }
        });

        document.addEventListener('mouseup', () => {
            if (this.isResizing) {
                this.isResizing = false;
                resizer.classList.remove('resizing');
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
    }

    async loadFolderTree() {
        try {
            const response = await fetch(`${API_BASE}/folders/tree`);
            const data = await response.json();
            this.folderTree = data.tree;
            this.renderFolderTree();
        } catch (error) {
            console.error('Failed to load folder tree:', error);
        }
    }

    renderFolderTree() {
        const treeEl = document.getElementById('folder-tree');
        treeEl.innerHTML = '';
        this.renderFolder(this.folderTree, treeEl, 0);
    }

    renderFolder(folder, parentEl, level) {
        const folderDiv = document.createElement('div');
        folderDiv.className = 'tree-folder';

        // 폴더 헤더
        const headerDiv = document.createElement('div');
        headerDiv.className = 'tree-folder-header';
        headerDiv.style.paddingLeft = `${level * 1}rem`;
        headerDiv.draggable = level > 0; // 루트 폴더는 드래그 불가
        headerDiv.dataset.folderId = folder.id;
        headerDiv.dataset.type = 'folder';

        const isCollapsed = this.collapsedFolders.has(folder.id);

        headerDiv.innerHTML = `
            <span class="tree-folder-toggle">${isCollapsed ? '▶' : '▼'}</span>
            <span class="tree-folder-icon">${isCollapsed ? '📁' : '📂'}</span>
            <span class="tree-folder-name">${folder.name}</span>
        `;

        // 드래그 이벤트
        if (level > 0) {
            headerDiv.addEventListener('dragstart', (e) => {
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('folderId', folder.id);
                e.dataTransfer.setData('type', 'folder');
                headerDiv.classList.add('dragging');
            });

            headerDiv.addEventListener('dragend', (e) => {
                headerDiv.classList.remove('dragging');
            });
        }

        // 드롭 영역으로 설정
        headerDiv.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            headerDiv.classList.add('drag-over');
        });

        headerDiv.addEventListener('dragleave', (e) => {
            headerDiv.classList.remove('drag-over');
        });

        headerDiv.addEventListener('drop', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            headerDiv.classList.remove('drag-over');

            const draggedType = e.dataTransfer.getData('type');
            const draggedId = e.dataTransfer.getData(draggedType === 'folder' ? 'folderId' : 'requestId');

            if (!draggedId) return;

            // 자기 자신으로 드롭은 무시
            if (draggedType === 'folder' && draggedId === folder.id) return;

            if (draggedType === 'request') {
                // 요청을 폴더로 이동
                await this.moveRequest(draggedId, folder.id);
            } else if (draggedType === 'folder') {
                // 폴더를 폴더로 이동 (하위 폴더로)
                await this.moveFolder(draggedId, folder.id);
            }
        });

        // 토글 클릭
        const toggle = headerDiv.querySelector('.tree-folder-toggle');
        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleFolder(folder.id);
        });

        // 폴더 클릭 (현재 폴더 설정)
        headerDiv.addEventListener('click', () => {
            this.currentFolder = folder;
            this.currentRequest = null; // 요청 선택 해제
            document.querySelectorAll('.tree-folder-header').forEach(h => h.classList.remove('active'));
            document.querySelectorAll('.tree-request').forEach(r => r.classList.remove('active'));
            headerDiv.classList.add('active');
        });

        folderDiv.appendChild(headerDiv);

        // 폴더 내용
        const contentDiv = document.createElement('div');
        contentDiv.className = `tree-folder-content ${isCollapsed ? 'collapsed' : ''}`;

        // 하위 폴더 렌더링
        folder.folders.forEach(subFolder => {
            this.renderFolder(subFolder, contentDiv, level + 1);
        });

        // 요청 렌더링
        folder.requests.forEach(req => {
            this.renderRequest(req, contentDiv, level + 1);
        });

        folderDiv.appendChild(contentDiv);
        parentEl.appendChild(folderDiv);
    }

    renderRequest(request, parentEl, level) {
        const reqDiv = document.createElement('div');
        reqDiv.className = 'tree-request';
        reqDiv.style.paddingLeft = `${level * 1}rem`;
        reqDiv.draggable = true;
        reqDiv.dataset.requestId = request.id;
        reqDiv.dataset.type = 'request';

        if (this.currentRequest && this.currentRequest.id === request.id) {
            reqDiv.classList.add('active');
        }

        reqDiv.innerHTML = `
            <span class="request-method method-${request.method}">${request.method}</span>
            <span class="request-name">${request.name}</span>
        `;

        // 드래그 이벤트
        reqDiv.addEventListener('dragstart', (e) => {
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('requestId', request.id);
            e.dataTransfer.setData('type', 'request');
            reqDiv.classList.add('dragging');
        });

        reqDiv.addEventListener('dragend', (e) => {
            reqDiv.classList.remove('dragging');
        });

        reqDiv.addEventListener('click', () => this.selectRequest(request.id));

        parentEl.appendChild(reqDiv);
    }

    toggleFolder(folderId) {
        if (this.collapsedFolders.has(folderId)) {
            this.collapsedFolders.delete(folderId);
        } else {
            this.collapsedFolders.add(folderId);
        }
        this.renderFolderTree();
    }

    async selectRequest(requestId) {
        try {
            const response = await fetch(`${API_BASE}/requests/${requestId}`);
            this.currentRequest = await response.json();
            this.renderRequestEditor();
            this.renderFolderTree(); // 활성 상태 업데이트
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

        // Documentation
        document.getElementById('docs-markdown').value = this.currentRequest.documentation || '';

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
            documentation: document.getElementById('docs-markdown').value,
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

        // 현재 폴더가 없으면 루트 폴더 사용
        const targetFolder = this.currentFolder || this.folderTree;

        try {
            const response = await fetch(`${API_BASE}/folders/${targetFolder.id}/requests`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, url: '', method: 'GET' })
            });

            const data = await response.json();
            await this.loadFolderTree();
            await this.selectRequest(data.request.id);
        } catch (error) {
            console.error('Failed to create request:', error);
        }
    }

    async createNewFolder() {
        const name = prompt('Enter folder name:');
        if (!name) return;

        // 현재 폴더가 없으면 루트에 추가
        const parentId = this.currentFolder ? this.currentFolder.id : null;

        try {
            await fetch(`${API_BASE}/folders`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, parent_id: parentId })
            });

            await this.loadFolderTree();
        } catch (error) {
            console.error('Failed to create folder:', error);
        }
    }

    async deleteFolder(folderId) {
        try {
            await fetch(`${API_BASE}/folders/${folderId}`, {
                method: 'DELETE'
            });

            await this.loadFolderTree();
        } catch (error) {
            console.error('Failed to delete folder:', error);
        }
    }

    async moveRequest(requestId, targetFolderId) {
        try {
            await fetch(`${API_BASE}/requests/${requestId}/move`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder_id: targetFolderId })
            });

            await this.loadFolderTree();
        } catch (error) {
            console.error('Failed to move request:', error);
            alert('Failed to move request');
        }
    }

    async moveFolder(folderId, targetFolderId) {
        try {
            await fetch(`${API_BASE}/folders/${folderId}/move`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ parent_id: targetFolderId })
            });

            await this.loadFolderTree();
        } catch (error) {
            console.error('Failed to move folder:', error);
            alert('Failed to move folder');
        }
    }

    beautifyJSON() {
        const textarea = document.getElementById('body-raw');
        const content = textarea.value.trim();

        if (!content) {
            alert('No content to beautify');
            return;
        }

        try {
            const parsed = JSON.parse(content);
            textarea.value = JSON.stringify(parsed, null, 2);
            this.saveCurrentRequest();
        } catch (error) {
            alert('Invalid JSON: ' + error.message);
        }
    }

    startAutoSave() {
        // 자동 저장 타이머 설정 (5초마다)
        setInterval(() => {
            if (this.currentRequest) {
                this.saveCurrentRequest();
            }
        }, 5000);
    }

    toggleDocsPreview() {
        const textarea = document.getElementById('docs-markdown');
        const preview = document.getElementById('docs-preview');

        if (preview.classList.contains('hidden')) {
            // 프리뷰 표시
            const markdown = textarea.value;
            preview.innerHTML = this.renderMarkdown(markdown);
            preview.classList.remove('hidden');
            textarea.style.display = 'none';
        } else {
            // 편집 모드
            preview.classList.add('hidden');
            textarea.style.display = 'block';
        }
    }

    renderMarkdown(markdown) {
        if (!markdown) return '<p>No documentation yet.</p>';

        // 간단한 마크다운 렌더러
        let html = markdown;

        // 코드 블록 (```)
        html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre><code>${this.escapeHtml(code.trim())}</code></pre>`;
        });

        // 인라인 코드 (`)
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

        // 헤더
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

        // 볼드
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // 이탤릭
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // 링크
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

        // 리스트
        html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

        // 번호 리스트
        html = html.replace(/^\d+\. (.*$)/gim, '<li>$1</li>');

        // 줄바꿈
        html = html.split('\n\n').map(para => {
            if (para.startsWith('<h') || para.startsWith('<ul') || para.startsWith('<pre') || para.startsWith('<li>')) {
                return para;
            }
            return `<p>${para}</p>`;
        }).join('');

        return html;
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
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
        if (!tbody) return; // Element doesn't exist in simplified UI

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

        // Check if history elements exist (they don't in simplified UI)
        const inputList = document.getElementById('history-input-list');
        const outputList = document.getElementById('history-output-list');
        if (!inputList || !outputList) return;

        try {
            const response = await fetch(`${API_BASE}/history/${this.currentRequest.id}?limit=20`);
            const result = await response.json();

            if (result.success && result.history.length > 0) {
                this.renderInputHistory(result.history);
                this.renderOutputHistory(result.history);
            } else {
                // No history
                inputList.innerHTML =
                    '<p class="history-empty">No history yet. Send a request to start tracking!</p>';
                outputList.innerHTML =
                    '<p class="history-empty">No response history yet. Send a request to see responses!</p>';
            }
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    renderInputHistory(history) {
        const historyList = document.getElementById('history-input-list');
        if (!historyList) return; // Element doesn't exist in simplified UI
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
        if (!historyList) return; // Element doesn't exist in simplified UI
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

    // More Menu
    toggleMoreMenu() {
        const moreMenu = document.getElementById('more-menu');
        moreMenu.classList.toggle('hidden');
    }

    // Request Toolbar Actions
    async copyRequestUrl() {
        if (!this.currentRequest) {
            alert('Please select a request first');
            return;
        }

        const url = document.getElementById('input-url').value;
        if (!url) {
            alert('No URL to copy');
            return;
        }

        try {
            await navigator.clipboard.writeText(url);
            alert('URL copied to clipboard!');
        } catch (error) {
            // Fallback for older browsers
            const input = document.createElement('input');
            input.value = url;
            document.body.appendChild(input);
            input.select();
            document.execCommand('copy');
            document.body.removeChild(input);
            alert('URL copied to clipboard!');
        }
    }

    async deleteRequest() {
        // 폴더가 선택된 경우
        if (this.currentFolder && this.currentFolder.id && !this.currentRequest) {
            // 루트 폴더는 삭제 불가
            if (this.currentFolder.id === this.folderTree.id) {
                alert('Cannot delete root folder');
                return;
            }

            if (!confirm(`Delete folder "${this.currentFolder.name}" and all its contents? This cannot be undone.`)) {
                return;
            }

            try {
                await this.deleteFolder(this.currentFolder.id);
                this.currentFolder = null;
                alert('Folder deleted successfully');
            } catch (error) {
                console.error('Failed to delete folder:', error);
                alert('Failed to delete folder');
            }
            return;
        }

        // 요청이 선택된 경우
        if (!this.currentRequest) {
            alert('Please select a folder or request first');
            return;
        }

        if (!confirm(`Delete request "${this.currentRequest.name}"? This cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/requests/${this.currentRequest.id}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.currentRequest = null;
                this.clearResponse();
                await this.loadFolderTree();
                alert('Request deleted successfully');
            } else {
                alert(`Failed to delete request: ${result.error}`);
            }
        } catch (error) {
            console.error('Failed to delete request:', error);
            alert('Failed to delete request');
        }
    }

    async clearAllData() {
        if (!confirm('Clear ALL data? This will delete all requests and folders. This cannot be undone!')) {
            return;
        }

        if (!confirm('Are you ABSOLUTELY sure? This action is irreversible!')) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/clear-all`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.currentRequest = null;
                this.currentFolder = null;
                this.clearResponse();
                await this.loadFolderTree();
                document.getElementById('more-menu').classList.add('hidden');
                alert('All data cleared successfully');
            } else {
                alert(`Failed to clear data: ${result.error}`);
            }
        } catch (error) {
            console.error('Failed to clear data:', error);
            alert('Failed to clear data');
        }
    }


    // ==================
    // 프로젝트 관리
    // ==================

    async loadProjects() {
        try {
            const response = await fetch(`${API_BASE}/projects`);
            const result = await response.json();

            if (result.success) {
                this.projects = result.projects;
                this.renderProjectsDropdown();

                // 활성 프로젝트 찾기
                const activeProject = this.projects.find(p => p.is_active);
                if (activeProject) {
                    this.currentProject = activeProject;
                }
            }
        } catch (error) {
            console.error('Failed to load projects:', error);
        }
    }

    renderProjectsDropdown() {
        const dropdown = document.getElementById('project-dropdown');
        dropdown.innerHTML = '';

        if (this.projects.length === 0) {
            dropdown.innerHTML = '<option value="">No projects</option>';
            return;
        }

        this.projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = project.name;
            option.selected = project.is_active;
            dropdown.appendChild(option);
        });
    }

    async onProjectChange(projectId) {
        if (!projectId) return;

        try {
            const response = await fetch(`${API_BASE}/projects/${projectId}/activate`, {
                method: 'PUT'
            });

            const result = await response.json();

            if (result.success) {
                this.currentProject = result.project;

                // 폴더 트리 새로고침
                await this.loadFolderTree();

                // 현재 요청 초기화
                this.currentRequest = null;
                this.clearResponse();
            }
        } catch (error) {
            console.error('Failed to activate project:', error);
            alert('Failed to switch project');
        }
    }

    showNewProjectModal() {
        document.getElementById('new-project-modal').classList.add('active');
        document.getElementById('new-project-name').value = '';
        document.getElementById('new-project-name').focus();
    }

    hideNewProjectModal() {
        document.getElementById('new-project-modal').classList.remove('active');
    }

    async createNewProject() {
        const name = document.getElementById('new-project-name').value.trim();

        if (!name) {
            alert('Please enter a project name');
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/projects`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });

            const result = await response.json();

            if (result.success) {
                this.hideNewProjectModal();
                await this.loadProjects();

                // 새 프로젝트 활성화
                await this.onProjectChange(result.project.id);
            } else {
                alert(`Failed to create project: ${result.error}`);
            }
        } catch (error) {
            console.error('Failed to create project:', error);
            alert('Failed to create project');
        }
    }

    async showManageProjectsModal() {
        await this.loadProjects();
        this.renderProjectsList();
        document.getElementById('manage-projects-modal').classList.add('active');
    }

    hideManageProjectsModal() {
        document.getElementById('manage-projects-modal').classList.remove('active');
    }

    renderProjectsList() {
        const list = document.getElementById('projects-list');
        list.innerHTML = '';

        if (this.projects.length === 0) {
            list.innerHTML = '<p class="history-empty">No projects yet. Create one!</p>';
            return;
        }

        this.projects.forEach(project => {
            const item = document.createElement('div');
            item.className = `project-item ${project.is_active ? 'active' : ''}`;

            item.innerHTML = `
                <div class="project-item-info">
                    <div class="project-item-name" data-project-id="${project.id}">
                        ${project.name}
                        ${project.is_active ? '<span class="project-item-badge">Active</span>' : ''}
                    </div>
                </div>
                <div class="project-item-actions">
                    ${!project.is_active ? `<button class="btn-activate-project" data-project-id="${project.id}">Activate</button>` : ''}
                    <button class="btn-delete-project" data-project-id="${project.id}">Delete</button>
                </div>
            `;

            // 더블클릭으로 이름 변경
            const nameEl = item.querySelector('.project-item-name');
            nameEl.addEventListener('dblclick', () => {
                this.renameProjectInline(project.id, nameEl);
            });

            // 활성화 버튼
            const activateBtn = item.querySelector('.btn-activate-project');
            if (activateBtn) {
                activateBtn.addEventListener('click', async () => {
                    await this.activateProject(project.id);
                });
            }

            // 삭제 버튼
            const deleteBtn = item.querySelector('.btn-delete-project');
            deleteBtn.addEventListener('click', async () => {
                if (confirm(`Delete project "${project.name}"?`)) {
                    await this.deleteProject(project.id);
                }
            });

            list.appendChild(item);
        });
    }

    async activateProject(projectId) {
        await this.onProjectChange(projectId);
        await this.loadProjects();
        this.renderProjectsList();
    }

    async deleteProject(projectId) {
        try {
            const response = await fetch(`${API_BASE}/projects/${projectId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                await this.loadProjects();
                this.renderProjectsList();

                // 현재 프로젝트가 삭제된 경우 폴더 트리 새로고침
                await this.loadFolderTree();
            } else {
                alert(`Failed to delete project: ${result.error}`);
            }
        } catch (error) {
            console.error('Failed to delete project:', error);
            alert('Failed to delete project');
        }
    }

    renameProjectInline(projectId, nameEl) {
        const currentName = nameEl.textContent.trim().replace('Active', '').trim();
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentName;

        nameEl.innerHTML = '';
        nameEl.appendChild(input);
        input.focus();
        input.select();

        const finishRename = async () => {
            const newName = input.value.trim();

            if (newName && newName !== currentName) {
                try {
                    const response = await fetch(`${API_BASE}/projects/${projectId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name: newName })
                    });

                    const result = await response.json();

                    if (result.success) {
                        await this.loadProjects();
                        this.renderProjectsList();
                    } else {
                        alert(`Failed to rename project: ${result.error}`);
                        this.renderProjectsList();
                    }
                } catch (error) {
                    console.error('Failed to rename project:', error);
                    alert('Failed to rename project');
                    this.renderProjectsList();
                }
            } else {
                this.renderProjectsList();
            }
        };

        input.addEventListener('blur', finishRename);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                finishRename();
            } else if (e.key === 'Escape') {
                this.renderProjectsList();
            }
        });
    }

    // ==================== Modal Helper Functions ====================

    showModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }

    hideModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    }

    showImportModal() {
        this.showModal('import-modal');
    }

    // ==================== Share Functions ====================

    showShareModal() {
        // 초기화
        document.getElementById('share-url-container').style.display = 'none';
        document.getElementById('btn-create-share').style.display = 'block';
        document.getElementById('btn-copy-share').style.display = 'none';
        document.getElementById('share-expires').value = '';
        document.getElementById('share-readonly').checked = true;
        this.showModal('share-modal');
    }

    hideShareModal() {
        this.hideModal('share-modal');
    }

    async createShare() {
        const expiresHours = document.getElementById('share-expires').value;
        const readOnly = document.getElementById('share-readonly').checked;

        const btn = document.getElementById('btn-create-share');
        btn.disabled = true;
        btn.textContent = '생성 중...';

        try {
            const payload = {
                read_only: readOnly
            };

            if (expiresHours) {
                payload.expires_hours = parseInt(expiresHours);
            }

            const response = await fetch(`${API_BASE}/share/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (result.success) {
                // URL 표시
                document.getElementById('share-url-input').value = result.share_url;
                document.getElementById('share-url-container').style.display = 'block';
                document.getElementById('btn-create-share').style.display = 'none';
                document.getElementById('btn-copy-share').style.display = 'block';
            } else {
                alert(`공유 링크 생성 실패: ${result.error}`);
                btn.disabled = false;
                btn.textContent = 'Create Share Link';
            }
        } catch (error) {
            console.error('Failed to create share:', error);
            alert('공유 링크 생성 중 오류가 발생했습니다.');
            btn.disabled = false;
            btn.textContent = 'Create Share Link';
        }
    }

    copyShareURL() {
        const urlInput = document.getElementById('share-url-input');
        urlInput.select();
        document.execCommand('copy');

        const btn = document.getElementById('btn-copy-share');
        const originalText = btn.textContent;
        btn.textContent = '✅ Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }

    showImportShareModal() {
        document.getElementById('import-share-input').value = '';
        this.showModal('import-share-modal');
    }

    hideImportShareModal() {
        this.hideModal('import-share-modal');
    }

    async importShare() {
        const input = document.getElementById('import-share-input').value.trim();

        if (!input) {
            alert('공유 URL 또는 ID를 입력하세요.');
            return;
        }

        // URL에서 share ID 추출 (https://example.com/share/abc123 -> abc123)
        let shareId = input;
        if (input.includes('/share/')) {
            const parts = input.split('/share/');
            shareId = parts[1];
        }

        const btn = document.getElementById('btn-confirm-import-share');
        btn.disabled = true;
        btn.textContent = '가져오는 중...';

        try {
            const response = await fetch(`${API_BASE}/share/${shareId}/import`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const result = await response.json();

            if (result.success) {
                alert(`프로젝트 "${result.project.name}"를 성공적으로 가져왔습니다!`);
                this.hideImportShareModal();

                // 프로젝트 목록 새로고침
                await this.loadProjects();

                // 가져온 프로젝트로 전환
                await this.switchToProject(result.project.id);
            } else {
                alert(`프로젝트 가져오기 실패: ${result.error}`);
                btn.disabled = false;
                btn.textContent = 'Import Project';
            }
        } catch (error) {
            console.error('Failed to import share:', error);
            alert('프로젝트 가져오기 중 오류가 발생했습니다.');
            btn.disabled = false;
            btn.textContent = 'Import Project';
        }
    }

    // ==================== Global Constants Functions ====================

    async showGlobalConstantsModal() {
        this.showModal('global-constants-modal');
        await this.loadGlobalConstants();
    }

    hideGlobalConstantsModal() {
        this.hideModal('global-constants-modal');
    }

    async loadGlobalConstants() {
        try {
            const response = await fetch('/api/global-constants');
            const data = await response.json();

            const tbody = document.getElementById('global-constants-tbody');
            tbody.innerHTML = '';

            // Global constants가 있으면 표시
            if (data && data.variables && Object.keys(data.variables).length > 0) {
                for (const [key, value] of Object.entries(data.variables)) {
                    this.addGlobalConstantRow(key, value);
                }
            } else {
                // 빈 행 하나 추가
                this.addGlobalConstantRow();
            }
        } catch (error) {
            console.error('Failed to load global constants:', error);
            alert('Global Constants를 불러오는 중 오류가 발생했습니다.');
        }
    }

    addGlobalConstantRow(key = '', value = '') {
        const tbody = document.getElementById('global-constants-tbody');
        const row = document.createElement('tr');

        row.innerHTML = `
            <td><input type="text" value="${this.escapeHtml(key)}" placeholder="KEY" class="global-const-key"></td>
            <td><input type="text" value="${this.escapeHtml(value)}" placeholder="value" class="global-const-value"></td>
            <td><button class="btn-remove" onclick="this.closest('tr').remove()">×</button></td>
        `;

        tbody.appendChild(row);
    }

    async saveGlobalConstants() {
        const tbody = document.getElementById('global-constants-tbody');
        const rows = tbody.querySelectorAll('tr');
        const constants = {};

        rows.forEach(row => {
            const keyInput = row.querySelector('.global-const-key');
            const valueInput = row.querySelector('.global-const-value');

            const key = keyInput.value.trim();
            const value = valueInput.value.trim();

            if (key) {  // 키가 있는 경우만 저장
                constants[key] = value;
            }
        });

        try {
            const response = await fetch('/api/global-constants', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ constants })
            });

            const result = await response.json();

            if (result.success) {
                alert('Global Constants가 저장되었습니다!');
                this.hideGlobalConstantsModal();
            } else {
                alert('저장 실패: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Failed to save global constants:', error);
            alert('Global Constants 저장 중 오류가 발생했습니다.');
        }
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    // ==================== Project Management Functions ====================

    async switchToProject(projectId) {
        try {
            const response = await fetch(`${API_BASE}/projects/${projectId}/activate`, {
                method: 'PUT'
            });

            const result = await response.json();

            if (result.success) {
                this.currentProject = result.project;
                await this.loadFolderTree();
                this.updateProjectDropdown();
            }
        } catch (error) {
            console.error('Failed to switch project:', error);
        }
    }

    // ==================== Insomnia Import/Export Functions ====================

    showImportInsomniaModal() {
        // 초기화
        document.getElementById('insomnia-import-file').value = '';
        document.getElementById('import-insomnia-preview').style.display = 'none';
        document.getElementById('btn-confirm-import-insomnia').disabled = true;
        this.selectedInsomniaFile = null;
        this.showModal('import-insomnia-modal');
    }

    hideImportInsomniaModal() {
        this.hideModal('import-insomnia-modal');
    }

    onInsomniaFileSelected(event) {
        const file = event.target.files[0];
        if (!file) {
            document.getElementById('import-insomnia-preview').style.display = 'none';
            document.getElementById('btn-confirm-import-insomnia').disabled = true;
            this.selectedInsomniaFile = null;
            return;
        }

        // 파일 읽기
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const content = e.target.result;
                const jsonData = JSON.parse(content);

                // 워크스페이스 이름 찾기
                let projectName = 'Unknown Project';
                if (jsonData.resources) {
                    const workspace = jsonData.resources.find(r => r._type === 'workspace');
                    if (workspace) {
                        projectName = workspace.name || 'Unknown Project';
                    }
                }

                // 미리보기 표시
                document.getElementById('import-insomnia-filename').textContent = file.name;
                document.getElementById('import-insomnia-projectname').textContent = projectName;
                document.getElementById('import-insomnia-preview').style.display = 'block';
                document.getElementById('btn-confirm-import-insomnia').disabled = false;

                // 파일 내용 저장
                this.selectedInsomniaFile = content;
            } catch (error) {
                alert('유효하지 않은 JSON 파일입니다.');
                document.getElementById('import-insomnia-preview').style.display = 'none';
                document.getElementById('btn-confirm-import-insomnia').disabled = true;
                this.selectedInsomniaFile = null;
            }
        };
        reader.readAsText(file);
    }

    async importInsomnia() {
        if (!this.selectedInsomniaFile) {
            alert('파일을 선택하세요.');
            return;
        }

        const btn = document.getElementById('btn-confirm-import-insomnia');
        btn.disabled = true;
        btn.textContent = '가져오는 중...';

        try {
            const response = await fetch(`${API_BASE}/import/insomnia`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: this.selectedInsomniaFile })
            });

            const result = await response.json();

            if (result.success) {
                alert(`프로젝트 "${result.project.name}"를 성공적으로 가져왔습니다! (${result.imported_count}개 요청)`);
                this.hideImportInsomniaModal();

                // 프로젝트 목록 새로고침
                await this.loadProjects();

                // 가져온 프로젝트로 전환
                await this.switchToProject(result.project.id);
            } else {
                alert(`Insomnia JSON 가져오기 실패: ${result.error}`);
                btn.disabled = false;
                btn.textContent = 'Import as New Project';
            }
        } catch (error) {
            console.error('Failed to import Insomnia JSON:', error);
            alert('Insomnia JSON 가져오기 중 오류가 발생했습니다.');
            btn.disabled = false;
            btn.textContent = 'Import as New Project';
        }
    }

    showExportInsomniaModal() {
        this.showModal('export-insomnia-modal');
        this.loadExportInsomnia();
    }

    hideExportInsomniaModal() {
        this.hideModal('export-insomnia-modal');
    }

    async loadExportInsomnia() {
        try {
            const response = await fetch(`${API_BASE}/export/insomnia`);
            const result = await response.json();

            if (result.success) {
                document.getElementById('export-insomnia-textarea').value = JSON.stringify(result.content, null, 2);
            } else {
                alert(`Insomnia JSON 내보내기 실패: ${result.error}`);
            }
        } catch (error) {
            console.error('Failed to export Insomnia JSON:', error);
            alert('Insomnia JSON 내보내기 중 오류가 발생했습니다.');
        }
    }

    copyExportInsomniaToClipboard() {
        const textarea = document.getElementById('export-insomnia-textarea');
        textarea.select();
        document.execCommand('copy');

        const btn = document.getElementById('btn-copy-export-insomnia');
        const originalText = btn.textContent;
        btn.textContent = '✅ Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }

    downloadExportInsomnia() {
        const content = document.getElementById('export-insomnia-textarea').value;
        const blob = new Blob([content], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.currentProject?.name || 'Lumina'}_Insomnia_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        const btn = document.getElementById('btn-download-export-insomnia');
        const originalText = btn.textContent;
        btn.textContent = '✅ Downloaded!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }

    // ==================== Postman Import/Export Functions ====================

    showImportPostmanModal() {
        // 초기화
        document.getElementById('postman-import-file').value = '';
        document.getElementById('import-postman-preview').style.display = 'none';
        document.getElementById('btn-confirm-import-postman').disabled = true;
        this.selectedPostmanFile = null;
        this.showModal('import-postman-modal');
    }

    hideImportPostmanModal() {
        this.hideModal('import-postman-modal');
    }

    onPostmanFileSelected(event) {
        const file = event.target.files[0];
        if (!file) {
            document.getElementById('import-postman-preview').style.display = 'none';
            document.getElementById('btn-confirm-import-postman').disabled = true;
            this.selectedPostmanFile = null;
            return;
        }

        // 파일 읽기
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const content = e.target.result;
                const jsonData = JSON.parse(content);

                // Collection 이름 찾기
                let collectionName = 'Unknown Collection';
                if (jsonData.info && jsonData.info.name) {
                    collectionName = jsonData.info.name;
                }

                // 미리보기 표시
                document.getElementById('import-postman-filename').textContent = file.name;
                document.getElementById('import-postman-collectionname').textContent = collectionName;
                document.getElementById('import-postman-preview').style.display = 'block';
                document.getElementById('btn-confirm-import-postman').disabled = false;

                // 파일 내용 저장
                this.selectedPostmanFile = jsonData;
            } catch (error) {
                alert('유효하지 않은 JSON 파일입니다.');
                document.getElementById('import-postman-preview').style.display = 'none';
                document.getElementById('btn-confirm-import-postman').disabled = true;
                this.selectedPostmanFile = null;
            }
        };
        reader.readAsText(file);
    }

    async importPostman() {
        if (!this.selectedPostmanFile) {
            alert('파일을 선택하세요.');
            return;
        }

        const btn = document.getElementById('btn-confirm-import-postman');
        btn.disabled = true;
        btn.textContent = '가져오는 중...';

        try {
            const response = await fetch(`${API_BASE}/import/postman`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ data: this.selectedPostmanFile })
            });

            const result = await response.json();

            if (result.success) {
                alert(`성공적으로 가져왔습니다! (${result.imported_count}개 요청)`);
                this.hideImportPostmanModal();

                // 폴더 트리 새로고침
                await this.loadFolderTree();
            } else {
                alert(`Postman Collection 가져오기 실패: ${result.error}`);
                btn.disabled = false;
                btn.textContent = 'Import as New Project';
            }
        } catch (error) {
            console.error('Failed to import Postman Collection:', error);
            alert('Postman Collection 가져오기 중 오류가 발생했습니다.');
            btn.disabled = false;
            btn.textContent = 'Import as New Project';
        }
    }

    showExportPostmanModal() {
        this.showModal('export-postman-modal');
        this.loadExportPostman();
    }

    hideExportPostmanModal() {
        this.hideModal('export-postman-modal');
    }

    async loadExportPostman() {
        try {
            const response = await fetch(`${API_BASE}/export/postman`);
            const result = await response.json();

            if (result.success) {
                document.getElementById('export-postman-textarea').value = JSON.stringify(result.data, null, 2);
            } else {
                alert(`Postman Collection 내보내기 실패: ${result.error}`);
            }
        } catch (error) {
            console.error('Failed to export Postman Collection:', error);
            alert('Postman Collection 내보내기 중 오류가 발생했습니다.');
        }
    }

    copyExportPostmanToClipboard() {
        const textarea = document.getElementById('export-postman-textarea');
        textarea.select();
        document.execCommand('copy');

        const btn = document.getElementById('btn-copy-export-postman');
        const originalText = btn.textContent;
        btn.textContent = '✅ Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }

    downloadExportPostman() {
        const content = document.getElementById('export-postman-textarea').value;
        const blob = new Blob([content], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.currentProject?.name || 'Lumina'}_Postman_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        const btn = document.getElementById('btn-download-export-postman');
        const originalText = btn.textContent;
        btn.textContent = '✅ Downloaded!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }

    setupResizers() {
        const sidebar = document.getElementById('sidebar-panel');
        const mainPanel = document.getElementById('main-panel');
        const responsePanel = document.getElementById('response-panel');
        const sidebarResizer = document.getElementById('resizer-sidebar');
        const responseResizer = document.getElementById('resizer-response');

        if (!sidebar || !sidebarResizer) return;

        let isResizingSidebar = false;
        let isResizingResponse = false;
        let startX = 0;
        let startWidth = 0;

        sidebarResizer.addEventListener('mousedown', (e) => {
            isResizingSidebar = true;
            startX = e.clientX;
            startWidth = sidebar.offsetWidth;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        responseResizer.addEventListener('mousedown', (e) => {
            isResizingResponse = true;
            startX = e.clientX;
            startWidth = responsePanel.offsetWidth;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (isResizingSidebar) {
                const newWidth = startWidth + (e.clientX - startX);
                if (newWidth >= 200 && newWidth <= 600) {
                    sidebar.style.width = newWidth + 'px';
                }
            } else if (isResizingResponse) {
                const newWidth = startWidth - (e.clientX - startX);
                if (newWidth >= 300 && newWidth <= 800) {
                    responsePanel.style.width = newWidth + 'px';
                }
            }
        });

        document.addEventListener('mouseup', () => {
            isResizingSidebar = false;
            isResizingResponse = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        });
    }
}

// 앱 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.app = new LuminaApp();
});
