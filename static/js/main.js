// 脉脉自动发布系统 - 前端逻辑（对话模式 + 可编辑提示词）

class MaimaiPublisher {
    constructor() {
        this.chatHistory = [];
        this.prompts = {};
        this.currentPrompt = '';
        this.currentPromptKey = '';
        this.initializeElements();
        this.bindEvents();
        this.bootstrap();
    }

    initializeElements() {
        // 主聊天区域
        this.chatBox = document.getElementById('chat-box');
        this.chatInput = document.getElementById('chat-input');
        this.sendMsgBtn = document.getElementById('send-msg');
        this.clearChatBtn = document.getElementById('clear-chat');

        // 发布区域
        this.titleInput = document.getElementById('title');
        this.topicUrlInput = document.getElementById('topic-url');
        this.generatedContentTextarea = document.getElementById('generated-content');
        this.publishBtn = document.getElementById('publish-btn');
        this.clearBtn = document.getElementById('clear-btn');

        // 提示词管理
        this.promptSelect = document.getElementById('prompt-select');
        this.applyPromptBtn = document.getElementById('apply-prompt');
        this.managePromptsBtn = document.getElementById('manage-prompts');
        this.promptModal = document.getElementById('prompt-modal');
        this.closePromptModalBtn = document.getElementById('close-prompt-modal');
        this.closePromptModalFooterBtn = document.getElementById('close-prompt-modal-footer');
        this.addPromptItemBtn = document.getElementById('add-prompt-item');
        this.saveAllPromptsBtn = document.getElementById('save-all-prompts');
        this.promptListContainer = document.getElementById('prompt-list-container');
        this.currentPromptName = document.getElementById('current-prompt-name');

        // 其他
        this.statusDisplay = document.getElementById('status-display');
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

        // 发布相关
        this.publishBtn?.addEventListener('click', () => this.publishContent());
        this.clearBtn?.addEventListener('click', () => this.clearContent());
        this.getTopicInfoBtn?.addEventListener('click', () => this.getTopicInfo());
        this.generatedContentTextarea?.addEventListener('input', () => this.updatePublishButton());

        // 提示词管理
        this.applyPromptBtn?.addEventListener('click', () => this.applySelectedPrompt());
        this.managePromptsBtn?.addEventListener('click', () => this.openPromptModal());
        this.closePromptModalBtn?.addEventListener('click', () => this.closePromptModal());
        this.closePromptModalFooterBtn?.addEventListener('click', () => this.closePromptModal());
        this.addPromptItemBtn?.addEventListener('click', () => this.addPromptItem());
        this.saveAllPromptsBtn?.addEventListener('click', () => this.saveAllPrompts());
        
        // 点击弹窗外部关闭
        this.promptModal?.addEventListener('click', (e) => {
            if (e.target === this.promptModal) {
                this.closePromptModal();
            }
        });

        // 其他
        this.getTopicInfoBtn?.addEventListener('click', () => this.getTopicInfo());
    }

    async bootstrap() {
        this.initializeButtonStates();
        await this.loadPrompts();
        this.addSystemMessage(this.currentPrompt || '你是一个资深新媒体编辑，擅长将话题梳理成适合脉脉的内容。');
        this.updatePublishButton();
        this.updateStatus('系统初始化完成，已配置移动端API发布模式', 'success');
    }

    // 初始化按钮状态
    initializeButtonStates() {
        // 确保所有按钮的loading状态都是隐藏的
        const buttons = [
            this.sendMsgBtn,
            this.publishBtn,
            this.getTopicInfoBtn
        ];
        
        buttons.forEach(button => {
            if (button) {
                this.setButtonLoading(button, false);
            }
        });
    }

    // ===== 提示词管理 =====
    async loadPrompts() {
        try {
            const saved = localStorage.getItem('maimai_prompts');
            if (saved) {
                this.prompts = JSON.parse(saved);
            } else {
                // 默认提示词
                this.prompts = {
                    '默认提示词': '你是一个资深新媒体编辑，擅长将话题梳理成适合脉脉的内容。',
                    '脉脉创作者': '你是一名脉脉创作者，你在创作之前必须根据话题上网搜索实时最新的内容，避免制作内容过时。\\n创作的内容要符合脉脉的特点，不要有明显的ai生成痕迹，要符合正常创作者水平。\\n\\n这是脉脉的要求：\\n⚠目前参与活动的内容，需遵循以下内容规范（不符合要求的帖子不算入奖励）\\n①内容为经历内容时需要与话题的内容方向一致且为自身经历，分享他人故事之后不计入奖励\\n②内容为观点、知识、感受内容时，多个主贴需具有讨论方向的差异性，模板类内容不计入奖励\\n③帖子内容需非提问形式，且字数超过30字\\n④禁止AI编纂、抄袭搬运、水帖、个人人设冲突行为'
                };
            }
            
            // 加载当前使用的提示词
            const currentKey = localStorage.getItem('maimai_current_prompt_key');
            if (currentKey && this.prompts[currentKey]) {
                this.currentPrompt = this.prompts[currentKey];
                this.currentPromptKey = currentKey;
            } else {
                const firstKey = Object.keys(this.prompts)[0];
                this.currentPrompt = this.prompts[firstKey] || '';
                this.currentPromptKey = firstKey || '';
            }
            
            this.updatePromptSelect();
            this.updateCurrentPromptDisplay();
            this.updateStatus('提示词加载完成', 'success');
        } catch (error) {
            this.updateStatus(`提示词加载异常: ${error.message}`, 'error');
        }
    }

