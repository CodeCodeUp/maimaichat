// 脉脉自动发布系统 - 前端逻辑（对话模式 + 可编辑提示词）

class MaimaiPublisher {
    constructor() {
        this.chatHistory = [];
        this.prompts = {};
        this.initializeElements();
        this.bindEvents();
        this.bootstrap();
        this.currentChatId = null;
        this.currentDraftId = null;
        this.chatList = document.getElementById('chat-list');
        this.newChatBtn = document.getElementById('new-chat');
        this.saveChatBtn = document.getElementById('save-chat');
        this.draftList = document.getElementById('draft-list');
        this.newDraftBtn = document.getElementById('new-draft');
        this.saveDraftBtn = document.getElementById('save-draft');

    }

    initializeElements() {
        // 左侧
        this.chatBox = document.getElementById('chat-box');
        this.chatInput = document.getElementById('chat-input');
        this.sendMsgBtn = document.getElementById('send-msg');
        this.clearChatBtn = document.getElementById('clear-chat');
        this.useMainModelCheckbox = document.getElementById('use-main-model');

        // 发布
        this.titleInput = document.getElementById('title');
        this.topicUrlInput = document.getElementById('topic-url');
        this.generatedContentTextarea = document.getElementById('generated-content');
        this.publishBtn = document.getElementById('publish-btn');
        this.clearBtn = document.getElementById('clear-btn');

        // 右侧
        this.promptList = document.getElementById('prompt-list');
        this.savePromptsBtn = document.getElementById('save-prompts');
        this.addPromptBtn = document.getElementById('add-prompt');
        this.applyPromptSelect = document.getElementById('apply-prompt-select');
        this.applyPromptBtn = document.getElementById('apply-prompt');

        // 其他
        this.statusDisplay = document.getElementById('status-display');
        this.testConnectionBtn = document.getElementById('test-connection');
        this.getTopicInfoBtn = document.getElementById('get-topic-info');
    }

