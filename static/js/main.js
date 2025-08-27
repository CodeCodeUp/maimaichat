// 脉脉自动发布系统 - 前端逻辑（对话模式 + 可编辑提示词）

class MaimaiPublisher {
    constructor() {
        this.chatHistory = [];
        this.prompts = {};
        this.currentChatId = null;
        this.currentDraftId = null;
        this.initializeElements();
        this.bindEvents();
        this.bootstrap();
    }

    initializeElements() {
        // 左侧聊天和列表
        this.chatBox = document.getElementById('chat-box');
        this.chatInput = document.getElementById('chat-input');
        this.sendMsgBtn = document.getElementById('send-msg');
        this.clearChatBtn = document.getElementById('clear-chat');
        this.chatList = document.getElementById('chat-list');
        this.newChatBtn = document.getElementById('new-chat');
        this.saveChatBtn = document.getElementById('save-chat');

        // 发布区域
        this.titleInput = document.getElementById('title');
        this.topicUrlInput = document.getElementById('topic-url');
        this.generatedContentTextarea = document.getElementById('generated-content');
        this.publishBtn = document.getElementById('publish-btn');
        this.clearBtn = document.getElementById('clear-btn');

        // 草稿列表
        this.draftList = document.getElementById('draft-list');
        this.newDraftBtn = document.getElementById('new-draft');
        this.saveDraftBtn = document.getElementById('save-draft');

        // 右侧配置
        this.useMainModelCheckbox = document.getElementById('use-main-model');
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
        // 聊天相关
        this.sendMsgBtn?.addEventListener('click', () => this.sendMessage());
        this.clearChatBtn?.addEventListener('click', () => this.clearChat());
        
        if (this.chatInput) {
            this.chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        // 会话管理
        this.newChatBtn?.addEventListener('click', () => this.newChat());
        this.saveChatBtn?.addEventListener('click', () => this.saveChat());

        // 草稿管理
        this.newDraftBtn?.addEventListener('click', () => this.newDraft());
        this.saveDraftBtn?.addEventListener('click', () => this.saveDraft());

        // 发布相关
        this.publishBtn?.addEventListener('click', () => this.publishContent());
        this.clearBtn?.addEventListener('click', () => this.clearContent());
        this.getTopicInfoBtn?.addEventListener('click', () => this.getTopicInfo());
        this.generatedContentTextarea?.addEventListener('input', () => this.updatePublishButton());

        // 提示词管理
        this.savePromptsBtn?.addEventListener('click', () => this.savePrompts());
        this.addPromptBtn?.addEventListener('click', () => this.addPromptItem());
        this.applyPromptBtn?.addEventListener('click', () => this.applySelectedPrompt());

        // 其他
        this.testConnectionBtn?.addEventListener('click', () => this.testConnection());
    }

    async bootstrap() {
        // 初始化按钮状态
        this.initializeButtonStates();
        
        await this.loadConfig();
        await this.loadPrompts();
        await this.refreshChatList();
        await this.refreshDraftList();
        this.addSystemMessage('你是一个资深新媒体编辑，擅长将话题梳理成适合脉脉的内容。');
        this.updatePublishButton();
        this.updateStatus('系统初始化完成，已配置移动端API发布模式', 'success');
    }

    // 初始化按钮状态
    initializeButtonStates() {
        // 确保所有按钮的loading状态都是隐藏的
        const buttons = [
            this.sendMsgBtn,
            this.publishBtn,
            this.testConnectionBtn,
            this.getTopicInfoBtn
        ];
        
        buttons.forEach(button => {
            if (button) {
                this.setButtonLoading(button, false);
            }
        });
    }

    // ===== 配置加载 =====
    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const result = await response.json();
            if (result.success) {
                this.config = result.data;
                this.updateStatus('配置加载成功', 'success');
            } else {
                this.updateStatus(`配置加载失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`配置加载异常: ${error.message}`, 'error');
        }
    }

    // ===== 提示词管理 =====
    async loadPrompts() {
        try {
            const response = await fetch('/api/prompts');
            const result = await response.json();
            if (result.success) {
                this.prompts = result.data || {};
                this.renderPromptList();
                this.renderPromptSelect();
                this.updateStatus('提示词加载成功', 'success');
            } else {
                this.updateStatus(`提示词加载失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`提示词加载异常: ${error.message}`, 'error');
        }
    }

