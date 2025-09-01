// 脉脉自动发布系统 - 前端逻辑（对话模式 + 可编辑提示词）

class MaimaiPublisher {
    constructor() {
        this.chatHistory = [];
        this.prompts = {};
        this.currentPrompt = '';
        this.currentPromptKey = '';
        this.topics = [];
        this.groupedTopics = {}; // 新增：保存分组后的话题数据
        this.groups = [];  // 新增: 分组列表
        this.selectedTopicId = '';
        this.jsonRetryCount = 0;
        this.maxJsonRetry = 10;
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
        this.topicGroupFilter = document.getElementById('topic-group-filter');
        this.topicSelect = document.getElementById('topic-select');
        this.topicUrlInput = document.getElementById('topic-url');
        this.refreshTopicsBtn = document.getElementById('refresh-topics');
        this.generatedContentTextarea = document.getElementById('generated-content');
        this.publishBtn = document.getElementById('publish-btn');
        this.schedulePublishBtn = document.getElementById('schedule-publish-btn');
        this.clearBtn = document.getElementById('clear-btn');

        // 话题管理
        this.manageTopicsBtn = document.getElementById('manage-topics');
        this.topicModal = document.getElementById('topic-modal');
        this.closeTopicModalBtn = document.getElementById('close-topic-modal');
        this.closeTopicModalFooterBtn = document.getElementById('close-topic-modal-footer');
        this.newTopicIdInput = document.getElementById('new-topic-id');
        this.newTopicNameInput = document.getElementById('new-topic-name');
        this.newTopicCircleInput = document.getElementById('new-topic-circle');
        this.newTopicGroupSelect = document.getElementById('new-topic-group-select');  // 新增
        this.addTopicBtn = document.getElementById('add-topic-btn');
        this.topicSearchInput = document.getElementById('topic-search');
        this.searchTopicsBtn = document.getElementById('search-topics-btn');
        this.topicListContainer = document.getElementById('topic-list-container');
        this.batchJsonInput = document.getElementById('batch-json-input');
        this.batchImportGroupSelect = document.getElementById('batch-import-group-select');  // 新增
        this.batchImportBtn = document.getElementById('batch-import-btn');
        this.clearJsonBtn = document.getElementById('clear-json-btn');
        
        // 分组管理
        this.newGroupNameInput = document.getElementById('new-group-name');
        this.addGroupBtn = document.getElementById('add-group-btn');

        // 定时发布管理
        this.manageScheduledBtn = document.getElementById('manage-scheduled');
        this.scheduledModal = document.getElementById('scheduled-modal');
        this.closeScheduledModalBtn = document.getElementById('close-scheduled-modal');
        this.closeScheduledModalFooterBtn = document.getElementById('close-scheduled-modal-footer');
        this.refreshScheduledBtn = document.getElementById('refresh-scheduled');
        this.scheduledListContainer = document.getElementById('scheduled-list-container');
        this.scheduledPendingCount = document.getElementById('scheduled-pending-count');
        this.pendingCount = document.getElementById('pending-count');

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
        this.schedulePublishBtn?.addEventListener('click', () => this.schedulePublish());
        this.clearBtn?.addEventListener('click', () => this.clearContent());
        this.getTopicInfoBtn?.addEventListener('click', () => this.getTopicInfo());
        this.generatedContentTextarea?.addEventListener('input', () => this.updatePublishButton());
        this.refreshTopicsBtn?.addEventListener('click', () => this.loadTopics());
        this.topicGroupFilter?.addEventListener('change', () => this.onTopicGroupFilterChange());
        this.topicSelect?.addEventListener('change', () => this.onTopicSelectChange());
        this.topicUrlInput?.addEventListener('input', () => this.onTopicUrlInput());

        // 话题管理
        this.manageTopicsBtn?.addEventListener('click', () => this.openTopicModal());
        this.closeTopicModalBtn?.addEventListener('click', () => this.closeTopicModal());
        this.closeTopicModalFooterBtn?.addEventListener('click', () => this.closeTopicModal());
        this.addTopicBtn?.addEventListener('click', () => this.addTopic());
        this.searchTopicsBtn?.addEventListener('click', () => this.searchTopics());
        this.batchImportBtn?.addEventListener('click', () => this.batchImportTopics());
        this.clearJsonBtn?.addEventListener('click', () => this.clearJsonInput());
        this.topicSearchInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.searchTopics();
            }
        });
        
        // 分组管理
        this.addGroupBtn?.addEventListener('click', () => this.addGroup());
        
        // 定时发布管理
        this.manageScheduledBtn?.addEventListener('click', () => this.openScheduledModal());
        this.closeScheduledModalBtn?.addEventListener('click', () => this.closeScheduledModal());
        this.closeScheduledModalFooterBtn?.addEventListener('click', () => this.closeScheduledModal());
        this.refreshScheduledBtn?.addEventListener('click', () => this.loadScheduledPosts());
        
        // 点击定时发布弹窗外部关闭
        this.scheduledModal?.addEventListener('click', (e) => {
            if (e.target === this.scheduledModal) {
                this.closeScheduledModal();
            }
        });
        
        // 点击话题弹窗外部关闭
        this.topicModal?.addEventListener('click', (e) => {
            if (e.target === this.topicModal) {
                this.closeTopicModal();
            }
        });

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
        await this.loadGroups();
        await this.loadTopics();
        await this.loadScheduledPostsCount();
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
            this.schedulePublishBtn,
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

        // 如果是新的用户输入（非重试），重置计数器
        if (!this.isRetrying) {
            this.jsonRetryCount = 0;
        }

        this.addUserMessage(text);
        this.chatInput.value = '';
        this.setButtonLoading(this.sendMsgBtn, true);
        
        const retryInfo = this.jsonRetryCount > 0 ? ` (重试 ${this.jsonRetryCount}/${this.maxJsonRetry})` : '';
        this.updateStatus(`正在生成回复...${retryInfo}`, 'info');

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
                // 尝试解析JSON格式并自动回填，如果失败可能触发重试
                await this.processGeneratedContent(result.content);
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
        this.jsonRetryCount = 0;
        this.isRetrying = false;
        if (this.chatBox) {
            this.chatBox.innerHTML = '';
        }
        this.updateStatus('对话已清空', 'success');
    }

    // 处理AI生成的内容，检测JSON格式并自动回填
    async processGeneratedContent(content) {
        // 先默认填入原始内容
        if (this.generatedContentTextarea) {
            this.generatedContentTextarea.value = content;
            this.updatePublishButton();
        }

        // 尝试解析JSON格式
        const jsonResult = this.extractJsonFromContent(content);
        if (jsonResult) {
            const { title, content: jsonContent } = jsonResult;
            
            // 自动填入标题和内容
            if (title && this.titleInput) {
                this.titleInput.value = title;
            }
            
            if (jsonContent && this.generatedContentTextarea) {
                this.generatedContentTextarea.value = jsonContent;
                this.updatePublishButton();
            }
            
            if (title || jsonContent) {
                this.updateStatus('JSON格式检测成功，已自动回填', 'success');
                this.jsonRetryCount = 0; // 重置重试计数器
                this.isRetrying = false;
            }
        } else {
            // JSON解析失败，检查是否需要重试
            if (this.jsonRetryCount < this.maxJsonRetry) {
                this.jsonRetryCount++;
                this.isRetrying = true;
                this.updateStatus(`JSON格式解析失败，正在重试 (${this.jsonRetryCount}/${this.maxJsonRetry})`, 'warning');
                
                // 添加重试提示消息
                this.addUserMessage('请按照JSON格式回答，包含title和content字段：\n```json\n{\n  "title": "标题",\n  "content": "内容"\n}\n```');
                
                // 延迟1秒后自动重试
                setTimeout(() => {
                    this.autoRetryGeneration();
                }, 1000);
            } else {
                // 达到最大重试次数，忽略错误继续原始流程
                this.updateStatus(`JSON格式解析失败，已达到最大重试次数(${this.maxJsonRetry})，继续原始流程`, 'warning');
                this.jsonRetryCount = 0;
                this.isRetrying = false;
            }
        }
    }

    // 自动重试生成
    async autoRetryGeneration() {
        this.setButtonLoading(this.sendMsgBtn, true);
        
        const retryInfo = ` (重试 ${this.jsonRetryCount}/${this.maxJsonRetry})`;
        this.updateStatus(`正在生成回复...${retryInfo}`, 'info');

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
                // 递归调用处理生成内容
                await this.processGeneratedContent(result.content);
                this.updateStatus(`生成成功，使用模型: ${result.model_used || 'unknown'}`, 'success');
            } else {
                this.updateStatus(`生成失败: ${result.error}`, 'error');
                this.isRetrying = false;
            }
        } catch (error) {
            this.updateStatus(`生成异常: ${error.message}`, 'error');
            this.isRetrying = false;
        } finally {
            this.setButtonLoading(this.sendMsgBtn, false);
        }
    }

    // 从内容中提取JSON格式的title和content
    extractJsonFromContent(content) {
        try {
            // 查找JSON代码块 (```json ... ```)
            const jsonBlockMatch = content.match(/```json\s*\n?([\s\S]*?)\n?```/);
            if (jsonBlockMatch) {
                const jsonStr = jsonBlockMatch[1].trim();
                const parsed = JSON.parse(jsonStr);
                
                if (parsed.title || parsed.content) {
                    return {
                        title: parsed.title || '',
                        content: parsed.content || ''
                    };
                }
            }
            
            // 查找花括号包围的JSON (寻找第一个完整的JSON对象)
            const braceMatch = content.match(/\{[\s\S]*?\}/);
            if (braceMatch) {
                const jsonStr = braceMatch[0];
                const parsed = JSON.parse(jsonStr);
                
                if (parsed.title || parsed.content) {
                    return {
                        title: parsed.title || '',
                        content: parsed.content || ''
                    };
                }
            }
            
            return null;
        } catch (error) {
            // JSON解析失败，忽略错误继续原始流程
            return null;
        }
    }

    // ===== 发布功能 =====
    async publishContent() {
        const title = this.titleInput?.value.trim();
        const content = this.generatedContentTextarea?.value.trim();
        const topicUrl = this.topicUrlInput?.value.trim();
        const selectedTopicId = this.selectedTopicId;

        if (!title || !content) {
            this.updateStatus('请确保标题和内容都已填写', 'error');
            return;
        }

        // 检查话题选择：由于UI已经做了互斥处理，这里只需要简单验证
        if (selectedTopicId && topicUrl) {
            // 这种情况理论上不应该发生，但保留检查
            this.updateStatus('系统错误：话题选择状态异常', 'error');
            return;
        }

        this.setButtonLoading(this.publishBtn, true);
        this.updateStatus('正在发布到脉脉...', 'info');

        try {
            let publishData = { title, content };
            
            if (selectedTopicId) {
                // 使用选择的话题
                const selectedTopic = this.topics.find(t => t.id === selectedTopicId);
                if (selectedTopic) {
                    publishData.topic_id = selectedTopic.id;
                    publishData.circle_type = selectedTopic.circle_type;
                    this.updateStatus(`使用选择的话题: ${selectedTopic.name}`, 'info');
                }
            } else if (topicUrl) {
                // 使用链接提取
                publishData.topic_url = topicUrl;
                this.updateStatus('使用话题链接进行发布', 'info');
            } else {
                this.updateStatus('无话题发布', 'info');
            }

            const response = await fetch('/api/publish', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(publishData),
                signal: AbortSignal.timeout(180000) // 3分钟超时
            });
            const result = await response.json();
            
            if (result.success) {
                this.updateStatus(`发布成功！${result.message}${result.url ? '\n链接: ' + result.url : ''}`, 'success');
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

    // ===== 话题管理 =====
    async loadTopics() {
        try {
            const response = await fetch('/api/topics');
            const result = await response.json();
            if (result.success) {
                // 保存分组后的话题数据
                this.groupedTopics = result.data || {};
                
                // 将分组格式转换为平铺格式用于下拉选择
                this.topics = [];
                for (const [groupName, topics] of Object.entries(this.groupedTopics)) {
                    this.topics.push(...topics);
                }
                
                this.updateTopicGroupFilter();
                this.updateTopicSelect();
                this.updateStatus('话题列表加载完成', 'success');
            } else {
                this.updateStatus(`话题列表加载失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`话题列表加载异常: ${error.message}`, 'error');
        }
    }

    updateTopicGroupFilter() {
        if (!this.topicGroupFilter) return;
        
        this.topicGroupFilter.innerHTML = '<option value="">所有分组</option>';
        Object.keys(this.groupedTopics).forEach(groupName => {
            const option = document.createElement('option');
            option.value = groupName;
            option.textContent = groupName;
            this.topicGroupFilter.appendChild(option);
        });
    }

    updateTopicSelect() {
        if (!this.topicSelect) return;
        
        // 获取当前选择的分组
        const selectedGroup = this.topicGroupFilter?.value || '';
        
        this.topicSelect.innerHTML = '<option value="">选择话题（可选）</option>';
        
        if (selectedGroup) {
            // 显示特定分组的话题
            const groupTopics = this.groupedTopics[selectedGroup] || [];
            groupTopics.forEach(topic => {
                const option = document.createElement('option');
                option.value = topic.id;
                option.textContent = `${topic.name} (ID: ${topic.id}, ${topic.circle_type})`;
                this.topicSelect.appendChild(option);
            });
        } else {
            // 显示所有话题，按分组分类
            Object.entries(this.groupedTopics).forEach(([groupName, topics]) => {
                if (topics.length > 0) {
                    // 添加分组标题
                    const optgroup = document.createElement('optgroup');
                    optgroup.label = groupName;
                    
                    topics.forEach(topic => {
                        const option = document.createElement('option');
                        option.value = topic.id;
                        option.textContent = `${topic.name} (ID: ${topic.id}, ${topic.circle_type})`;
                        optgroup.appendChild(option);
                    });
                    
                    this.topicSelect.appendChild(optgroup);
                }
            });
        }
    }

    onTopicGroupFilterChange() {
        // 分组筛选改变时，清空话题选择并重新填充
        this.selectedTopicId = '';
        this.updateTopicSelect();
        
        // 重新启用话题URL输入
        if (this.topicUrlInput) {
            this.topicUrlInput.disabled = false;
            this.topicUrlInput.placeholder = '或输入话题链接';
        }
        if (this.getTopicInfoBtn) {
            this.getTopicInfoBtn.disabled = false;
        }
    }

    onTopicUrlInput() {
        const hasUrl = this.topicUrlInput?.value.trim();
        if (hasUrl && this.topicSelect) {
            // 输入了链接，清空话题选择并禁用
            this.topicSelect.value = '';
            this.selectedTopicId = '';
            this.topicSelect.disabled = true;
        } else if (this.topicSelect) {
            // 没有链接，启用话题选择
            this.topicSelect.disabled = false;
        }
    }

    onTopicSelectChange() {
        this.selectedTopicId = this.topicSelect?.value || '';
        if (this.selectedTopicId && this.topicUrlInput) {
            // 选择了话题，清空链接输入框并禁用
            this.topicUrlInput.value = '';
            this.topicUrlInput.disabled = true;
            this.topicUrlInput.placeholder = '已选择话题，链接输入已禁用';
            if (this.getTopicInfoBtn) {
                this.getTopicInfoBtn.disabled = true;
            }
            
            // 将话题名称填入标题框
            const selectedTopic = this.topics.find(t => t.id === this.selectedTopicId);
            if (selectedTopic && this.titleInput) {
                this.titleInput.value = selectedTopic.name;
                this.updateStatus(`已选择话题："${selectedTopic.name}"，名称已填入标题框`, 'success');
            }
        } else if (this.topicUrlInput) {
            // 没有选择话题，启用链接输入框
            this.topicUrlInput.disabled = false;
            this.topicUrlInput.placeholder = '或输入话题链接';
            if (this.getTopicInfoBtn) {
                this.getTopicInfoBtn.disabled = false;
            }
            
            // 清空标题框（如果之前是话题名称）
            if (this.titleInput && this.titleInput.value) {
                const wasTopicName = this.topics.some(t => t.name === this.titleInput.value);
                if (wasTopicName) {
                    this.titleInput.value = '';
                }
            }
        }
    }

    openTopicModal() {
        if (!this.topicModal) return;
        this.updateGroupSelects();
        this.loadTopicsForModal();
        this.topicModal.style.display = 'block';
    }

    closeTopicModal() {
        if (!this.topicModal) return;
        this.topicModal.style.display = 'none';
        if (this.newTopicIdInput) this.newTopicIdInput.value = '';
        if (this.newTopicNameInput) this.newTopicNameInput.value = '';
        if (this.newTopicCircleInput) this.newTopicCircleInput.value = '';
        if (this.newTopicGroupSelect) this.newTopicGroupSelect.value = '';
        if (this.topicSearchInput) this.topicSearchInput.value = '';
        if (this.batchJsonInput) this.batchJsonInput.value = '';
        if (this.newGroupNameInput) this.newGroupNameInput.value = '';
    }

    async addTopic() {
        const topicId = this.newTopicIdInput?.value.trim();
        const name = this.newTopicNameInput?.value.trim();
        const circleType = this.newTopicCircleInput?.value.trim();
        const group = this.newTopicGroupSelect?.value.trim() || null;
        
        if (!topicId || !name || !circleType) {
            this.updateStatus('请填写话题ID、名称和圈子类型', 'error');
            return;
        }

        try {
            const requestData = { id: topicId, name, circle_type: circleType };
            if (group) {
                requestData.group = group;
            }
            
            const response = await fetch('/api/topics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });
            const result = await response.json();
            
            if (result.success) {
                this.newTopicIdInput.value = '';
                this.newTopicNameInput.value = '';
                this.newTopicCircleInput.value = '';
                this.newTopicGroupSelect.value = '';
                this.loadTopicsForModal();
                this.loadTopics();
                this.updateStatus('话题添加成功', 'success');
            } else {
                this.updateStatus(`话题添加失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`话题添加异常: ${error.message}`, 'error');
        }
    }

    async loadTopicsForModal() {
        try {
            const response = await fetch('/api/topics');
            const result = await response.json();
            if (result.success) {
                this.renderTopicListByGroups(result.data || {});
            }
        } catch (error) {
            this.updateStatus(`加载话题失败: ${error.message}`, 'error');
        }
    }

    async searchTopics() {
        const keyword = this.topicSearchInput?.value.trim();
        if (!keyword) {
            this.loadTopicsForModal();
            return;
        }

        try {
            const response = await fetch(`/api/topics/search?q=${encodeURIComponent(keyword)}`);
            const result = await response.json();
            if (result.success) {
                // 搜索结果转换为分组格式显示
                const searchResults = { '搜索结果': result.data || [] };
                this.renderTopicListByGroups(searchResults);
            } else {
                this.updateStatus(`搜索话题失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`搜索话题异常: ${error.message}`, 'error');
        }
    }

    renderTopicListByGroups(groupedTopics) {
        if (!this.topicListContainer) return;
        
        this.topicListContainer.innerHTML = '';
        
        for (const [groupName, topics] of Object.entries(groupedTopics)) {
            if (topics.length === 0) continue;
            
            // 创建分组标题
            const groupHeader = document.createElement('div');
            groupHeader.className = 'topic-group-header';
            groupHeader.innerHTML = `
                <div class="group-title">
                    <h5>${this.escapeHtml(groupName)} (${topics.length})</h5>
                    <div class="group-actions">
                        ${groupName !== '搜索结果' && groupName !== '未分组' ? `
                            <button class="btn-secondary small edit-group" data-group="${this.escapeHtml(groupName)}">重命名</button>
                            <button class="btn-danger small delete-group" data-group="${this.escapeHtml(groupName)}">删除分组</button>
                        ` : ''}
                    </div>
                </div>
            `;
            
            // 绑定分组操作事件
            if (groupName !== '搜索结果' && groupName !== '未分组') {
                const editBtn = groupHeader.querySelector('.edit-group');
                const deleteBtn = groupHeader.querySelector('.delete-group');
                
                editBtn?.addEventListener('click', () => this.editGroup(groupName));
                deleteBtn?.addEventListener('click', () => this.deleteGroup(groupName));
            }
            
            this.topicListContainer.appendChild(groupHeader);
            
            // 添加该分组的话题
            topics.forEach(topic => {
                this.topicListContainer.appendChild(this.createTopicItem(topic));
            });
        }
    }

    createTopicItem(topic) {
        const item = document.createElement('div');
        item.className = 'topic-item';
        
        // 生成分组选择器选项
        const groupOptions = this.groups.map(group => 
            `<option value="${this.escapeHtml(group)}" ${topic.group === group ? 'selected' : ''}>${this.escapeHtml(group)}</option>`
        ).join('');
        
        item.innerHTML = `
            <div class="topic-item-header">
                <div class="topic-item-info">
                    <div class="topic-item-name">${this.escapeHtml(topic.name)} <small>(ID: ${this.escapeHtml(topic.id)})</small></div>
                    <div class="topic-item-circle">${this.escapeHtml(topic.circle_type)}</div>
                    <div class="topic-item-group">分组: ${this.escapeHtml(topic.group || '未分组')}</div>
                </div>
                <div class="topic-item-actions">
                    <button class="btn-secondary small edit-topic">编辑</button>
                    <button class="btn-danger small delete-topic">删除</button>
                </div>
            </div>
            <div class="topic-item-edit">
                <input type="text" class="edit-name" value="${this.escapeHtml(topic.name)}" placeholder="话题名称">
                <input type="text" class="edit-circle" value="${this.escapeHtml(topic.circle_type)}" placeholder="圈子类型" style="width: 150px;">
                <select class="edit-group" style="width: 120px;">
                    <option value="">无分组</option>
                    ${groupOptions}
                </select>
                <button class="btn-success small save-topic">保存</button>
                <button class="btn-secondary small cancel-edit">取消</button>
            </div>
        `;

        // 绑定编辑事件
        const editBtn = item.querySelector('.edit-topic');
        const deleteBtn = item.querySelector('.delete-topic');
        const saveBtn = item.querySelector('.save-topic');
        const cancelBtn = item.querySelector('.cancel-edit');

        editBtn?.addEventListener('click', () => {
            item.classList.add('editing');
        });

        cancelBtn?.addEventListener('click', () => {
            item.classList.remove('editing');
        });

        saveBtn?.addEventListener('click', () => {
            this.updateTopic(topic.id, item);
        });

        deleteBtn?.addEventListener('click', () => {
            if (confirm('确定要删除这个话题吗？')) {
                this.deleteTopic(topic.id);
            }
        });

        return item;
    }

    async updateTopic(topicId, itemElement) {
        const nameInput = itemElement.querySelector('.edit-name');
        const circleInput = itemElement.querySelector('.edit-circle');
        const groupSelect = itemElement.querySelector('.edit-group');
        
        const name = nameInput?.value.trim();
        const circleType = circleInput?.value.trim();
        const group = groupSelect?.value.trim() || null;
        
        if (!name || !circleType) {
            this.updateStatus('请填写话题名称和圈子类型', 'error');
            return;
        }

        try {
            const requestData = { name, circle_type: circleType };
            if (group !== null) {
                requestData.group = group;
            }
            
            const response = await fetch(`/api/topics/${topicId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });
            const result = await response.json();
            
            if (result.success) {
                itemElement.classList.remove('editing');
                this.loadTopicsForModal();
                this.loadTopics();
                this.updateStatus('话题更新成功', 'success');
            } else {
                this.updateStatus(`话题更新失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`话题更新异常: ${error.message}`, 'error');
        }
    }

    async deleteTopic(topicId) {
        try {
            const response = await fetch(`/api/topics/${topicId}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            
            if (result.success) {
                this.loadTopicsForModal();
                this.loadTopics();
                this.updateStatus('话题删除成功', 'success');
            } else {
                this.updateStatus(`话题删除失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`话题删除异常: ${error.message}`, 'error');
        }
    }

    clearJsonInput() {
        if (this.batchJsonInput) {
            this.batchJsonInput.value = '';
        }
    }

    async batchImportTopics() {
        const jsonText = this.batchJsonInput?.value.trim();
        if (!jsonText) {
            this.updateStatus('请输入JSON数据', 'error');
            return;
        }

        try {
            // 解析JSON
            const topicsData = JSON.parse(jsonText);
            if (!Array.isArray(topicsData)) {
                this.updateStatus('JSON数据必须是数组格式', 'error');
                return;
            }

            if (topicsData.length === 0) {
                this.updateStatus('JSON数组不能为空', 'error');
                return;
            }
            
            // 获取选择的默认分组
            const defaultGroup = this.batchImportGroupSelect?.value.trim() || null;
            if (defaultGroup) {
                // 为没有指定分组的话题添加默认分组
                topicsData.forEach(topic => {
                    if (!topic.group) {
                        topic.group = defaultGroup;
                    }
                });
            }

            this.setButtonLoading(this.batchImportBtn, true);
            this.updateStatus(`正在批量导入 ${topicsData.length} 个话题...`, 'info');

            const response = await fetch('/api/topics/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topics: topicsData })
            });
            const result = await response.json();
            
            if (result.success) {
                const { summary } = result;
                let statusText = `批量导入完成！\n总数: ${summary.total}, 成功: ${summary.success}, 失败: ${summary.failed}, 跳过: ${summary.skipped}`;
                
                // 显示详细结果
                if (result.results.failed.length > 0) {
                    statusText += `\n失败详情: ${result.results.failed.slice(0, 3).map(f => f.error).join(', ')}`;
                    if (result.results.failed.length > 3) {
                        statusText += ` 等${result.results.failed.length}个错误`;
                    }
                }
                
                if (result.results.skipped.length > 0) {
                    statusText += `\n跳过详情: ${result.results.skipped.slice(0, 3).map(s => s.reason).join(', ')}`;
                    if (result.results.skipped.length > 3) {
                        statusText += ` 等${result.results.skipped.length}个`;
                    }
                }

                this.updateStatus(statusText, summary.failed > 0 ? 'warning' : 'success');
                
                // 清空输入框并刷新列表
                this.batchJsonInput.value = '';
                this.batchImportGroupSelect.value = '';
                this.loadTopicsForModal();
                this.loadTopics();
            } else {
                this.updateStatus(`批量导入失败: ${result.error}`, 'error');
            }
        } catch (parseError) {
            if (parseError instanceof SyntaxError) {
                this.updateStatus('JSON格式错误，请检查数据格式', 'error');
            } else {
                this.updateStatus(`批量导入异常: ${parseError.message}`, 'error');
            }
        } finally {
            this.setButtonLoading(this.batchImportBtn, false);
        }
    }

    // ===== 分组管理功能 =====
    async loadGroups() {
        try {
            const response = await fetch('/api/topics/groups');
            const result = await response.json();
            if (result.success) {
                this.groups = result.data || [];
                this.updateStatus('分组列表加载完成', 'success');
            } else {
                this.updateStatus(`分组列表加载失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`分组列表加载异常: ${error.message}`, 'error');
        }
    }

    updateGroupSelects() {
        // 更新新增话题的分组选择器
        if (this.newTopicGroupSelect) {
            this.newTopicGroupSelect.innerHTML = '<option value="">选择分组 (可选)</option>';
            this.groups.forEach(group => {
                const option = document.createElement('option');
                option.value = group;
                option.textContent = group;
                this.newTopicGroupSelect.appendChild(option);
            });
        }

        // 更新批量导入的分组选择器
        if (this.batchImportGroupSelect) {
            this.batchImportGroupSelect.innerHTML = '<option value="">导入到... (默认：未分组)</option>';
            this.groups.forEach(group => {
                const option = document.createElement('option');
                option.value = group;
                option.textContent = group;
                this.batchImportGroupSelect.appendChild(option);
            });
        }
    }

    async addGroup() {
        const groupName = this.newGroupNameInput?.value.trim();
        if (!groupName) {
            this.updateStatus('请输入分组名称', 'error');
            return;
        }

        try {
            const response = await fetch('/api/topics/groups', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: groupName })
            });
            const result = await response.json();
            
            if (result.success) {
                this.newGroupNameInput.value = '';
                await this.loadGroups();
                this.updateGroupSelects();
                this.updateStatus('分组创建成功', 'success');
            } else {
                this.updateStatus(`分组创建失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`分组创建异常: ${error.message}`, 'error');
        }
    }

    async editGroup(oldName) {
        const newName = prompt('请输入新的分组名称:', oldName);
        if (!newName || newName === oldName) return;

        try {
            const response = await fetch(`/api/topics/groups/${encodeURIComponent(oldName)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ new_name: newName })
            });
            const result = await response.json();
            
            if (result.success) {
                await this.loadGroups();
                this.updateGroupSelects();
                this.loadTopicsForModal();
                this.updateStatus(`分组 "${oldName}" 已重命名为 "${newName}"`, 'success');
            } else {
                this.updateStatus(`分组重命名失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`分组重命名异常: ${error.message}`, 'error');
        }
    }

    async deleteGroup(groupName) {
        const deleteTopics = confirm(`确定要删除分组 "${groupName}" 吗？\n\n点击 "确定" 只删除分组（话题变为未分组）\n点击 "取消" 取消操作`);
        if (!deleteTopics && !confirm('确定要删除分组及其包含的所有话题吗？')) return;

        try {
            const response = await fetch(`/api/topics/groups/${encodeURIComponent(groupName)}?delete_topics=${deleteTopics}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            
            if (result.success) {
                await this.loadGroups();
                this.updateGroupSelects();
                this.loadTopicsForModal();
                this.loadTopics();
                this.updateStatus(`分组 "${groupName}" 删除成功`, 'success');
            } else {
                this.updateStatus(`分组删除失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`分组删除异常: ${error.message}`, 'error');
        }
    }

    // ===== 定时发布管理 =====
    async schedulePublish() {
        const title = this.titleInput?.value.trim();
        const content = this.generatedContentTextarea?.value.trim();
        const topicUrl = this.topicUrlInput?.value.trim();
        const selectedTopicId = this.selectedTopicId;

        if (!title || !content) {
            this.updateStatus('请确保标题和内容都已填写', 'error');
            return;
        }

        this.setButtonLoading(this.schedulePublishBtn, true);
        this.updateStatus('正在添加到定时发布队列...', 'info');

        try {
            let publishData = { title, content };
            
            if (selectedTopicId) {
                const selectedTopic = this.topics.find(t => t.id === selectedTopicId);
                if (selectedTopic) {
                    publishData.topic_id = selectedTopic.id;
                    publishData.circle_type = selectedTopic.circle_type;
                }
            } else if (topicUrl) {
                publishData.topic_url = topicUrl;
            }

            const response = await fetch('/api/scheduled-publish', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(publishData),
                signal: AbortSignal.timeout(180000)
            });
            const result = await response.json();
            
            if (result.success) {
                const scheduledTime = new Date(result.scheduled_at).toLocaleString();
                this.updateStatus(`定时发布添加成功！预计发布时间: ${scheduledTime}`, 'success');
                this.updatePendingCount(result.pending_count);
                
                this.clearContent();
                if (this.titleInput) this.titleInput.value = '';
            } else {
                this.updateStatus(`定时发布添加失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`定时发布添加异常: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(this.schedulePublishBtn, false);
        }
    }

    async loadScheduledPostsCount() {
        try {
            const response = await fetch('/api/scheduled-posts');
            const result = await response.json();
            if (result.success) {
                this.updatePendingCount(result.pending_count);
            }
        } catch (error) {
            // 静默失败
        }
    }

    async loadScheduledPosts() {
        try {
            const response = await fetch('/api/scheduled-posts');
            const result = await response.json();
            if (result.success) {
                this.renderScheduledPosts(result.data);
                this.updatePendingCount(result.pending_count);
                if (this.scheduledPendingCount) {
                    this.scheduledPendingCount.textContent = result.pending_count;
                }
            }
        } catch (error) {
            this.updateStatus(`定时发布列表加载异常: ${error.message}`, 'error');
        }
    }

    renderScheduledPosts(posts) {
        if (!this.scheduledListContainer) return;
        
        this.scheduledListContainer.innerHTML = '';
        
        if (posts.length === 0) {
            this.scheduledListContainer.innerHTML = '<p class="no-posts">暂无定时发布任务</p>';
            return;
        }
        
        posts.forEach(post => {
            this.scheduledListContainer.appendChild(this.createScheduledPostItem(post));
        });
    }

    createScheduledPostItem(post) {
        const item = document.createElement('div');
        item.className = `scheduled-post-item ${post.status}`;
        
        const scheduledTime = new Date(post.scheduled_at).toLocaleString();
        
        let statusText = post.status === 'pending' ? '等待发布' : '发布失败';
        
        // 话题信息显示
        let topicInfo = '';
        if (post.topic_name && post.topic_id) {
            topicInfo = `<div class="topic-info">话题: ${this.escapeHtml(post.topic_name)} (ID: ${this.escapeHtml(post.topic_id)})</div>`;
        } else if (post.topic_url) {
            topicInfo = `<div class="topic-info">话题链接: ${this.escapeHtml(post.topic_url)}</div>`;
        }
        
        item.innerHTML = `
            <div class="post-header">
                <div class="post-title">${this.escapeHtml(post.title)}</div>
                <div class="post-status">${statusText}</div>
            </div>
            ${topicInfo}
            <div class="post-content">${this.escapeHtml(post.content.substring(0, 100))}...</div>
            <div class="post-meta">
                <small>预计发布: ${scheduledTime}</small>
                <div class="post-actions">
                    <button class="btn-danger small delete-scheduled-post" data-id="${post.id}">删除</button>
                </div>
            </div>
        `;

        const deleteBtn = item.querySelector('.delete-scheduled-post');
        deleteBtn?.addEventListener('click', () => {
            if (confirm('确定要删除这个定时发布任务吗？')) {
                this.deleteScheduledPost(post.id);
            }
        });

        return item;
    }

    async deleteScheduledPost(postId) {
        try {
            const response = await fetch(`/api/scheduled-posts/${postId}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            
            if (result.success) {
                this.loadScheduledPosts();
                this.updatePendingCount(result.pending_count);
                this.updateStatus('定时发布任务删除成功', 'success');
            } else {
                this.updateStatus(`删除失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`删除异常: ${error.message}`, 'error');
        }
    }

    openScheduledModal() {
        if (!this.scheduledModal) return;
        this.loadScheduledPosts();
        this.scheduledModal.style.display = 'block';
    }

    closeScheduledModal() {
        if (!this.scheduledModal) return;
        this.scheduledModal.style.display = 'none';
    }

    updatePendingCount(count) {
        if (this.pendingCount) {
            this.pendingCount.textContent = count;
            this.pendingCount.style.display = count > 0 ? 'inline' : 'none';
        }
    }

    // ===== 工具方法 =====
    updatePublishButton() {
        if (!this.publishBtn || !this.generatedContentTextarea) return;
        
        const hasContent = this.generatedContentTextarea.value.trim().length > 0;
        this.publishBtn.disabled = !hasContent;
        
        // 同时更新定时发布按钮
        if (this.schedulePublishBtn) {
            this.schedulePublishBtn.disabled = !hasContent;
        }
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
