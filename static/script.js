/**
 * Intelligent Complaint Analytics Platform
 * Frontend Javascript Modules
 */

// Global Fetch Interceptor to handle 401 Unauthorized
const originalFetch = window.fetch;
window.fetch = async function() {
    const response = await originalFetch.apply(this, arguments);
    if (response.status === 401) {
        window.location.href = '/login';
    }
    return response;
};

const App = {
    init() {
        this.ChatModule.init();
        this.ComplaintModule.init();
        this.AnalyzeModule.init();
    },

    /**
     * Chat Assistant Module
     */
    ChatModule: {
        currentSessionId: null,
        
        getCancelledSessions() {
            try {
                const data = localStorage.getItem('cancelledQuickReplies');
                return data ? new Set(JSON.parse(data)) : new Set();
            } catch(e) { return new Set(); }
        },
        
        markSessionCancelled(sessionId) {
            if (!sessionId) return;
            const cancelled = this.getCancelledSessions();
            cancelled.add(sessionId);
            localStorage.setItem('cancelledQuickReplies', JSON.stringify([...cancelled]));
        },

        updateStats(data) {
            const totalEl = document.getElementById('stat-total');
            if (!totalEl) return;

            totalEl.innerText = data.length;
            document.getElementById('stat-pending').innerText = data.filter(i => i.status !== 'resolved').length;
            document.getElementById('stat-resolved').innerText = data.filter(i => i.status === 'resolved').length;

            this.updateChart(data);
        },

        init() {
            this.form = document.getElementById('chat-form');
            this.input = document.getElementById('user-input');
            this.box = document.getElementById('chat-box');
            this.welcomeMsg = document.getElementById('welcome-msg');
            this.historyList = document.getElementById('chat-history-list');
            this.btnNew = document.getElementById('btn-new-chat');
            this.fileInput = document.getElementById('chat-file-input');
            this.attachBtn = document.getElementById('chat-attach-btn');
            this.filePreview = document.getElementById('chat-file-preview');
            this.fileName = document.getElementById('chat-file-name');
            this.fileRemove = document.getElementById('chat-file-remove');

            if (this.form) {
                this.form.addEventListener('submit', this.handleSubmit.bind(this));
            }
            if (this.btnNew) {
                this.btnNew.addEventListener('click', this.newSession.bind(this));
            }
            if (this.attachBtn && this.fileInput) {
                this.attachBtn.addEventListener('click', () => this.fileInput.click());
                this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
            }
            if (this.fileRemove) {
                this.fileRemove.addEventListener('click', this.clearFile.bind(this));
            }

            // Expose to global scope
            window.loadChatSession = this.loadSession.bind(this);
            window.deleteChatSession = this.deleteSession.bind(this);

            if (this.historyList) {
                this.loadHistory();
            }
        },

        newSession() {
            this.currentSessionId = null;
            this.box.innerHTML = '';
            if (this.welcomeMsg) {
                this.welcomeMsg.style.display = 'block';
                this.box.appendChild(this.welcomeMsg);
            }
            this.clearFile();
            this.loadHistory();
        },

        clearFile() {
            if (this.fileInput) this.fileInput.value = '';
            if (this.filePreview) this.filePreview.classList.add('d-none');
            if (this.fileName) this.fileName.textContent = '';
        },

        handleFileSelect(e) {
            const file = e.target.files[0];
            if (file) {
                this.fileName.textContent = file.name;
                this.filePreview.classList.remove('d-none');
            } else {
                this.clearFile();
            }
        },


        async loadHistory() {
            try {
                const res = await fetch('/api/chat/sessions');
                const data = await res.json();
                this.historyList.innerHTML = '';
                
                if (data.length === 0) {
                    this.historyList.innerHTML = '<div class="text-center p-3 text-muted small">No history</div>';
                    return;
                }

                data.forEach(item => {
                    const activeClass = this.currentSessionId === item.session_id ? 'bg-light border-primary' : '';
                    const div = document.createElement('div');
                    div.className = `list-group-item list-group-item-action p-3 ${activeClass}`;
                    div.style.cursor = 'pointer';
                    div.setAttribute('onclick', `loadChatSession('${item.session_id}')`);
                    div.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <strong class="text-truncate" style="max-width: 150px;">${DOMPurify.sanitize(item.title)}</strong>
                            <small class="text-muted">${item.timestamp.split(' ')[0]}</small>
                        </div>
                        <div class="text-end">
                            <button class="btn btn-sm btn-outline-danger p-1 rounded" onclick="deleteChatSession('${item.session_id}'); event.stopPropagation();"><i class="bi bi-trash"></i></button>
                        </div>
                    `;
                    this.historyList.appendChild(div);
                });
            } catch(e) {
                console.error("Failed to load chat history", e);
            }
        },

        async loadSession(sessionId) {
            this.currentSessionId = sessionId;
            try {
                const res = await fetch(`/api/chat/sessions/${sessionId}`);
                const data = await res.json();
                
                this.box.innerHTML = '';
                if (this.welcomeMsg) this.welcomeMsg.style.display = 'none';

                data.forEach(msg => {
                    this.appendMessage(msg.user_message, 'user', msg.file_path);
                    this.appendMessage(msg.ai_response, 'ai');
                });
                
                this.showQuickReplies();
                this.loadHistory(); // refresh active state
            } catch (e) {
                console.error("Failed to load session", e);
            }
        },

        async deleteSession(sessionId) {
            const result = await Swal.fire({title: 'Delete this chat?', icon: 'warning', showCancelButton: true, confirmButtonColor: '#dc3545'});
            if (result.isConfirmed) {
                try {
                    await fetch(`/api/chat/sessions/${sessionId}`, {method: 'DELETE'});
                    if (this.currentSessionId === sessionId) {
                        this.newSession();
                    } else {
                        this.loadHistory();
                    }
                } catch(e) {
                    Swal.fire('Error', 'Deletion failed', 'error');
                }
            }
        },

        async handleSubmit(e) {
            e.preventDefault();
            const msg = this.input.value.trim();
            if (!msg) return;

            if (this.welcomeMsg) this.welcomeMsg.style.display = 'none';
            const file = this.fileInput ? this.fileInput.files[0] : null;
            
            // Optimistic render
            if (file) {
                this.appendMessage(msg, 'user', 'pending');
            } else {
                this.appendMessage(msg, 'user');
            }
            
            this.input.value = '';
            this.removeQuickReplies();
            
            const loadingId = this.showLoading();
            try {
                const formData = new FormData();
                formData.append('message', msg);
                if (this.currentSessionId) formData.append('session_id', this.currentSessionId);
                if (file) formData.append('file', file);

                const res = await fetch('/api/chat', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                this.clearFile();
                this.removeLoading(loadingId);
                
                if (res.ok) {
                    this.currentSessionId = data.session_id;
                    if (file) {
                        await this.loadSession(this.currentSessionId);
                    } else {
                        this.appendMessage(data.response, 'ai');
                        this.showQuickReplies(data.suggestions);
                        this.loadHistory(); // refresh sidebar
                    }
                } else {
                    this.appendMessage('Error: ' + (data.error || 'Unknown error'), 'error');
                }
            } catch (err) {
                this.removeLoading(loadingId);
                this.appendMessage('Connection Error', 'error');
            }
        },

        appendMessage(text, type, filePath = null) {
            const div = document.createElement('div');
            const bubble = document.createElement('div');
            
            div.className = `d-flex mb-3 ${type === 'user' ? 'justify-content-end' : 'justify-content-start'} animate__animated animate__fadeIn`;
            bubble.className = `message-bubble p-3 rounded-4 shadow-sm ${type === 'user' ? 'bg-primary text-white user-bubble' : 'bg-white border ai-bubble'}`;
            bubble.style.maxWidth = '85%';

            let fileHtml = '';
            if (filePath) {
                if (filePath === 'pending') {
                    fileHtml = `<div class="mt-2"><span class="badge bg-light text-primary"><i class="bi bi-paperclip"></i> 附件上傳中...</span></div>`;
                } else {
                    const ext = filePath.split('.').pop().toLowerCase();
                    if (ext === 'pdf' || ext === 'docx' || ext === 'doc') {
                        fileHtml = `<div class="mt-2"><a href="${filePath}" target="_blank" class="btn btn-sm btn-light text-primary"><i class="bi bi-file-earmark-text"></i> 檢視附件</a></div>`;
                    } else if (ext === 'png' || ext === 'jpg' || ext === 'jpeg' || ext === 'gif') {
                        fileHtml = `<div class="mt-2"><a href="${filePath}" target="_blank"><img src="${filePath}" class="img-fluid rounded" style="max-height: 150px;"></a></div>`;
                    } else {
                        fileHtml = `<div class="mt-2"><a href="${filePath}" target="_blank" class="btn btn-sm btn-light text-primary"><i class="bi bi-paperclip"></i> 檢視附件</a></div>`;
                    }
                }
            }

            if (type === 'ai') {
                // Prevent XSS by using DOMPurify
                const rawHtml = marked.parse(text);
                const safeHtml = DOMPurify.sanitize(rawHtml);
                bubble.innerHTML = safeHtml + fileHtml;
                bubble.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
            } else {
                bubble.innerText = text;
                if (fileHtml) {
                    bubble.innerHTML += fileHtml;
                }
            }
            
            div.appendChild(bubble);
            this.box.appendChild(div);
            this.box.scrollTop = this.box.scrollHeight;
            
            if (window.MathJax) {
                MathJax.typesetPromise([bubble]).catch(err => console.error(err));
            }
        },

        showLoading() {
            const id = 'loading-' + Date.now();
            const div = document.createElement('div');
            div.id = id;
            div.innerHTML = `<div class="d-flex mb-3"><div class="bg-white border p-3 rounded-4 shadow-sm typing-dots"><span></span><span></span><span></span></div></div>`;
            this.box.appendChild(div);
            this.box.scrollTop = this.box.scrollHeight;
            return id;
        },

        removeLoading(id) { 
            const el = document.getElementById(id); 
            if (el) el.remove(); 
        },

        showQuickReplies(dynamicSuggestions = []) {
            this.removeQuickReplies();
            if (this.currentSessionId && this.getCancelledSessions().has(this.currentSessionId)) return;

            let selected = [];
            if (dynamicSuggestions && dynamicSuggestions.length > 0) {
                selected = dynamicSuggestions.slice(0, 3);
            } else {
                // Fallback generic questions if API didn't provide any
                selected = [
                    "請提供更多細節",
                    "這代表什麼意思？",
                    "還有其他建議嗎？"
                ];
            }

            const div = document.createElement('div');
            div.id = 'quick-replies';
            div.className = 'd-flex flex-wrap gap-2 mb-4 pb-4 justify-content-center animate__animated animate__fadeInUp';
            
            selected.forEach(q => {
                const btn = document.createElement('button');
                btn.className = 'btn btn-sm btn-outline-primary rounded-pill px-3 py-1';
                btn.textContent = q;
                btn.onclick = () => {
                    this.input.value = q;
                    this.removeQuickReplies();
                    this.form.querySelector('button[type="submit"]').click();
                };
                div.appendChild(btn);
            });

            const cancelBtn = document.createElement('button');
            cancelBtn.className = 'btn btn-sm btn-outline-secondary rounded-pill px-3 py-1';
            cancelBtn.textContent = '取消';
            cancelBtn.onclick = () => {
                this.removeQuickReplies();
                if (this.currentSessionId) this.markSessionCancelled(this.currentSessionId);
            };
            div.appendChild(cancelBtn);

            this.box.appendChild(div);
            this.box.scrollTop = this.box.scrollHeight;
        },

        removeQuickReplies() {
            const existing = document.getElementById('quick-replies');
            if (existing) existing.remove();
        }
    },

    /**
     * Complaint Management Module
     */
    ComplaintModule: {
        chartInstance: null,

        init() {
            this.btn = document.getElementById('submit-complaint');
            this.input = document.getElementById('complaint-text');
            this.inputName = document.getElementById('complaint-name');
            this.inputEmail = document.getElementById('complaint-email');
            this.inputAccount = document.getElementById('complaint-account');
            this.inputDept = document.getElementById('complaint-dept');
            this.list = document.getElementById('complaint-list');
            this.btnOllamaRefine = document.getElementById('btn-ollama-refine');

            this.inputUserId = document.getElementById('complaint-user-id');
            
            if (this.inputUserId) {
                this.loadUsersForDropdown();
            }

            if (this.list) {
                // Expose to global scope for HTML onclick handlers
                window.loadComplaints = this.loadComplaints.bind(this);
                window.deleteComplaint = this.deleteComplaint.bind(this);
                window.submitReply = this.submitReply.bind(this);
                window.resolveComplaint = this.resolveComplaint.bind(this);
                
                this.loadComplaints();
            }

            if (this.btn) {
                this.btn.addEventListener('click', this.handleSubmit.bind(this));
            }
            
            if (this.input && this.btnOllamaRefine) {
                this.input.addEventListener('input', () => {
                    if (this.input.value.trim().length > 0) {
                        this.btnOllamaRefine.classList.remove('d-none');
                    } else {
                        this.btnOllamaRefine.classList.add('d-none');
                    }
                });
                
                this.btnOllamaRefine.addEventListener('click', async () => {
                    const text = this.input.value.trim();
                    if (!text) return;
                    
                    const originalText = this.btnOllamaRefine.innerHTML;
                    this.btnOllamaRefine.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 潤飾中...';
                    this.btnOllamaRefine.disabled = true;
                    this.input.disabled = true;
                    
                    try {
                        const res = await fetch('/api/complaints/refine', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({text: text})
                        });
                        if (res.ok) {
                            const data = await res.json();
                            this.input.value = data.refined_text;
                        } else {
                            Swal.fire('錯誤', 'AI 潤飾失敗', 'error');
                        }
                    } catch(e) {
                        Swal.fire('錯誤', '連線失敗', 'error');
                    } finally {
                        this.btnOllamaRefine.innerHTML = originalText;
                        this.btnOllamaRefine.disabled = false;
                        this.input.disabled = false;
                    }
                });
            }
        },

        async loadUsersForDropdown() {
            try {
                const res = await fetch('/api/users');
                if (res.ok) {
                    const users = await res.json();
                    users.forEach(u => {
                        const option = document.createElement('option');
                        option.value = u.id;
                        option.textContent = `${u.username} (${u.role})`;
                        this.inputUserId.appendChild(option);
                    });
                }
            } catch(e) {
                console.error("Failed to load users for dropdown", e);
            }
        },

        async handleSubmit() {
            const content = this.input.value.trim();
            const cName = this.inputName ? this.inputName.value.trim() : '';
            const cEmail = this.inputEmail ? this.inputEmail.value.trim() : '';
            const cAccount = this.inputAccount ? this.inputAccount.value.trim() : '';
            const cDept = this.inputDept ? this.inputDept.value.trim() : '';

            if (!cName || !cEmail || !content) return Swal.fire('Notice', 'Please fill in Name, Email and Content', 'warning');

            const fileInput = document.getElementById('complaint-image');
            const file = fileInput ? fileInput.files[0] : null;

            const formData = new FormData();
            formData.append('content', content);
            formData.append('customer_name', cName);
            formData.append('email', cEmail);
            formData.append('account', cAccount);
            formData.append('department', cDept);
            
            if (this.inputUserId && this.inputUserId.value) {
                formData.append('user_id', this.inputUserId.value);
            }
            
            if (file) {
                formData.append('image', file);
            }

            try {
                const res = await fetch('/api/complaints', {
                    method: 'POST',
                    body: formData
                });
                
                if (res.ok) {
                    this.input.value = '';
                    if (this.inputName) this.inputName.value = '';
                    if (this.inputEmail) this.inputEmail.value = '';
                    if (this.inputAccount) this.inputAccount.value = '';
                    if (this.inputDept) this.inputDept.value = '';
                    if (this.inputUserId) this.inputUserId.value = '';
                    if (fileInput) fileInput.value = '';
                    Swal.fire({icon: 'success', title: 'Submitted', timer: 1500, showConfirmButton: false});
                    this.loadComplaints();
                } else {
                    const data = await res.json();
                    Swal.fire('Error', data.error || 'Submission failed', 'error');
                }
            } catch(e) {
                Swal.fire('Error', 'Connection failed', 'error');
            }
        },

        async loadComplaints() {
            if (!this.list) return;
            this.updateDashboard();

            try {
                const res = await fetch('/api/complaints');
                const data = await res.json();
                
                this.list.innerHTML = '';
                if (data.length === 0) {
                    this.list.innerHTML = '<div class="text-center p-5 text-muted">No records found</div>';
                    return;
                }

                data.forEach(item => {
                    const isResolved = item.status === 'resolved';
                    const badge = isResolved 
                        ? '<span class="badge bg-success rounded-pill">Resolved</span>' 
                        : '<span class="badge bg-warning text-dark rounded-pill">Pending</span>';
                    
                    // Sanitize user inputs/outputs
                    const safeContent = DOMPurify.sanitize(item.content);
                    const safeReply = item.admin_reply ? DOMPurify.sanitize(item.admin_reply) : '';

                    let replyHtml = '';
                    if (item.admin_reply) {
                        let splitReplies = safeReply.split(/(?=\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}\])/);
                        splitReplies = splitReplies.filter(r => r.trim());
                        splitReplies.reverse();
                        
                        replyHtml = `<div class="mt-3"><strong>歷史回覆 / Reply History:</strong>` + 
                            splitReplies.map(r => {
                                let content = r.trim().replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                                return `<div class="mt-2 p-3 bg-light border-start border-4 border-success" style="white-space: pre-wrap;">${content}</div>`;
                            }).join('') +
                            `</div>`;
                    }
                        
                    let imageHtml = '';
                    if (item.image_path) {
                        const ext = item.image_path.split('.').pop().toLowerCase();
                        if (ext === 'pdf' || ext === 'docx' || ext === 'doc') {
                            imageHtml = `<div class="mt-3"><a href="${item.image_path}" target="_blank" class="btn btn-sm btn-outline-secondary"><i class="bi bi-file-earmark-text"></i> 檢視附加檔案</a></div>`;
                        } else {
                            imageHtml = `<div class="mt-3"><a href="${item.image_path}" target="_blank"><img src="${item.image_path}" loading="lazy" class="img-fluid rounded border" style="max-height: 200px;"></a></div>`;
                        }
                    }

                    let actionBtns = '';
                    if (window.USER_ROLE) {
                        const replyBtn = `<button class="btn btn-sm btn-outline-primary rounded-pill" onclick="submitReply(${item.id})">回覆</button>`;
                        const resolveBtn = !isResolved 
                            ? `<button class="btn btn-sm btn-success rounded-pill text-white" onclick="resolveComplaint(${item.id})">標記處理完成</button>` : '';
                        actionBtns = `${replyBtn} ${resolveBtn} <button class="btn btn-sm btn-outline-danger rounded-pill" onclick="deleteComplaint(${item.id})">Delete</button>`;
                    }

                    let userInfo = [];
                    if (item.customer_name) userInfo.push(`<strong>${DOMPurify.sanitize(item.customer_name)}</strong>`);
                    if (item.account) userInfo.push(`(${DOMPurify.sanitize(item.account)})`);
                    if (item.department) userInfo.push(`[${DOMPurify.sanitize(item.department)}]`);
                    if (item.email) userInfo.push(`- <a href="mailto:${DOMPurify.sanitize(item.email)}">${DOMPurify.sanitize(item.email)}</a>`);
                    
                    const div = document.createElement('div');
                    div.className = 'list-group-item list-group-item-action p-4 border-bottom';
                    div.innerHTML = `
                        <div class="d-flex w-100 justify-content-between align-items-center mb-2">
                            <small class="text-muted">${item.timestamp}</small>
                            <div>${badge}</div>
                        </div>
                        <div class="mb-2 text-primary small"><i class="bi bi-person-circle"></i> ${userInfo.join(' ')}</div>
                        <h5 class="mb-3 fw-bold">${safeContent}</h5>
                        ${imageHtml}
                        ${replyHtml}
                        <div class="mt-3 text-end">
                            ${actionBtns}
                        </div>
                    `;
                    this.list.appendChild(div);
                });
            } catch(e) {
                console.error("Failed to load complaints", e);
            }
        },

        async deleteComplaint(id) {
            const result = await Swal.fire({title: 'Delete this record?', icon: 'warning', showCancelButton: true, confirmButtonColor: '#dc3545'});
            if (result.isConfirmed) {
                try {
                    await fetch(`/api/complaints/${id}`, {method: 'DELETE'});
                    this.loadComplaints();
                    Swal.fire('Deleted', '', 'success');
                } catch(e) {
                    Swal.fire('Error', 'Deletion failed', 'error');
                }
            }
        },

        async resolveComplaint(id) {
            const result = await Swal.fire({title: 'Mark as Resolved?', icon: 'question', showCancelButton: true});
            if (result.isConfirmed) {
                try {
                    await fetch(`/api/complaints/${id}/resolve`, {method: 'POST'});
                    this.loadComplaints();
                    Swal.fire('Resolved', '', 'success');
                } catch(e) {
                    Swal.fire('Error', 'Failed to resolve', 'error');
                }
            }
        },

        async submitReply(id) {
            const titleText = window.USER_ROLE === 'member' ? '回覆工單' : '回覆工單 (Reply)';
            
            // Find the original complaint text from the UI
            const complaintCard = document.querySelector(`button[onclick="submitReply(${id})"]`)?.closest('.list-group-item');
            const originalComplaintText = complaintCard ? complaintCard.querySelector('h5').innerText : "";

            const htmlContent = `
                <div class="mb-2 text-start">
                    <div class="d-flex justify-content-between align-items-center mb-2 px-1">
                        <span class="text-secondary small fw-bold">草擬回覆內容</span>
                        <button type="button" id="swal-btn-refine" class="btn btn-sm btn-outline-primary rounded-pill d-none" style="font-size: 0.75rem;">
                            <i class="bi bi-magic"></i> AI 擴寫回覆
                        </button>
                    </div>
                    <textarea id="swal-reply-input" class="swal2-textarea m-0 w-100" style="min-height: 400px; resize: none;" placeholder="請輸入回覆內容..."></textarea>
                </div>
            `;

            const {value: text, isConfirmed} = await Swal.fire({
                title: titleText, 
                html: htmlContent,
                width: '800px',
                showCancelButton: true,
                didOpen: () => {
                    const input = document.getElementById('swal-reply-input');
                    const btn = document.getElementById('swal-btn-refine');
                    
                    input.addEventListener('input', () => {
                        if (input.value.trim().length > 0) {
                            btn.classList.remove('d-none');
                        } else {
                            btn.classList.add('d-none');
                        }
                    });

                    btn.addEventListener('click', async () => {
                        const draft = input.value.trim();
                        if (!draft) return;
                        
                        btn.disabled = true;
                        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> 處理中...';
                        
                        try {
                            const response = await fetch('/api/complaints/refine_reply', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({ original_complaint: originalComplaintText, draft_reply: draft })
                            });
                            
                            const data = await response.json();
                            if (response.ok && data.refined_text) {
                                input.value = data.refined_text;
                            } else {
                                Swal.showValidationMessage('潤飾失敗，請稍後再試');
                            }
                        } catch (e) {
                            console.error(e);
                            Swal.showValidationMessage('連線錯誤，請稍後再試');
                        } finally {
                            btn.disabled = false;
                            btn.innerHTML = '<i class="bi bi-magic"></i> 修改描述';
                        }
                    });
                },
                preConfirm: () => {
                    const val = document.getElementById('swal-reply-input').value;
                    if (!val) {
                        Swal.showValidationMessage('回覆內容不能為空');
                    }
                    return val;
                }
            });

            if (isConfirmed && text) {
                try {
                    await fetch(`/api/complaints/${id}/reply`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({reply: text})
                    });
                    this.loadComplaints();
                    Swal.fire('Success', '回覆成功', 'success');
                } catch(e) {
                    Swal.fire('Error', 'Failed to submit reply', 'error');
                }
            }
        },

        async updateDashboard() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();

                ['total', 'pending', 'resolved'].forEach(key => {
                    const el = document.getElementById(`stat-${key}`);
                    if (el) el.innerText = data[key];
                });

                const ctx = document.getElementById('statusChart');
                if (ctx) {
                    if (this.chartInstance) this.chartInstance.destroy();
                    this.chartInstance = new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: ['Pending', 'Resolved'],
                            datasets: [{data: [data.pending, data.resolved], backgroundColor: ['#ffc107', '#198754'], borderWidth: 0}]
                        },
                        options: {responsive: true, maintainAspectRatio: false, cutout: '75%', plugins: {legend: {position: 'right'}}}
                    });
                }
            } catch(e) {
                console.error("Failed to update dashboard", e);
            }
        }
    },

    /**
     * AI Analysis Module
     */
    AnalyzeModule: {
        currentRecordId: null,

        init() {
            this.input = document.getElementById('analyze-input');
            this.btn = document.getElementById('btn-analyze');
            this.box = document.getElementById('analyze-result-box');
            this.content = document.getElementById('analyze-content');
            this.historyList = document.getElementById('analyze-history-list');
            this.btnNew = document.getElementById('btn-new-analyze');
            this.selectedEmoji = '';

            if (this.btn) {
                this.btn.addEventListener('click', this.handleAnalyze.bind(this));
            }
            if (this.btnNew) {
                this.btnNew.addEventListener('click', this.newAnalysis.bind(this));
            }
            
            this.chatInput = document.getElementById('analyze-chat-input');
            this.chatBtn = document.getElementById('btn-analyze-chat-send');
            if (this.chatBtn) {
                this.chatBtn.addEventListener('click', this.sendAnalyzeChat.bind(this));
            }
            if (this.chatInput) {
                this.chatInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') this.sendAnalyzeChat();
                });
            }

            // Emoji select logic
            const emojiSelect = document.getElementById('emoji-select');
            if (emojiSelect) {
                emojiSelect.addEventListener('change', (e) => {
                    this.selectedEmoji = e.target.value;
                });
            }

            // Expose to global scope
            window.loadAnalyzeRecord = this.loadRecord.bind(this);
            window.deleteAnalyzeRecord = this.deleteRecord.bind(this);

            if (this.historyList) {
                this.loadHistory();
            }
        },

        newAnalysis() {
            this.currentRecordId = null;
            this.input.value = '';
            this.selectedEmoji = '';
            const emojiSelect = document.getElementById('emoji-select');
            if (emojiSelect) emojiSelect.value = '';
            this.box.style.display = 'none';
            this.content.innerHTML = '';
            this.loadHistory();
        },

        async loadHistory() {
            try {
                const res = await fetch('/api/analyze/history');
                const data = await res.json();
                this.historyList.innerHTML = '';
                
                if (data.length === 0) {
                    this.historyList.innerHTML = '<div class="text-center p-3 text-muted small">No history</div>';
                    return;
                }

                // store globally so we can load them easily
                window._analyzeData = data;

                data.forEach(item => {
                    const activeClass = this.currentRecordId === item.id ? 'bg-light border-warning' : '';
                    const div = document.createElement('div');
                    const title = item.text_input.substring(0, 30) + (item.text_input.length > 30 ? '...' : '');
                    div.className = `list-group-item list-group-item-action p-3 ${activeClass}`;
                    div.style.cursor = 'pointer';
                    div.setAttribute('onclick', `loadAnalyzeRecord(${item.id})`);
                    div.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <strong class="text-truncate" style="max-width: 150px;">${DOMPurify.sanitize(title)}</strong>
                            <small class="text-muted">${item.timestamp.split(' ')[0]}</small>
                        </div>
                        <div class="text-end">
                            <button class="btn btn-sm btn-outline-danger p-1 rounded" onclick="deleteAnalyzeRecord(${item.id}); event.stopPropagation();"><i class="bi bi-trash"></i></button>
                        </div>
                    `;
                    this.historyList.appendChild(div);
                });
            } catch(e) {
                console.error("Failed to load analyze history", e);
            }
        },

        loadRecord(id) {
            const record = window._analyzeData.find(r => r.id === id);
            if (!record) return;
            this.currentRecordId = id;
            this.input.value = record.text_input.replace(/\[顧客心情：.*?\] \n/, '');
            this.box.style.display = 'block';
            this.formatResult(record.analysis_result);
            try {
                const history = record.chat_history ? JSON.parse(record.chat_history) : [];
                this.renderAnalyzeChat(history);
            } catch (e) {
                this.renderAnalyzeChat([]);
            }
            this.loadHistory(); // refresh active state
        },

        async deleteRecord(id) {
            const result = await Swal.fire({title: 'Delete this analysis?', icon: 'warning', showCancelButton: true, confirmButtonColor: '#dc3545'});
            if (result.isConfirmed) {
                try {
                    await fetch(`/api/analyze/${id}`, {method: 'DELETE'});
                    if (this.currentRecordId === id) {
                        this.newAnalysis();
                    } else {
                        this.loadHistory();
                    }
                } catch(e) {
                    Swal.fire('Error', 'Deletion failed', 'error');
                }
            }
        },

        formatResult(resultText) {
            const rawHtml = window.marked ? marked.parse(resultText) : resultText;
            const safeResult = DOMPurify.sanitize(rawHtml);
            this.content.innerHTML = safeResult
                .replace('情緒分數：', '<strong class="text-danger">情緒分數：</strong>')
                .replace('情緒標籤：', '<strong class="text-primary">情緒標籤：</strong>')
                .replace('關鍵訴求：', '<strong class="text-dark">關鍵訴求：</strong>')
                .replace('建議回覆：', '<div class="mt-3 p-3 bg-white border-start border-4 border-success rounded"><strong>💡 建議回覆：</strong><br>') + '</div>';
            this.content.querySelectorAll('pre code').forEach(el => {
                if (window.hljs) hljs.highlightElement(el);
            });
            this.content.style.whiteSpace = 'normal'; // Reset from pre-wrap since we use HTML now
            
            if (window.MathJax) {
                MathJax.typesetPromise([this.content]).catch(err => console.error(err));
            }
        },

        async handleAnalyze() {
            if (!this.selectedEmoji) return Swal.fire('提示', '請選擇當下心情 (必填)', 'warning');
            
            const text = this.input.value.trim();
            if (!text) return Swal.fire('提示', '請貼上客戶抱怨內容', 'warning');

            // Combine emoji with text if selected
            const payloadText = this.selectedEmoji ? `[顧客心情：${this.selectedEmoji}] \n${text}` : text;

            this.btn.disabled = true;
            this.btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Analyzing...';
            this.box.style.display = 'none';

            try {
                const res = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: payloadText})
                });
                const data = await res.json();
                
                if (res.ok) {
                    this.currentRecordId = data.id || null;
                    this.formatResult(data.result);
                    this.renderAnalyzeChat([]);
                    this.box.style.display = 'block';
                    this.loadHistory();
                } else {
                    Swal.fire('Error', data.error || '分析失敗', 'error');
                }
            } catch(e) {
                console.error(e);
                Swal.fire('Error', '連線錯誤', 'error');
            } finally {
                this.btn.disabled = false;
                this.btn.innerHTML = '<i class="bi bi-magic"></i> 開始分析';
            }
        },

        renderAnalyzeChat(history) {
            const container = document.getElementById('analyze-chat-history');
            if (!container) return;
            container.innerHTML = '';
            
            if (!history || history.length === 0) {
                container.innerHTML = '<div class="text-center text-muted small py-3">目前還沒有追問紀錄，請在下方輸入您的問題。</div>';
                return;
            }
            
            history.forEach(msg => {
                const div = document.createElement('div');
                div.className = `mb-3 p-3 rounded-4 ${msg.role === 'user' ? 'bg-primary text-white ms-5' : 'bg-white border me-5 shadow-sm'}`;
                const roleIcon = msg.role === 'user' ? '<i class="bi bi-person-fill"></i>' : '<i class="bi bi-robot"></i>';
                
                let contentHtml = '';
                if (msg.role === 'ai') {
                    contentHtml = DOMPurify.sanitize(window.marked ? marked.parse(msg.content) : msg.content);
                } else {
                    contentHtml = DOMPurify.sanitize(msg.content).replace(/\n/g, '<br>');
                }

                div.innerHTML = `<strong>${roleIcon} ${msg.role === 'user' ? '您' : 'AI 客服顧問'}</strong><div class="mt-2" style="${msg.role === 'user' ? '' : ''} font-size: 0.95rem; line-height: 1.6;">${contentHtml}</div>`;
                container.appendChild(div);
                
                // Highlight code blocks
                if (msg.role === 'ai') {
                    div.querySelectorAll('pre code').forEach(el => {
                        if (window.hljs) hljs.highlightElement(el);
                    });
                }
            });
            container.scrollTop = container.scrollHeight;
            
            if (window.MathJax) {
                MathJax.typesetPromise([container]).catch(err => console.error(err));
            }
        },

        async sendAnalyzeChat() {
            if (!this.currentRecordId) return;
            const message = this.chatInput.value.trim();
            if (!message) return;
            
            this.chatBtn.disabled = true;
            this.chatInput.disabled = true;
            this.chatBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
            
            // Optimistically add user message
            const container = document.getElementById('analyze-chat-history');
            if (container.innerHTML.includes('目前還沒有追問紀錄')) {
                container.innerHTML = '';
            }
            const div = document.createElement('div');
            div.className = 'mb-3 p-3 rounded-4 bg-primary text-white ms-5 shadow-sm';
            div.innerHTML = `<strong><i class="bi bi-person-fill"></i> 您</strong><div class="mt-2" style="font-size: 0.95rem;">${DOMPurify.sanitize(message).replace(/\n/g, '<br>')}</div>`;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
            
            if (window.MathJax) {
                MathJax.typesetPromise([div]).catch(err => console.error(err));
            }
            
            try {
                const res = await fetch(`/api/analyze/${this.currentRecordId}/chat`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message})
                });
                const data = await res.json();
                
                if (res.ok) {
                    this.renderAnalyzeChat(data.history);
                    this.chatInput.value = '';
                    this.loadHistory(); // Refresh history data silently
                } else {
                    Swal.fire('Error', data.error || '傳送失敗', 'error');
                }
            } catch(e) {
                console.error(e);
                Swal.fire('Error', '連線錯誤', 'error');
            } finally {
                this.chatBtn.disabled = false;
                this.chatInput.disabled = false;
                this.chatBtn.innerHTML = '<i class="bi bi-send-fill"></i> 發送';
                this.chatInput.focus();
            }
        }
    },

    /**
     * User Management Module
     */
    UserModule: {
        init() {
            this.modalEl = document.getElementById('userModal');
            if (this.modalEl) {
                this.modal = new bootstrap.Modal(this.modalEl);
                this.tableBody = document.getElementById('userTableBody');
                
                document.getElementById('nav-user-btn').addEventListener('click', () => {
                    this.loadUsers();
                    this.modal.show();
                });
                
                document.getElementById('addUserForm').addEventListener('submit', this.handleAddUser.bind(this));

                const toggleBtn = document.getElementById('togglePassword');
                const passInput = document.getElementById('newPassword');
                if (toggleBtn && passInput) {
                    toggleBtn.addEventListener('click', () => {
                        const type = passInput.getAttribute('type') === 'password' ? 'text' : 'password';
                        passInput.setAttribute('type', type);
                        toggleBtn.innerHTML = type === 'password' ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
                    });
                }
                
                window.deleteUser = this.deleteUser.bind(this);
                window.resetPassword = this.resetPassword.bind(this);
                
                window.toggleRowPassword = function(btn) {
                    const input = btn.previousElementSibling;
                    if (input.type === 'password') {
                        input.type = 'text';
                        btn.innerHTML = '<i class="bi bi-eye-slash"></i>';
                    } else {
                        input.type = 'password';
                        btn.innerHTML = '<i class="bi bi-eye"></i>';
                    }
                };
            }
        },

        async loadUsers() {
            try {
                const res = await fetch('/api/users');
                if (!res.ok) return;
                const users = await res.json();
                
                this.tableBody.innerHTML = '';
                users.forEach(user => {
                    let roleBadge = '';
                    if (user.role === 'superadmin') roleBadge = '<span class="badge bg-danger">主管理</span>';
                    else if (user.role === 'admin') roleBadge = '<span class="badge bg-secondary">客服/管理員</span>';
                    else roleBadge = '<span class="badge bg-success">會員</span>';
                        
                    const deleteBtn = (user.username === 'admin' || window.USER_ROLE !== 'superadmin')
                        ? '' // Protect default admin visually or hide if not superadmin
                        : `<button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${user.id})">刪除</button>`;
                        
                    const resetBtn = (user.username === 'admin' || window.USER_ROLE !== 'superadmin')
                        ? ''
                        : `<button class="btn btn-sm btn-outline-warning me-2" onclick="resetPassword(${user.id}, '${DOMPurify.sanitize(user.username)}')">重設密碼</button>`;

                    const passContent = (user.password_plain && window.USER_ROLE === 'superadmin')
                        ? `<div class="input-group input-group-sm" style="width: 130px;">
                               <input type="password" class="form-control text-center bg-white border-0 py-0" value="${DOMPurify.sanitize(user.password_plain)}" readonly>
                               <button class="btn btn-outline-secondary py-0 px-2 toggle-pwd-btn" type="button" onclick="toggleRowPassword(this)"><i class="bi bi-eye"></i></button>
                           </div>`
                        : (user.password_plain ? `<span class="text-muted small">********</span>` : `<span class="text-muted small">已加密</span>`);

                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${user.id}</td>
                        <td class="fw-bold">${DOMPurify.sanitize(user.username)}</td>
                        <td>${passContent}</td>
                        <td>${user.name ? DOMPurify.sanitize(user.name) : '-'}</td>
                        <td>${user.email ? DOMPurify.sanitize(user.email) : '-'}</td>
                        <td>${roleBadge}</td>
                        <td class="text-muted small">${user.created_at}</td>
                        <td class="text-end">${resetBtn}${deleteBtn}</td>
                    `;
                    this.tableBody.appendChild(tr);
                });
            } catch(e) {
                console.error("Failed to load users", e);
            }
        },

        async handleAddUser(e) {
            e.preventDefault();
            const usernameInput = document.getElementById('newUsername');
            const passwordInput = document.getElementById('newPassword');
            const roleInput = document.getElementById('newRole');
            const nameInput = document.getElementById('newName');
            const emailInput = document.getElementById('newEmail');
            
            try {
                const res = await fetch('/api/users', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        username: usernameInput.value.trim(),
                        password: passwordInput.value,
                        role: roleInput ? roleInput.value : 'admin',
                        name: nameInput ? nameInput.value.trim() : '',
                        email: emailInput ? emailInput.value.trim() : ''
                    })
                });
                
                const data = await res.json();
                if (res.ok) {
                    Swal.fire({icon: 'success', title: '新增成功', timer: 1500, showConfirmButton: false});
                    usernameInput.value = '';
                    passwordInput.value = '';
                    this.loadUsers();
                } else {
                    Swal.fire('Error', data.error || '新增失敗', 'error');
                }
            } catch(e) {
                Swal.fire('Error', '連線失敗', 'error');
            }
        },

        async deleteUser(id) {
            const result = await Swal.fire({title: '確定刪除此帳號？', icon: 'warning', showCancelButton: true, confirmButtonColor: '#dc3545'});
            if (result.isConfirmed) {
                try {
                    const res = await fetch(`/api/users/${id}`, {method: 'DELETE'});
                    const data = await res.json();
                    if (res.ok) {
                        this.loadUsers();
                        Swal.fire('已刪除', '', 'success');
                    } else {
                        Swal.fire('Error', data.error || '刪除失敗', 'error');
                    }
                } catch(e) {
                    Swal.fire('Error', '連線失敗', 'error');
                }
            }
        },

        async resetPassword(id, username) {
            const { value: password } = await Swal.fire({
                title: `重設 ${username} 的密碼`,
                input: 'text',
                inputPlaceholder: '請輸入新密碼',
                showCancelButton: true,
                confirmButtonText: '確認重設',
                cancelButtonText: '取消',
                inputValidator: (value) => {
                    if (!value) {
                        return '密碼不能為空！'
                    }
                }
            });

            if (password) {
                try {
                    const res = await fetch(`/api/users/${id}/reset_password`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ password })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        Swal.fire('成功', '密碼重設成功', 'success');
                    } else {
                        Swal.fire('錯誤', data.error || '重設失敗', 'error');
                    }
                } catch(e) {
                    Swal.fire('Error', '連線失敗', 'error');
                }
            }
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
    App.UserModule.init();
});