    renderPromptList() {
        if (!this.promptList) return;
        this.promptList.innerHTML = '';
        Object.entries(this.prompts).forEach(([key, value]) => {
            this.promptList.appendChild(this.createPromptItem(key, value));
        });
    }

    renderPromptSelect() {
        if (!this.applyPromptSelect) return;
        this.applyPromptSelect.innerHTML = '<option value="">选择模板</option>';
        Object.keys(this.prompts).forEach(key => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = key;
            this.applyPromptSelect.appendChild(option);
        });
    }

    createPromptItem(key = '', value = '') {
        const wrapper = document.createElement('div');
        wrapper.className = 'prompt-item';
        wrapper.innerHTML = `
            <input class="prompt-key" placeholder="模板名称" value="${this.escapeHtml(key)}">
            <textarea class="prompt-value" rows="4" placeholder="请输入提示词模板">${this.escapeHtml(value)}</textarea>
        `;
        return wrapper;
    }

    addPromptItem() {
        if (!this.promptList) return;
        this.promptList.appendChild(this.createPromptItem());
    }

    async savePrompts() {
        if (!this.promptList) return;
        
        const items = this.promptList.querySelectorAll('.prompt-item');
        const updated = {};
        
        items.forEach(item => {
            const key = item.querySelector('.prompt-key').value.trim();
            const value = item.querySelector('.prompt-value').value.trim();
            if (key) {
                updated[key] = value;
            }
        });

        try {
            const response = await fetch('/api/prompts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompts: updated })
            });
            const result = await response.json();
            if (result.success) {
                this.prompts = result.data;
                this.renderPromptSelect();
                this.updateStatus('提示词保存成功', 'success');
            } else {
                this.updateStatus(`提示词保存失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`提示词保存异常: ${error.message}`, 'error');
        }
    }

    applySelectedPrompt() {
        if (!this.applyPromptSelect) return;
        
        const key = this.applyPromptSelect.value;
        if (!key) {
            this.updateStatus('请选择一个提示词模板', 'error');
            return;
        }
        
        const content = this.prompts[key] || '';
        if (!content) {
            this.updateStatus('所选模板为空', 'error');
            return;
        }
        
        this.addSystemMessage(content);
        this.updateStatus(`已将模板"${key}"注入到对话中`, 'success');
    }

    // ===== 聊天功能 =====
    addSystemMessage(content) {
        this.appendChat({ role: 'system', content });
    }

    addUserMessage(content) {
        this.appendChat({ role: 'user', content });
    }

    addAssistantMessage(content) {
        this.appendChat({ role: 'assistant', content });
    }

    appendChat(message) {
        this.chatHistory.push(message);
        
        if (!this.chatBox) return;
        
        const div = document.createElement('div');
        div.className = `chat-message ${message.role}`;
        
        // 创建头像
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        // 设置头像内容
        if (message.role === 'user') {
            avatar.textContent = '我';
        } else if (message.role === 'assistant') {
            avatar.textContent = 'AI';
        } else {
            avatar.textContent = '系统';
        }
        
        // 创建消息内容
        const content = document.createElement('div');
        content.className = 'message-content';
        content.innerHTML = this.escapeHtml(message.content).replace(/\n/g, '<br>');
        
        // 组装消息
        div.appendChild(avatar);
        div.appendChild(content);
        
        this.chatBox.appendChild(div);
        this.chatBox.scrollTop = this.chatBox.scrollHeight;
    }

    async sendMessage() {
        const text = this.chatInput?.value.trim();
        if (!text) return;

        this.addUserMessage(text);
        this.chatInput.value = '';
        this.setButtonLoading(this.sendMsgBtn, true);
        this.updateStatus('正在生成回复...', 'info');

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: this.chatHistory,
                    use_main_model: this.useMainModelCheckbox?.checked || true
                }),
                signal: AbortSignal.timeout(180000) // 3分钟超时
            });
            const result = await response.json();
            
            if (result.success) {
                this.addAssistantMessage(result.content);
                // 将最新回复填入编辑区
                if (this.generatedContentTextarea) {
                    this.generatedContentTextarea.value = result.content;
                    this.updatePublishButton();
                }
                this.updateStatus(`生成成功，使用模型: ${result.model_used || 'unknown'}`, 'success');
            } else {
                this.updateStatus(`生成失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`生成异常: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(this.sendMsgBtn, false);
        }
    }

    clearChat() {
        this.chatHistory = [];
        if (this.chatBox) {
            this.chatBox.innerHTML = '';
        }
        this.updateStatus('对话已清空', 'success');
    }

    // ===== 会话管理 =====
    async refreshChatList() {
        if (!this.chatList) return;
        
        try {
            const response = await fetch('/api/chats');
            const result = await response.json();
            if (result.success) {
                this.renderChatList(result.data);
            } else {
                this.updateStatus(`加载会话列表失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`加载会话列表异常: ${error.message}`, 'error');
        }
    }

    renderChatList(chats) {
        if (!this.chatList) return;
        
        this.chatList.innerHTML = '';
        chats.forEach(chat => {
            const item = document.createElement('div');
            item.className = 'list-item';
            if (chat.id === this.currentChatId) {
                item.classList.add('active');
            }
            
            item.innerHTML = `
                <div class="title">${this.escapeHtml(chat.title || '未命名会话')}</div>
                <div class="actions">
                    <button onclick="app.loadChat('${chat.id}')" title="加载">📂</button>
                    <button onclick="app.deleteChat('${chat.id}')" title="删除">🗑️</button>
                </div>
            `;
            this.chatList.appendChild(item);
        });
    }

    async loadChat(chatId) {
        try {
            const response = await fetch(`/api/chats/${chatId}`);
            const result = await response.json();
            if (result.success) {
                this.currentChatId = chatId;
                this.chatHistory = result.data.messages || [];
                this.renderChatHistory();
                this.refreshChatList();
                this.updateStatus(`会话"${result.data.title || '未命名'}"已加载`, 'success');
            } else {
                this.updateStatus(`加载会话失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`加载会话异常: ${error.message}`, 'error');
        }
    }

    renderChatHistory() {
        if (!this.chatBox) return;
        
        this.chatBox.innerHTML = '';
        this.chatHistory.forEach(message => {
            this.appendChat(message);
        });
    }

    newChat() {
        this.currentChatId = null;
        this.clearChat();
        this.refreshChatList();
        this.updateStatus('新建会话', 'success');
    }

    async saveChat() {
        const title = prompt('请输入会话标题：', this.generateChatTitle());
        if (!title) return;

        try {
            const response = await fetch('/api/chats', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: this.currentChatId,
                    title: title,
                    messages: this.chatHistory,
                    updated_at: Date.now()
                })
            });
            const result = await response.json();
            if (result.success) {
                this.currentChatId = result.id;
                this.refreshChatList();
                this.updateStatus('会话保存成功', 'success');
            } else {
                this.updateStatus(`会话保存失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`会话保存异常: ${error.message}`, 'error');
        }
    }

    async deleteChat(chatId) {
        if (!confirm('确定要删除这个会话吗？')) return;

        try {
            const response = await fetch(`/api/chats/${chatId}`, { method: 'DELETE' });
            const result = await response.json();
            if (result.success) {
                if (this.currentChatId === chatId) {
                    this.newChat();
                }
                this.refreshChatList();
                this.updateStatus('会话删除成功', 'success');
            } else {
                this.updateStatus(`会话删除失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`会话删除异常: ${error.message}`, 'error');
        }
    }

    generateChatTitle() {
        const userMessages = this.chatHistory.filter(m => m.role === 'user');
        if (userMessages.length > 0) {
            return userMessages[0].content.substring(0, 20) + '...';
        }
        return '新会话';
    }

    // ===== 草稿管理 =====
    async refreshDraftList() {
        if (!this.draftList) return;
        
        try {
            const response = await fetch('/api/drafts');
            const result = await response.json();
            if (result.success) {
                this.renderDraftList(result.data);
            } else {
                this.updateStatus(`加载草稿列表失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`加载草稿列表异常: ${error.message}`, 'error');
        }
    }

    renderDraftList(drafts) {
        if (!this.draftList) return;
        
        this.draftList.innerHTML = '';
        drafts.forEach(draft => {
            const item = document.createElement('div');
            item.className = 'list-item';
            if (draft.id === this.currentDraftId) {
                item.classList.add('active');
            }
            
            item.innerHTML = `
                <div class="title">${this.escapeHtml(draft.title || '未命名草稿')}</div>
                <div class="actions">
                    <button onclick="app.loadDraft('${draft.id}')" title="加载">📂</button>
                    <button onclick="app.deleteDraft('${draft.id}')" title="删除">🗑️</button>
                </div>
            `;
            this.draftList.appendChild(item);
        });
    }

    async loadDraft(draftId) {
        try {
            const response = await fetch(`/api/drafts/${draftId}`);
            const result = await response.json();
            if (result.success) {
                this.currentDraftId = draftId;
                if (this.titleInput) this.titleInput.value = result.data.title || '';
                if (this.generatedContentTextarea) this.generatedContentTextarea.value = result.data.content || '';
                if (this.topicUrlInput) this.topicUrlInput.value = result.data.topic_url || '';
                this.updatePublishButton();
                this.refreshDraftList();
                this.updateStatus(`草稿"${result.data.title || '未命名'}"已加载`, 'success');
            } else {
                this.updateStatus(`加载草稿失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`加载草稿异常: ${error.message}`, 'error');
        }
    }

    newDraft() {
        this.currentDraftId = null;
        if (this.titleInput) this.titleInput.value = '';
        if (this.generatedContentTextarea) this.generatedContentTextarea.value = '';
        if (this.topicUrlInput) this.topicUrlInput.value = '';
        this.updatePublishButton();
        this.refreshDraftList();
        this.updateStatus('新建草稿', 'success');
    }

    async saveDraft() {
        const title = this.titleInput?.value.trim() || '未命名草稿';
        const content = this.generatedContentTextarea?.value.trim() || '';
        const topicUrl = this.topicUrlInput?.value.trim() || '';

        try {
            const response = await fetch('/api/drafts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: this.currentDraftId,
                    title: title,
                    content: content,
                    topic_url: topicUrl,
                    updated_at: Date.now()
                })
            });
            const result = await response.json();
            if (result.success) {
                this.currentDraftId = result.id;
                this.refreshDraftList();
                this.updateStatus('草稿保存成功', 'success');
            } else {
                this.updateStatus(`草稿保存失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`草稿保存异常: ${error.message}`, 'error');
        }
    }

    async deleteDraft(draftId) {
        if (!confirm('确定要删除这个草稿吗？')) return;

        try {
            const response = await fetch(`/api/drafts/${draftId}`, { method: 'DELETE' });
            const result = await response.json();
            if (result.success) {
                if (this.currentDraftId === draftId) {
                    this.newDraft();
                }
                this.refreshDraftList();
                this.updateStatus('草稿删除成功', 'success');
            } else {
                this.updateStatus(`草稿删除失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`草稿删除异常: ${error.message}`, 'error');
        }
    }

    // ===== 发布功能 =====
    async publishContent() {
        const title = this.titleInput?.value.trim();
        const content = this.generatedContentTextarea?.value.trim();
        const topicUrl = this.topicUrlInput?.value.trim();

        if (!title || !content) {
            this.updateStatus('请确保标题和内容都已填写', 'error');
            return;
        }

        this.setButtonLoading(this.publishBtn, true);
        this.updateStatus('正在发布到脉脉...', 'info');

        try {
            const response = await fetch('/api/publish', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content, topic_url: topicUrl }),
                signal: AbortSignal.timeout(180000) // 3分钟超时
            });
            const result = await response.json();
            
            if (result.success) {
                this.updateStatus(`发布成功！使用移动端API。${result.message}${result.url ? '\n链接: ' + result.url : ''}`, 'success');
            } else {
                this.updateStatus(`发布失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`发布异常: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(this.publishBtn, false);
        }
    }

    async testConnection() {
        this.setButtonLoading(this.testConnectionBtn, true);
        this.updateStatus('正在测试连接...', 'info');

        try {
            const response = await fetch('/api/test-connection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'all' }),
                signal: AbortSignal.timeout(180000) // 3分钟超时
            });
            const result = await response.json();
            
            if (result.success) {
                let statusText = '连接测试结果:\n';
                if (result.results.ai) {
                    statusText += `AI API: ${result.results.ai.success ? '✅ 正常' : '❌ ' + result.results.ai.error}\n`;
                }
                if (result.results.maimai) {
                    statusText += `脉脉API: ${result.results.maimai.success ? '✅ 正常' : '❌ ' + result.results.maimai.error}`;
                }
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
        const topicUrl = this.topicUrlInput?.value.trim();
        if (!topicUrl) {
            this.updateStatus('请输入话题链接', 'error');
            return;
        }

        this.setButtonLoading(this.getTopicInfoBtn, true);
        this.updateStatus('正在获取话题信息...', 'info');

        try {
            const response = await fetch('/api/topic-info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic_url: topicUrl }),
                signal: AbortSignal.timeout(180000) // 3分钟超时
            });
            const result = await response.json();
            
            if (result.success) {
                this.updateStatus(
                    `话题信息:\n` +
                    `ID: ${result.topic_id}\n` +
                    `标题: ${result.title}\n` +
                    `描述: ${result.description}\n` +
                    `参与人数: ${result.participant_count}`,
                    'success'
                );
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
        if (this.generatedContentTextarea) {
            this.generatedContentTextarea.value = '';
            this.updatePublishButton();
        }
        this.updateStatus('内容已清空', 'success');
    }

    // ===== 工具方法 =====
    updatePublishButton() {
        if (!this.publishBtn || !this.generatedContentTextarea) return;
        
        const hasContent = this.generatedContentTextarea.value.trim().length > 0;
        this.publishBtn.disabled = !hasContent;
    }

    setButtonLoading(button, loading) {
        if (!button) return;
        
        const btnText = button.querySelector('.btn-text');
        const loadingSpan = button.querySelector('.loading');
        
        if (btnText && loadingSpan) {
            if (loading) {
                btnText.style.display = 'none';
                loadingSpan.style.display = 'inline';
                button.disabled = true;
            } else {
                btnText.style.display = 'inline';
                loadingSpan.style.display = 'none';
                button.disabled = false;
            }
        } else {
            button.disabled = loading;
        }
    }

    updateStatus(message, type = 'info') {
        if (!this.statusDisplay) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const html = `<p class="${type}">[${timestamp}] ${this.escapeHtml(message).replace(/\n/g, '<br>')}</p>`;
        this.statusDisplay.innerHTML = html;
        this.statusDisplay.scrollTop = this.statusDisplay.scrollHeight;
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

// 全局实例，供HTML中的onclick事件使用
let app;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    app = new MaimaiPublisher();
});