    savePrompts() {
        try {
            localStorage.setItem('maimai_prompts', JSON.stringify(this.prompts));
            this.updateStatus('提示词保存成功', 'success');
        } catch (error) {
            this.updateStatus(`提示词保存失败: ${error.message}`, 'error');
        }
    }

    updatePromptSelect() {
        if (!this.promptSelect) return;
        
        this.promptSelect.innerHTML = '<option value="">选择提示词模板</option>';
        Object.keys(this.prompts).forEach(key => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = key;
            if (key === this.currentPromptKey) {
                option.selected = true;
            }
            this.promptSelect.appendChild(option);
        });
    }

    updateCurrentPromptDisplay() {
        if (this.currentPromptName) {
            this.currentPromptName.textContent = this.currentPromptKey || '无';
        }
    }

    applySelectedPrompt() {
        const selectedKey = this.promptSelect?.value;
        if (!selectedKey) {
            this.updateStatus('请选择一个提示词模板', 'error');
            return;
        }
        
        const content = this.prompts[selectedKey];
        if (!content) {
            this.updateStatus('所选模板为空', 'error');
            return;
        }
        
        this.currentPrompt = content;
        this.currentPromptKey = selectedKey;
        localStorage.setItem('maimai_current_prompt_key', selectedKey);
        this.updateCurrentPromptDisplay();
        this.clearChat();
        this.addSystemMessage(this.currentPrompt);
        this.updateStatus(`已应用模板"${selectedKey}"`, 'success');
    }

    openPromptModal() {
        if (!this.promptModal) return;
        this.updatePromptSelect();
        this.updateCurrentPromptDisplay();
        this.renderPromptList();
        this.promptModal.style.display = 'block';
    }

    closePromptModal() {
        if (!this.promptModal) return;
        this.promptModal.style.display = 'none';
    }

    renderPromptList() {
        if (!this.promptListContainer) return;
        
        this.promptListContainer.innerHTML = '';
        Object.entries(this.prompts).forEach(([key, value]) => {
            this.promptListContainer.appendChild(this.createPromptItemCard(key, value));
        });
    }

    createPromptItemCard(key = '', value = '') {
        const card = document.createElement('div');
        card.className = 'prompt-item-card';
        
        const keyId = 'prompt_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        card.innerHTML = `
            <div class="prompt-item-header">
                <input type="text" class="prompt-key" value="${this.escapeHtml(key)}" placeholder="模板名称" data-key="${keyId}">
                <div class="prompt-item-actions">
                    <button class="btn-danger small delete-prompt" data-key="${keyId}">删除</button>
                </div>
            </div>
            <textarea class="prompt-value" rows="6" placeholder="输入提示词内容..." data-key="${keyId}">${this.escapeHtml(value)}</textarea>
        `;
        
        // 绑定删除事件
        const deleteBtn = card.querySelector('.delete-prompt');
        deleteBtn?.addEventListener('click', () => {
            if (confirm('确定要删除这个提示词模板吗？')) {
                card.remove();
            }
        });
        
        return card;
    }

    addPromptItem() {
        if (!this.promptListContainer) return;
        this.promptListContainer.appendChild(this.createPromptItemCard());
    }

    saveAllPrompts() {
        if (!this.promptListContainer) return;
        
        const cards = this.promptListContainer.querySelectorAll('.prompt-item-card');
        const newPrompts = {};
        
        cards.forEach(card => {
            const keyInput = card.querySelector('.prompt-key');
            const valueTextarea = card.querySelector('.prompt-value');
            
            if (keyInput && valueTextarea) {
                const key = keyInput.value.trim();
                const value = valueTextarea.value.trim();
                
                if (key) {
                    newPrompts[key] = value;
                }
            }
        });
        
        if (Object.keys(newPrompts).length === 0) {
            this.updateStatus('至少需要一个有效的提示词模板', 'error');
            return;
        }
        
        this.prompts = newPrompts;
        this.savePrompts();
        this.updatePromptSelect();
        this.updateCurrentPromptDisplay();
        this.closePromptModal();
        this.updateStatus('提示词模板保存成功', 'success');
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
                    use_main_model: true
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