    bindEvents() {
        this.sendMsgBtn.addEventListener('click', () => this.sendMessage());
        // 左侧列表按钮
        if (this.newChatBtn) this.newChatBtn.addEventListener('click', () => this.newChat());
        if (this.saveChatBtn) this.saveChatBtn.addEventListener('click', () => this.saveChat());
        if (this.newDraftBtn) this.newDraftBtn.addEventListener('click', () => this.newDraft());
        if (this.saveDraftBtn) this.saveDraftBtn.addEventListener('click', () => this.saveDraft());

        if (this.chatInput) {
        // 启动时加载列表
        this.refreshLists = async () => { await this.refreshChatList(); await this.refreshDraftList(); };

            this.chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        this.clearChatBtn.addEventListener('click', () => this.clearChat());
        this.publishBtn.addEventListener('click', () => this.publishContent());
        this.clearBtn.addEventListener('click', () => this.clearContent());
        this.testConnectionBtn.addEventListener('click', () => this.testConnection());
        this.getTopicInfoBtn.addEventListener('click', () => this.getTopicInfo());
        this.generatedContentTextarea.addEventListener('input', () => this.updatePublishButton());
        this.savePromptsBtn.addEventListener('click', () => this.savePrompts());
        this.addPromptBtn.addEventListener('click', () => this.addPromptItem());
        // 初始化后加载列表
        if (this.refreshLists) this.refreshLists();

        this.applyPromptBtn.addEventListener('click', () => this.applySelectedPrompt());
    }

    async bootstrap() {
        await this.loadConfig();
        await this.loadPrompts();
        this.addSystemMessage('你是一个资深新媒体编辑，擅长将话题梳理成适合脉脉的内容。');
        this.updatePublishButton();
    }

    // ===== Prompts =====
    async loadPrompts() {
        try {
            const res = await fetch('/api/prompts');
            const json = await res.json();
            if (json.success) {
                this.prompts = json.data || {};
                this.renderPromptList();
                this.renderPromptSelect();
                this.updateStatus('提示词加载成功', 'success');
            } else {
                this.updateStatus(`提示词加载失败: ${json.error}`,'error');
            }
        } catch (e) {
            this.updateStatus(`提示词加载异常: ${e.message}`,'error');
        }
    }

    renderPromptList() {
        this.promptList.innerHTML = '';
        Object.entries(this.prompts).forEach(([key, value]) => {
            this.promptList.appendChild(this.createPromptItem(key, value));
        });
    }

    renderPromptSelect() {
        this.applyPromptSelect.innerHTML = '';
        Object.keys(this.prompts).forEach(k => {
            const opt = document.createElement('option');
            opt.value = k; opt.textContent = k; this.applyPromptSelect.appendChild(opt);
        });
    }

    createPromptItem(key = '', value = '') {
        const wrapper = document.createElement('div');
        wrapper.className = 'prompt-item';
        wrapper.innerHTML = `
            <input class="prompt-key" placeholder="模板名称，如：职场话题" value="${key}">
            <textarea class="prompt-value" rows="4" placeholder="请输入提示词模板">${value}</textarea>
        `;
        return wrapper;
    }

    addPromptItem() {
        this.promptList.appendChild(this.createPromptItem());
    }

    async savePrompts() {
        // 从UI收集
        const items = this.promptList.querySelectorAll('.prompt-item');
        const updated = {};
        items.forEach(item => {
            const key = item.querySelector('.prompt-key').value.trim();
            const val = item.querySelector('.prompt-value').value.trim();
            if (key) updated[key] = val;
        });
        try {
            const res = await fetch('/api/prompts', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompts: updated })
            });
            const json = await res.json();
            if (json.success) {
                this.prompts = json.data;
                this.renderPromptSelect();
                this.updateStatus('提示词保存成功', 'success');
            } else {
                this.updateStatus(`提示词保存失败: ${json.error}`, 'error');
            }
        } catch (e) {
            this.updateStatus(`提示词保存异常: ${e.message}`, 'error');
        }
    }

    applySelectedPrompt() {
        const key = this.applyPromptSelect.value;
        const content = this.prompts[key] || '';
        if (!content) {
            this.updateStatus('所选模板为空', 'warning');
            return;
        }
        this.addSystemMessage(content);
        this.updateStatus(`已将模板“${key}”作为system注入`, 'success');
    }

    // ===== Chat =====
    addSystemMessage(content) { this.appendChat({ role: 'system', content }); }
    addUserMessage(content) { this.appendChat({ role: 'user', content }); }
    addAssistantMessage(content) { this.appendChat({ role: 'assistant', content }); }

    appendChat(message) {
        this.chatHistory.push(message);
        const div = document.createElement('div');
        div.className = `chat-msg ${message.role}`;
        div.innerHTML = `<span class="role">${message.role === 'user' ? '我' : (message.role === 'assistant' ? 'AI' : '系统')}</span><span class="content">${this.escapeHtml(message.content).replace(/\n/g, '<br>')}</span>`;
        this.chatBox.appendChild(div);
        this.chatBox.scrollTop = this.chatBox.scrollHeight;
    }

    async sendMessage() {
        const text = this.chatInput.value.trim();
        if (!text) return;
        this.addUserMessage(text);
        this.chatInput.value = '';
        this.setButtonLoading(this.sendMsgBtn, true);
        this.updateStatus('正在生成，请稍候...', 'warning');
        try {
            const res = await fetch('/api/generate', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: this.chatHistory,
                    use_main_model: this.useMainModelCheckbox.checked
                })
            });
            const json = await res.json();
            if (json.success) {
                this.addAssistantMessage(json.content);
                // 将最新回复填入编辑区以便发布
                this.generatedContentTextarea.value = json.content;
                this.updatePublishButton();
                this.updateStatus(`生成成功，模型: ${json.model_used}`, 'success');
            } else {
                this.updateStatus(`生成失败: ${json.error}`, 'error');
            }
        } catch (e) {
            this.updateStatus(`生成异常: ${e.message}`, 'error');
        } finally {
            this.setButtonLoading(this.sendMsgBtn, false);
        }
    }

    clearChat() {
        this.chatHistory = [];
        this.chatBox.innerHTML = '';
        this.updateStatus('对话已清空', 'success');
    }

    // ===== Publish / Topic =====
    async publishContent() {
        const title = this.titleInput.value.trim();
        const content = this.generatedContentTextarea.value.trim();
        const topicUrl = this.topicUrlInput.value.trim();
        if (!title || !content) { this.updateStatus('请确保标题和内容都已填写', 'error'); return; }
        this.setButtonLoading(this.publishBtn, true);
        this.updateStatus('正在发布到脉脉，请稍候...', 'warning');
        try {
            const response = await fetch('/api/publish', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content, topic_url: topicUrl })
            });
            const result = await response.json();
            if (result.success) {
                this.updateStatus(`发布成功！\n${result.message}\n${result.url ? '链接: ' + result.url : ''}`, 'success');
            } else {
                this.updateStatus(`发布失败: ${result.error}`, 'error');
                if (result.details) console.error('详细错误:', result.details);
            }
        } catch (error) {
            this.updateStatus(`发布异常: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(this.publishBtn, false);
        }
    }

    async testConnection() {
        this.setButtonLoading(this.testConnectionBtn, true);
        this.updateStatus('正在测试连接...', 'warning');
        try {
            const response = await fetch('/api/test-connection', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'all' })});
            const result = await response.json();
            if (result.success) {
                let statusText = '连接测试结果:\n';
                if (result.results.ai) statusText += `AI API: ${result.results.ai.success ? '✅ 正常' : '❌ ' + result.results.ai.error}\n`;
                if (result.results.maimai) statusText += `脉脉API: ${result.results.maimai.success ? '✅ 正常' : '❌ ' + result.results.maimai.error}\n`;
                this.updateStatus(statusText, 'success');
            } else {
                this.updateStatus(`连接测试失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`连接测试异常: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(this.testConnectionBtn, false);
        }
    }

    async getTopicInfo() {
        const topicUrl = this.topicUrlInput.value.trim();
        if (!topicUrl) { this.updateStatus('请输入话题链接', 'error'); return; }
        this.setButtonLoading(this.getTopicInfoBtn, true);
        this.updateStatus('正在获取话题信息...', 'warning');
        try {
            const response = await fetch('/api/topic-info', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ topic_url: topicUrl })});
            const result = await response.json();
            if (result.success) {
                this.updateStatus(`话题信息获取成功:\n话题ID: ${result.topic_id}\n标题: ${result.title}\n描述: ${result.description}\n参与人数: ${result.participant_count}`, 'success');
            } else {
                this.updateStatus(`获取话题信息失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`获取话题信息异常: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(this.getTopicInfoBtn, false);
        }
    }

    clearContent() {
        this.generatedContentTextarea.value = '';
        this.updatePublishButton();
        this.updateStatus('内容已清空', 'success');
    }

    // ===== Helpers =====
    updatePublishButton() {
        const hasContent = this.generatedContentTextarea.value.trim().length > 0;
        this.publishBtn.disabled = !hasContent;
    }

    setButtonLoading(button, loading) {
        const btnText = button.querySelector('.btn-text');
        const loadingSpan = button.querySelector('.loading');
        if (!btnText || !loadingSpan) return;
        if (loading) { btnText.style.display = 'none'; loadingSpan.style.display = 'inline-block'; button.disabled = true; }
        else { btnText.style.display = 'inline'; loadingSpan.style.display = 'none'; button.disabled = false; }
    }

    updateStatus(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        this.statusDisplay.innerHTML = `<p>[${timestamp}] ${this.escapeHtml(message).replace(/\n/g, '<br>')}</p>`;
        this.statusDisplay.classList.remove('status-success', 'status-error', 'status-warning');
        if (type === 'success') this.statusDisplay.classList.add('status-success');
        else if (type === 'error') this.statusDisplay.classList.add('status-error');
        else if (type === 'warning') this.statusDisplay.classList.add('status-warning');
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new MaimaiPublisher();
});
