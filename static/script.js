document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. AI 聊天模組 ---
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const welcomeMsg = document.getElementById('welcome-msg');

    if(chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const msg = userInput.value.trim();
            if(!msg) return;

            if(welcomeMsg) welcomeMsg.style.display = 'none';
            appendMessage(msg, 'user');
            userInput.value = '';
            
            const loadingId = showLoading();
            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                const data = await res.json();
                removeLoading(loadingId);
                if(res.ok) appendMessage(data.response, 'ai');
                else appendMessage('Error: ' + data.error, 'error');
            } catch(err) {
                removeLoading(loadingId);
                appendMessage('連線錯誤', 'error');
            }
        });
    }

    function appendMessage(text, type) {
        const div = document.createElement('div');
        const bubble = document.createElement('div');
        div.className = `d-flex mb-3 ${type === 'user' ? 'justify-content-end' : 'justify-content-start'} animate__animated animate__fadeIn`;
        bubble.className = `message-bubble p-3 rounded-4 shadow-sm ${type === 'user' ? 'bg-primary text-white user-bubble' : 'bg-white border ai-bubble'}`;
        bubble.style.maxWidth = '85%';

        if(type === 'ai') {
            bubble.innerHTML = marked.parse(text);
            bubble.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
        } else {
            bubble.textContent = text;
        }
        div.appendChild(bubble);
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function showLoading() {
        const id = 'loading-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.innerHTML = `<div class="d-flex mb-3"><div class="bg-white border p-3 rounded-4 shadow-sm typing-dots"><span></span><span></span><span></span></div></div>`;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
        return id;
    }
    function removeLoading(id) { const el = document.getElementById(id); if(el) el.remove(); }


    // --- 2. 工單模組 (CRUD + Chart) ---
    window.loadComplaints = loadComplaints;
    window.deleteComplaint = deleteComplaint;
    window.adminReply = adminReply;

    const complaintBtn = document.getElementById('submit-complaint');
    const complaintInput = document.getElementById('complaint-text');
    const complaintList = document.getElementById('complaint-list');
    let chartInstance = null;

    if(complaintList) loadComplaints();

    if(complaintBtn) {
        complaintBtn.addEventListener('click', async () => {
            const content = complaintInput.value.trim();
            if(!content) return Swal.fire('提示', '請輸入內容', 'warning');

            const res = await fetch('/api/complaints', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({content})
            });
            if(res.ok) {
                complaintInput.value = '';
                Swal.fire({icon: 'success', title: '提交成功', timer: 1500, showConfirmButton: false});
                loadComplaints();
            }
        });
    }

    async function loadComplaints() {
        if(!complaintList) return;
        updateDashboard(); // 更新圖表

        const res = await fetch('/api/complaints');
        const data = await res.json();
        
        complaintList.innerHTML = '';
        if(data.length === 0) {
            complaintList.innerHTML = '<div class="text-center p-5 text-muted">無記錄</div>';
            return;
        }

        data.forEach(item => {
            const badge = item.status === 'resolved' 
                ? '<span class="badge bg-success rounded-pill">已結案</span>' 
                : '<span class="badge bg-warning text-dark rounded-pill">待處理</span>';
            
            const reply = item.admin_reply 
                ? `<div class="mt-3 p-3 bg-light border-start border-4 border-success small"><strong>客服回覆：</strong> ${item.admin_reply}</div>` 
                : '';

            const replyBtn = item.status !== 'resolved'
                ? `<button class="btn btn-sm btn-outline-primary rounded-pill" onclick="adminReply(${item.id})">模擬回覆</button>` : '';

            const div = document.createElement('div');
            div.className = 'list-group-item p-4 border-bottom';
            div.innerHTML = `
                <div class="d-flex justify-content-between mb-2"><small class="text-muted">${item.timestamp}</small>${badge}</div>
                <h6 class="mb-3 fw-bold" style="white-space: pre-wrap;">${item.content}</h6>
                ${reply}
                <div class="mt-3 d-flex justify-content-end gap-2">${replyBtn}
                <button class="btn btn-sm btn-outline-danger rounded-pill" onclick="deleteComplaint(${item.id})">刪除</button></div>
            `;
            complaintList.appendChild(div);
        });
    }

    async function deleteComplaint(id) {
        const result = await Swal.fire({title: '確定刪除?', icon: 'warning', showCancelButton: true, confirmButtonColor: '#dc3545'});
        if(result.isConfirmed) {
            await fetch(`/api/complaints/${id}`, {method: 'DELETE'});
            loadComplaints();
            Swal.fire('已刪除', '', 'success');
        }
    }

    async function adminReply(id) {
        const {value: text} = await Swal.fire({title: '管理員回覆', input: 'textarea', showCancelButton: true});
        if(text) {
            await fetch(`/api/complaints/${id}/reply`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({reply: text})
            });
            loadComplaints();
            Swal.fire('成功', '已回覆並結案', 'success');
        }
    }

    async function updateDashboard() {
        const res = await fetch('/api/stats');
        const data = await res.json();

        // 更新數字
        ['total', 'pending', 'resolved'].forEach(key => {
            const el = document.getElementById(`stat-${key}`);
            if(el) el.innerText = data[key];
        });

        // 更新 Chart.js
        const ctx = document.getElementById('statusChart');
        if(ctx) {
            if(chartInstance) chartInstance.destroy();
            chartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['待處理', '已結案'],
                    datasets: [{data: [data.pending, data.resolved], backgroundColor: ['#ffc107', '#198754'], borderWidth: 0}]
                },
                options: {responsive: true, maintainAspectRatio: false, cutout: '75%', plugins: {legend: {position: 'right'}}}
            });
        }
    }

    // --- 3. AI 輿情分析模組 ---
    const analyzeBtn = document.getElementById('btn-analyze');
    const analyzeInput = document.getElementById('analyze-input');
    const analyzeBox = document.getElementById('analyze-result-box');
    const analyzeContent = document.getElementById('analyze-content');

    if(analyzeBtn) {
        analyzeBtn.addEventListener('click', async () => {
            const text = analyzeInput.value.trim();
            if(!text) return Swal.fire('提示', '請輸入文字', 'info');

            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> 分析中...';
            analyzeBox.style.display = 'none';

            try {
                const res = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text})
                });
                const data = await res.json();
                if(res.ok) {
                    analyzeBox.style.display = 'block';
                    analyzeContent.innerHTML = data.result
                        .replace('情緒分數：', '<strong class="text-danger">情緒分數：</strong>')
                        .replace('情緒標籤：', '<strong class="text-primary">情緒標籤：</strong>')
                        .replace('關鍵訴求：', '<strong class="text-dark">關鍵訴求：</strong>')
                        .replace('建議回覆：', '<div class="mt-3 p-3 bg-white border-start border-4 border-success rounded"><strong>💡 建議回覆：</strong><br>') + '</div>';
                } else {
                    Swal.fire('錯誤', data.error, 'error');
                }
            } catch(e) {
                Swal.fire('錯誤', '連線失敗', 'error');
            } finally {
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = '<i class="bi bi-magic"></i> 開始分析';
            }
        });
    }
});