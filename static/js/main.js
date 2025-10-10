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
        this.currentPosts = [];  // 新增：当前解析的多篇内容
        this.isMultiplePosts = false;  // 新增：是否为多篇模式
        this.aiConfigs = {};  // 新增：AI配置列表
        this.currentAiConfigId = '';  // 新增：当前AI配置ID
        this.groupKeywords = {}; // 新增：分组关键词数据
        this.selectedKeyword = ''; // 新增：当前选择的关键词
        this.currentGroupHasKeywords = false; // 新增：当前选择的分组是否有关键词
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
        
        // 关键词选择相关元素
        this.keywordSelectionDiv = document.getElementById('keyword-selection');
        this.keywordSelect = document.getElementById('keyword-select');
        this.manageKeywordsBtn = document.getElementById('manage-keywords');
        
        // 关键词管理弹窗相关元素
        this.keywordModal = document.getElementById('keyword-modal');
        this.closeKeywordModalBtn = document.getElementById('close-keyword-modal');
        this.closeKeywordModalFooterBtn = document.getElementById('close-keyword-modal-footer');
        this.keywordGroupSelect = document.getElementById('keyword-group-select');
        this.currentGroupName = document.getElementById('current-group-name');
        this.currentGroupCount = document.getElementById('current-group-count');
        this.newKeywordInput = document.getElementById('new-keyword-input');
        this.addKeywordBtn = document.getElementById('add-keyword-btn');
        this.batchKeywordsInput = document.getElementById('batch-keywords-input');
        this.batchSetKeywordsBtn = document.getElementById('batch-set-keywords-btn');
        this.clearAllKeywordsBtn = document.getElementById('clear-all-keywords-btn');
        this.keywordsListContainer = document.getElementById('keywords-list-container');
        
        // 多篇内容相关元素
        this.multiplePostsContainer = document.getElementById('multiple-posts-container');
        this.multiplePostsList = document.getElementById('multiple-posts-list');
        this.postsCount = document.getElementById('posts-count');

        // 话题管理
        this.manageTopicsBtn = document.getElementById('manage-topics');
        this.topicModal = document.getElementById('topic-modal');
        this.closeTopicModalBtn = document.getElementById('close-topic-modal');
        this.closeTopicModalFooterBtn = document.getElementById('close-topic-modal-footer');
        this.newTopicIdInput = document.getElementById('new-topic-id');
        this.newTopicNameInput = document.getElementById('new-topic-name');
        this.newTopicCircleInput = document.getElementById('new-topic-circle');
        this.newTopicGroupSelect = document.getElementById('new-topic-group-select');  // 新增
        this.newTopicPublishTypeSelect = document.getElementById('new-topic-publish-type');  // 新增
        this.publishTypeSelect = document.getElementById('publish-type-select');  // 发布方式选择
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
    this.currentPromptName = document.getElementById('current-prompt-name');

    // 简化的提示词管理元素
    this.currentPromptIndex = document.getElementById('current-prompt-index');
    this.totalPromptsCount = document.getElementById('total-prompts-count');
    this.prevPromptBtn = document.getElementById('prev-prompt');
    this.nextPromptBtn = document.getElementById('next-prompt');
    this.deleteCurrentPromptBtn = document.getElementById('delete-current-prompt');
    this.currentPromptNameInput = document.getElementById('current-prompt-name-input');
    this.currentPromptContentInput = document.getElementById('current-prompt-content-input');
    this.saveCurrentPromptBtn = document.getElementById('save-current-prompt');
    this.promptQuickSelect = document.getElementById('prompt-quick-select');  // 新增：快速选择下拉框

    // 侧边栏快速提示词选择器
    this.sidebarPromptSelect = document.getElementById('sidebar-prompt-select');
    this.quickApplyPromptBtn = document.getElementById('quick-apply-prompt');
    this.sidebarCurrentPrompt = document.getElementById('sidebar-current-prompt');

    // 简化的提示词管理状态
    this.promptsArray = [];  // 所有提示词的数组
    this.currentPromptIdx = 0;  // 当前显示的提示词索引

        // 其他
        this.statusDisplay = document.getElementById('status-display');
        this.getTopicInfoBtn = document.getElementById('get-topic-info');
        
        // AI配置管理
        this.currentAiName = document.getElementById('current-ai-name');
        this.aiConfigSelect = document.getElementById('ai-config-select');
        this.testAiConfigBtn = document.getElementById('test-ai-config');
        this.manageAiConfigsBtn = document.getElementById('manage-ai-configs');
        this.aiConfigModal = document.getElementById('ai-config-modal');
        this.closeAiConfigModalBtn = document.getElementById('close-ai-config-modal');
        this.closeAiConfigModalFooterBtn = document.getElementById('close-ai-config-modal-footer');
        this.modalCurrentAiName = document.getElementById('modal-current-ai-name');
        this.aiConfigsContainer = document.getElementById('ai-configs-container');
        this.refreshAiConfigsBtn = document.getElementById('refresh-ai-configs');
        this.testAllConfigsBtn = document.getElementById('test-all-configs');
        
        // 自动发布管理
        this.manageAutoPublishBtn = document.getElementById('manage-auto-publish');
        this.autoPublishModal = document.getElementById('auto-publish-modal');
        this.closeAutoPublishModalBtn = document.getElementById('close-auto-publish-modal');
        this.closeAutoPublishModalFooterBtn = document.getElementById('close-auto-publish-modal-footer');
        this.autoPublishTopicSelect = document.getElementById('auto-publish-topic-select');
        this.autoPublishPromptSelect = document.getElementById('auto-publish-prompt-select');
        this.autoPublishPublishTypeSelect = document.getElementById('auto-publish-publish-type');
        this.autoPublishMaxPostsInput = document.getElementById('auto-publish-max-posts');
        this.createAutoPublishBtn = document.getElementById('create-auto-publish-btn');
        this.refreshAutoPublishBtn = document.getElementById('refresh-auto-publish');
        this.autoPublishListContainer = document.getElementById('auto-publish-list-container');
        this.autoPublishTotalCount = document.getElementById('auto-publish-total-count');
        this.autoPublishActiveCount = document.getElementById('auto-publish-active-count');
        
        // AI配置表单
        this.newAiNameInput = document.getElementById('new-ai-name');
        this.newAiDescriptionInput = document.getElementById('new-ai-description');
        this.newAiBaseUrlInput = document.getElementById('new-ai-base-url');
        this.newAiApiKeyInput = document.getElementById('new-ai-api-key');
        this.newAiMainModelInput = document.getElementById('new-ai-main-model');
        this.newAiAssistantModelInput = document.getElementById('new-ai-assistant-model');
        this.addAiConfigBtn = document.getElementById('add-ai-config-btn');
        this.clearAiFormBtn = document.getElementById('clear-ai-form-btn');
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

        // 关键词相关
        this.keywordSelect?.addEventListener('change', () => this.onKeywordSelectChange());
        this.manageKeywordsBtn?.addEventListener('click', () => this.openKeywordManageModal());
        
        // 关键词管理弹窗相关
        this.closeKeywordModalBtn?.addEventListener('click', () => this.closeKeywordManageModal());
        this.closeKeywordModalFooterBtn?.addEventListener('click', () => this.closeKeywordManageModal());
        this.keywordGroupSelect?.addEventListener('change', () => this.onKeywordGroupSelectChange());
        this.newKeywordInput?.addEventListener('input', () => this.updateKeywordButtons());
        this.newKeywordInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.addKeyword();
            }
        });
        this.addKeywordBtn?.addEventListener('click', () => this.addKeyword());
        this.batchKeywordsInput?.addEventListener('input', () => this.updateKeywordButtons());
        this.batchSetKeywordsBtn?.addEventListener('click', () => this.batchSetKeywords());
        this.clearAllKeywordsBtn?.addEventListener('click', () => this.clearAllKeywords());
        
        // 点击关键词弹窗外部关闭
        this.keywordModal?.addEventListener('click', (e) => {
            if (e.target === this.keywordModal) {
                this.closeKeywordManageModal();
            }
        });

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
        this.addPromptItemBtn?.addEventListener('click', () => this.addNewPrompt());
        this.saveAllPromptsBtn?.addEventListener('click', () => this.saveAllPrompts());
        this.saveCurrentPromptBtn?.addEventListener('click', () => this.saveCurrentPrompt());

        // 简化的提示词导航
        this.prevPromptBtn?.addEventListener('click', () => this.showPreviousPrompt());
        this.nextPromptBtn?.addEventListener('click', () => this.showNextPrompt());
        this.deleteCurrentPromptBtn?.addEventListener('click', () => this.deleteCurrentPrompt());

        // 快速选择下拉框
        this.promptQuickSelect?.addEventListener('change', (e) => this.jumpToPrompt(e.target.value));

        // 侧边栏快速提示词选择
        this.quickApplyPromptBtn?.addEventListener('click', () => this.quickApplyPrompt());
        this.sidebarPromptSelect?.addEventListener('change', (e) => {
            if (e.target.value) {
                this.quickApplyPromptBtn.disabled = false;
            } else {
                this.quickApplyPromptBtn.disabled = true;
            }
        });
        
        // AI配置管理
        this.aiConfigSelect?.addEventListener('change', (e) => this.switchAiConfig(e.target.value));
        this.testAiConfigBtn?.addEventListener('click', () => this.testCurrentAiConfig());
        this.manageAiConfigsBtn?.addEventListener('click', () => this.openAiConfigModal());
        this.closeAiConfigModalBtn?.addEventListener('click', () => this.closeAiConfigModal());
        this.closeAiConfigModalFooterBtn?.addEventListener('click', () => this.closeAiConfigModal());
        this.refreshAiConfigsBtn?.addEventListener('click', () => this.loadAiConfigs());
        this.testAllConfigsBtn?.addEventListener('click', () => this.testAllAiConfigs());
        this.addAiConfigBtn?.addEventListener('click', () => this.addAiConfig());
        this.clearAiFormBtn?.addEventListener('click', () => this.clearAiForm());
        
        // 自动发布管理
        this.manageAutoPublishBtn?.addEventListener('click', () => this.openAutoPublishModal());
        this.closeAutoPublishModalBtn?.addEventListener('click', () => this.closeAutoPublishModal());
        this.closeAutoPublishModalFooterBtn?.addEventListener('click', () => this.closeAutoPublishModal());
        this.createAutoPublishBtn?.addEventListener('click', () => this.createAutoPublishConfig());
        this.refreshAutoPublishBtn?.addEventListener('click', () => this.loadAutoPublishConfigs());
        
        // 点击弹窗外部关闭
        this.promptModal?.addEventListener('click', (e) => {
            if (e.target === this.promptModal) {
                this.closePromptModal();
            }
        });
        
        this.aiConfigModal?.addEventListener('click', (e) => {
            if (e.target === this.aiConfigModal) {
                this.closeAiConfigModal();
            }
        });
        
        this.autoPublishModal?.addEventListener('click', (e) => {
            if (e.target === this.autoPublishModal) {
                this.closeAutoPublishModal();
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
        await this.loadGroupKeywords();  // 新增：加载分组关键词
        await this.loadScheduledPostsCount();
        await this.loadAiConfigs();  // 新增：加载AI配置
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
            const response = await fetch('/api/prompts');
            const result = await response.json();
            
            if (result.success) {
                this.prompts = result.data;
                
                // 从后端获取当前选定的提示词
                let selectedKey = null;
                try {
                    const currentResponse = await fetch('/api/prompts/current');
                    const currentResult = await currentResponse.json();
                    
                    if (currentResult.success && currentResult.data.key && this.prompts[currentResult.data.key]) {
                        selectedKey = currentResult.data.key;
                    }
                } catch (error) {
                    console.warn('获取当前提示词失败，将使用默认逻辑:', error);
                }
                
                // 如果后端没有设置或获取失败，尝试从localStorage
                if (!selectedKey) {
                    const lastSelectedPrompt = localStorage.getItem('lastSelectedPrompt');
                    if (lastSelectedPrompt && this.prompts[lastSelectedPrompt]) {
                        selectedKey = lastSelectedPrompt;
                        
                        // 同步到后端
                        try {
                            await fetch('/api/prompts/current', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ key: selectedKey })
                            });
                        } catch (error) {
                            console.warn('同步提示词到后端失败:', error);
                        }
                    } else {
                        // 使用第一个提示词作为默认值
                        selectedKey = Object.keys(this.prompts)[0];
                    }
                }
                
                this.currentPrompt = this.prompts[selectedKey] || '';
                this.currentPromptKey = selectedKey || '';
                
                this.updatePromptSelect();
                this.updateCurrentPromptDisplay();
                this.updateStatus('提示词加载完成', 'success');
            } else {
                throw new Error(result.error || '提示词加载失败');
            }
        } catch (error) {
            console.error('提示词加载失败:', error);
            this.updateStatus(`提示词加载失败: ${error.message}`, 'error');
            
            // 设置基本默认值避免系统崩溃
            this.prompts = {'默认提示词': '你是一个资深新媒体编辑，擅长将话题梳理成适合脉脉的内容。'};
            this.currentPrompt = this.prompts['默认提示词'];
            this.currentPromptKey = '默认提示词';
            this.updatePromptSelect();
            this.updateCurrentPromptDisplay();
        }
    }

    async savePrompts() {
        try {
            const response = await fetch('/api/prompts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompts: this.prompts })
            });
            
            const result = await response.json();
            if (result.success) {
                this.updateStatus('提示词保存成功', 'success');
                return true;
            } else {
                throw new Error(result.error || '保存失败');
            }
        } catch (error) {
            this.updateStatus(`提示词保存失败: ${error.message}`, 'error');
            return false;
        }
    }

    updatePromptSelect() {
        // 更新弹窗内的提示词选择器
        if (this.promptSelect) {
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
        
        // 更新侧边栏的提示词选择器
        if (this.sidebarPromptSelect) {
            this.sidebarPromptSelect.innerHTML = '<option value="">选择提示词</option>';
            let hasCurrentSelected = false;
            Object.keys(this.prompts).forEach(key => {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = key;
                if (key === this.currentPromptKey) {
                    option.selected = true;
                    hasCurrentSelected = true;
                }
                this.sidebarPromptSelect.appendChild(option);
            });
            
            // 根据是否有选中项设置按钮状态
            if (this.quickApplyPromptBtn) {
                this.quickApplyPromptBtn.disabled = !hasCurrentSelected;
            }
        }
    }

    updateCurrentPromptDisplay() {
        // 更新弹窗内的当前提示词显示
        if (this.currentPromptName) {
            this.currentPromptName.textContent = this.currentPromptKey || '无';
        }
        
        // 更新侧边栏的当前提示词显示
        if (this.sidebarCurrentPrompt) {
            this.sidebarCurrentPrompt.textContent = this.currentPromptKey || '无';
        }
    }

    async applySelectedPrompt() {
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
        
        // 保存选择到localStorage
        localStorage.setItem('lastSelectedPrompt', selectedKey);
        
        // 同步到后端
        try {
            const response = await fetch('/api/prompts/current', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: selectedKey })
            });
            
            const result = await response.json();
            if (!result.success) {
                console.warn('同步当前提示词到后端失败:', result.error);
            }
        } catch (error) {
            console.warn('同步当前提示词到后端异常:', error);
        }
        
        this.updateCurrentPromptDisplay();
        this.clearChat();
        this.addSystemMessage(this.currentPrompt);
        this.updateStatus(`已应用模板"${selectedKey}"`, 'success');
    }

    async quickApplyPrompt() {
        const selectedKey = this.sidebarPromptSelect?.value;
        if (!selectedKey) {
            this.updateStatus('请选择一个提示词', 'error');
            return;
        }
        
        const content = this.prompts[selectedKey];
        if (!content) {
            this.updateStatus('所选提示词为空', 'error');
            return;
        }
        
        this.currentPrompt = content;
        this.currentPromptKey = selectedKey;
        
        // 保存选择到localStorage
        localStorage.setItem('lastSelectedPrompt', selectedKey);
        
        // 同步到后端
        try {
            const response = await fetch('/api/prompts/current', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: selectedKey })
            });
            
            const result = await response.json();
            if (!result.success) {
                console.warn('同步当前提示词到后端失败:', result.error);
            }
        } catch (error) {
            console.warn('同步当前提示词到后端异常:', error);
        }
        
        // 更新所有相关显示
        this.updateCurrentPromptDisplay();
        this.updatePromptSelect(); // 同步更新弹窗中的选择器
        this.clearChat();
        this.addSystemMessage(this.currentPrompt);
        this.updateStatus(`已应用"${selectedKey}"`, 'success');
    }

    openPromptModal() {
        if (!this.promptModal) return;

        // 重置状态
        this.currentPromptIdx = 0;

        this.updatePromptSelect();
        this.updateCurrentPromptDisplay();
        this.convertPromptsToArray();
        this.showCurrentPrompt();
        this.promptModal.style.display = 'block';
    }

    closePromptModal() {
        if (!this.promptModal) return;
        this.promptModal.style.display = 'none';
    }

    // 将prompts对象转换为数组，方便导航
    convertPromptsToArray() {
        this.promptsArray = Object.entries(this.prompts).map(([key, value]) => ({ key, value }));

        if (this.totalPromptsCount) {
            this.totalPromptsCount.textContent = this.promptsArray.length;
        }

        // 更新快速选择下拉框
        this.updatePromptQuickSelect();
    }

    // 更新快速选择下拉框
    updatePromptQuickSelect() {
        if (!this.promptQuickSelect) return;

        this.promptQuickSelect.innerHTML = '<option value="">选择提示词跳转</option>';

        this.promptsArray.forEach((prompt, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = `${index + 1}. ${prompt.key}`;
            if (index === this.currentPromptIdx) {
                option.selected = true;
            }
            this.promptQuickSelect.appendChild(option);
        });
    }

    // 跳转到指定提示词
    jumpToPrompt(indexStr) {
        if (!indexStr) return;

        const index = parseInt(indexStr);
        if (index >= 0 && index < this.promptsArray.length) {
            this.currentPromptIdx = index;
            this.showCurrentPrompt();
        }
    }

    // 显示当前提示词
    showCurrentPrompt() {
        if (this.promptsArray.length === 0) {
            this.showEmptyState();
            return;
        }

        // 确保索引在有效范围内
        this.currentPromptIdx = Math.max(0, Math.min(this.currentPromptIdx, this.promptsArray.length - 1));

        const currentPrompt = this.promptsArray[this.currentPromptIdx];

        // 更新UI
        if (this.currentPromptIndex) {
            this.currentPromptIndex.textContent = this.currentPromptIdx + 1;
        }

        if (this.currentPromptNameInput) {
            this.currentPromptNameInput.value = currentPrompt.key;
        }

        if (this.currentPromptContentInput) {
            this.currentPromptContentInput.value = currentPrompt.value;
        }

        // 更新快速选择下拉框的选中状态
        if (this.promptQuickSelect) {
            this.promptQuickSelect.value = this.currentPromptIdx;
        }

        // 更新导航按钮状态
        this.updateNavigationButtons();
    }

    // 更新导航按钮状态
    updateNavigationButtons() {
        if (this.prevPromptBtn) {
            this.prevPromptBtn.disabled = this.currentPromptIdx === 0;
        }

        if (this.nextPromptBtn) {
            this.nextPromptBtn.disabled = this.currentPromptIdx >= this.promptsArray.length - 1;
        }

        if (this.deleteCurrentPromptBtn) {
            this.deleteCurrentPromptBtn.disabled = this.promptsArray.length === 0;
        }
    }

    // 显示空状态
    showEmptyState() {
        if (this.currentPromptIndex) {
            this.currentPromptIndex.textContent = '0';
        }

        if (this.currentPromptNameInput) {
            this.currentPromptNameInput.value = '';
            this.currentPromptNameInput.placeholder = '没有提示词，点击新增创建';
        }

        if (this.currentPromptContentInput) {
            this.currentPromptContentInput.value = '';
            this.currentPromptContentInput.placeholder = '没有提示词，点击新增创建';
        }

        this.updateNavigationButtons();
    }

    // 导航方法
    showPreviousPrompt() {
        if (this.currentPromptIdx > 0) {
            this.currentPromptIdx--;
            this.showCurrentPrompt();
        }
    }

    showNextPrompt() {
        if (this.currentPromptIdx < this.promptsArray.length - 1) {
            this.currentPromptIdx++;
            this.showCurrentPrompt();
        }
    }

    // 新增提示词
    addNewPrompt() {
        const newKey = `新提示词${Date.now()}`;
        const newValue = '';

        // 添加到prompts对象
        this.prompts[newKey] = newValue;

        // 重新转换数组
        this.convertPromptsToArray();

        // 跳转到新提示词
        this.currentPromptIdx = this.promptsArray.length - 1;
        this.showCurrentPrompt();

        // 聚焦到名称输入框
        if (this.currentPromptNameInput) {
            this.currentPromptNameInput.focus();
            this.currentPromptNameInput.select();
        }
    }

    // 删除当前提示词
    deleteCurrentPrompt() {
        if (this.promptsArray.length === 0) return;

        const currentPrompt = this.promptsArray[this.currentPromptIdx];
        if (!confirm(`确定要删除提示词"${currentPrompt.key}"吗？`)) {
            return;
        }

        // 从prompts对象中删除
        delete this.prompts[currentPrompt.key];

        // 重新转换数组
        this.convertPromptsToArray();

        // 调整当前索引
        if (this.currentPromptIdx >= this.promptsArray.length) {
            this.currentPromptIdx = Math.max(0, this.promptsArray.length - 1);
        }

        // 重新显示
        this.showCurrentPrompt();

        this.updateStatus('提示词已删除', 'success');
    }

    // 保存当前提示词
    saveCurrentPrompt() {
        if (!this.currentPromptNameInput || !this.currentPromptContentInput) return;

        const newName = this.currentPromptNameInput.value.trim();
        const newContent = this.currentPromptContentInput.value.trim();

        if (!newName) {
            this.updateStatus('请输入提示词名称', 'error');
            return;
        }

        if (this.promptsArray.length > 0) {
            const currentPrompt = this.promptsArray[this.currentPromptIdx];
            const oldName = currentPrompt.key;

            // 如果名称改变了，需要删除旧的，添加新的
            if (oldName !== newName) {
                delete this.prompts[oldName];
                this.prompts[newName] = newContent;

                // 重新转换数组并找到新位置
                this.convertPromptsToArray();
                this.currentPromptIdx = this.promptsArray.findIndex(p => p.key === newName);
            } else {
                // 只是内容改变
                this.prompts[newName] = newContent;
                currentPrompt.value = newContent;
            }
        } else {
            // 新增提示词
            this.prompts[newName] = newContent;
            this.convertPromptsToArray();
            this.currentPromptIdx = this.promptsArray.findIndex(p => p.key === newName);
        }

        this.showCurrentPrompt();
        this.updateStatus('当前提示词已保存', 'success');
    }

    // 保存全部提示词到服务器
    async saveAllPrompts() {
        if (Object.keys(this.prompts).length === 0) {
            this.updateStatus('至少需要一个有效的提示词模板', 'error');
            return;
        }

        const success = await this.savePrompts();
        if (success) {
            this.updatePromptSelect();
            this.updateCurrentPromptDisplay();
            this.updateStatus('提示词模板保存成功', 'success');
        }
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
            // 检查是否需要保存对话历史（当选择的话题有自动发布配置时）
            const shouldSaveConversation = await this.shouldSaveConversationForTopic(this.selectedTopicId);
            
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: this.chatHistory,
                    use_main_model: true,
                    topic_id: this.selectedTopicId || undefined,
                    save_conversation: shouldSaveConversation
                }),
                signal: AbortSignal.timeout(180000) // 3分钟超时
            });
            const result = await response.json();
            
            if (result.success) {
                this.addAssistantMessage(result.content);
                // 尝试解析JSON格式并自动回填，如果失败可能触发重试
                await this.processGeneratedContent(result.content, result);
                
                let statusMessage = `生成成功，使用模型: ${result.model_used || 'unknown'}`;
                if (result.conversation_id) {
                    statusMessage += ` | 已保存对话历史`;
                }
                this.updateStatus(statusMessage, 'success');
            } else {
                this.updateStatus(`生成失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`生成异常: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(this.sendMsgBtn, false);
        }
    }

    async shouldSaveConversationForTopic(topicId) {
        if (!topicId) {
            return false;
        }
        
        try {
            // 检查指定话题是否有自动发布配置
            const response = await fetch('/api/auto-publish');
            const result = await response.json();
            
            if (result.success) {
                // 查找该话题的配置
                const hasConfig = result.data.some(config => config.topic_id === topicId);
                return hasConfig;
            }
            return false;
        } catch (error) {
            console.error('检查自动发布配置失败:', error);
            return false;
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
    async processGeneratedContent(content, result = null) {
        // 优先使用后端解析的结果
        if (result && result.parsed_items && result.item_count > 0) {
            const parsedItems = result.parsed_items;
            
            if (parsedItems.length > 1) {
                // 多篇模式
                this.isMultiplePosts = true;
                this.currentPosts = parsedItems;
                this.renderMultiplePosts();
                this.updatePublishButton();
                this.updateStatus(`检测到多篇内容，共 ${parsedItems.length} 篇文章`, 'success');
                return;
            } else if (parsedItems.length === 1) {
                // 单篇模式 - 使用解析的结果
                this.isMultiplePosts = false;
                this.currentPosts = [];
                
                const parsedItem = parsedItems[0];
                
                // 自动填入标题和内容
                if (parsedItem.title && this.titleInput) {
                    this.titleInput.value = parsedItem.title;
                }
                
                if (parsedItem.content && this.generatedContentTextarea) {
                    this.generatedContentTextarea.value = parsedItem.content;
                    this.updatePublishButton();
                }
                
                this.updateStatus('内容解析成功，已自动回填', 'success');
                return;
            }
        }
        
        // 如果后端未解析到结构化内容，直接使用原始内容
        this.isMultiplePosts = false;
        this.currentPosts = [];
        
        if (this.generatedContentTextarea) {
            this.generatedContentTextarea.value = content;
            this.updatePublishButton();
        }
        
        this.updateStatus('使用原始内容', 'info');
    }
    
    // 渲染多篇内容
    renderMultiplePosts() {
        if (!this.multiplePostsContainer || !this.multiplePostsList) return;
        
        // 隐藏单篇内容区域，显示多篇内容区域
        if (this.generatedContentTextarea) {
            this.generatedContentTextarea.style.display = 'none';
        }
        this.multiplePostsContainer.style.display = 'block';
        
        // 更新数量显示
        if (this.postsCount) {
            this.postsCount.textContent = this.currentPosts.length;
        }
        
        // 清空并重新渲染列表
        this.multiplePostsList.innerHTML = '';
        
        this.currentPosts.forEach((post, index) => {
            this.multiplePostsList.appendChild(this.createPostItem(post, index));
        });
    }
    
    // 创建单个文章项
    createPostItem(post, index) {
        const item = document.createElement('div');
        item.className = 'post-item';
        
        item.innerHTML = `
            <div class="post-item-header">
                <div class="post-number">#${index + 1}</div>
                <div class="post-title-editable">
                    <input type="text" class="post-title-input" value="${this.escapeHtml(post.title)}" placeholder="标题">
                </div>
                <div class="post-actions">
                    <button class="btn-danger small delete-post" data-index="${index}">删除</button>
                </div>
            </div>
            <div class="post-content-editable">
                <textarea class="post-content-input" rows="4" placeholder="内容">${this.escapeHtml(post.content)}</textarea>
            </div>
        `;
        
        // 绑定删除事件
        const deleteBtn = item.querySelector('.delete-post');
        deleteBtn?.addEventListener('click', () => {
            this.deletePost(index);
        });
        
        // 绑定编辑事件
        const titleInput = item.querySelector('.post-title-input');
        const contentInput = item.querySelector('.post-content-input');
        
        titleInput?.addEventListener('input', (e) => {
            this.currentPosts[index].title = e.target.value;
        });
        
        contentInput?.addEventListener('input', (e) => {
            this.currentPosts[index].content = e.target.value;
        });
        
        return item;
    }
    
    // 删除文章
    deletePost(index) {
        if (confirm('确定要删除这篇文章吗？')) {
            this.currentPosts.splice(index, 1);
            
            if (this.currentPosts.length === 0) {
                // 如果删完了，切换回单篇模式
                this.switchToSingleMode();
            } else {
                // 重新渲染
                this.renderMultiplePosts();
            }
            this.updatePublishButton();
        }
    }
    
    // 切换回单篇模式
    switchToSingleMode() {
        this.isMultiplePosts = false;
        this.currentPosts = [];
        
        if (this.multiplePostsContainer) {
            this.multiplePostsContainer.style.display = 'none';
        }
        if (this.generatedContentTextarea) {
            this.generatedContentTextarea.style.display = 'block';
            this.generatedContentTextarea.value = '';
        }
        if (this.titleInput) {
            this.titleInput.value = '';
        }
        
        this.updatePublishButton();
        this.updateStatus('已切换回单篇模式', 'info');
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
                await this.processGeneratedContent(result.content, result);
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

    // ===== 发布功能 =====
    async publishContent() {
        if (this.isMultiplePosts) {
            // 多篇发布模式
            await this.publishMultiplePosts();
        } else {
            // 单篇发布模式
            await this.publishSinglePost();
        }
    }
    
    // 单篇发布
    async publishSinglePost() {
        const title = this.titleInput?.value.trim() || '';  // 允许标题为空
        const content = this.generatedContentTextarea?.value.trim();
        const topicUrl = this.topicUrlInput?.value.trim();
        const selectedTopicId = this.selectedTopicId;

        if (!content) {
            this.updateStatus('请确保内容已填写', 'error');
            return;
        }

        // 检查关键词要求
        if (this.currentGroupHasKeywords && !this.selectedKeyword) {
            this.updateStatus('当前话题分组需要选择关键词才能发布', 'error');
            return;
        }

        // 添加关键词到内容前面
        let finalContent = content;
        if (this.selectedKeyword) {
            finalContent = `${this.selectedKeyword} ${content}`;
        }

        this.setButtonLoading(this.publishBtn, true);
        this.updateStatus('正在发布到脉脉...', 'info');

        try {
            let publishData = { title, content: finalContent };
            
            // 获取发布方式
            const publishType = this.publishTypeSelect?.value || 'anonymous';
            publishData.publish_type = publishType;
            
            if (selectedTopicId) {
                const selectedTopic = this.topics.find(t => t.id === selectedTopicId);
                if (selectedTopic) {
                    publishData.topic_id = selectedTopic.id;
                    publishData.circle_type = selectedTopic.circle_type;
                    this.updateStatus(`使用选择的话题: ${selectedTopic.name} (${publishType === 'anonymous' ? '匿名' : '实名'}发布)`, 'info');
                }
            } else if (topicUrl) {
                publishData.topic_url = topicUrl;
                this.updateStatus(`使用话题链接进行发布 (${publishType === 'anonymous' ? '匿名' : '实名'}发布)`, 'info');
            } else {
                this.updateStatus(`无话题发布 (${publishType === 'anonymous' ? '匿名' : '实名'}发布)`, 'info');
            }

            const response = await fetch('/api/publish', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(publishData),
                signal: AbortSignal.timeout(180000)
            });
            const result = await response.json();
            
            if (result.success) {
                this.updateStatus(`发布成功！${result.message}${result.url ? '\n链接: ' + result.url : ''}`, 'success');
                this.clearContent();
                if (this.titleInput) this.titleInput.value = '';
            } else {
                this.updateStatus(`发布失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`发布异常: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(this.publishBtn, false);
        }
    }
    
    // 多篇发布
    async publishMultiplePosts() {
        if (!this.currentPosts || this.currentPosts.length === 0) {
            this.updateStatus('没有可发布的内容', 'error');
            return;
        }

        const validPosts = this.currentPosts.filter(post => 
            post.content.trim()  // 只验证内容不为空
        );

        if (validPosts.length === 0) {
            this.updateStatus('没有有效的文章内容（内容不能为空）', 'error');
            return;
        }

        // 检查关键词要求
        if (this.currentGroupHasKeywords && !this.selectedKeyword) {
            this.updateStatus('当前话题分组需要选择关键词才能发布', 'error');
            return;
        }

        this.setButtonLoading(this.publishBtn, true);
        this.updateStatus(`开始批量发布 ${validPosts.length} 篇文章...`, 'info');

        const topicUrl = this.topicUrlInput?.value.trim();
        const selectedTopicId = this.selectedTopicId;
        
        let publishData = {};
        
        // 获取发布方式
        const publishType = this.publishTypeSelect?.value || 'anonymous';
        publishData.publish_type = publishType;
        
        if (selectedTopicId) {
            const selectedTopic = this.topics.find(t => t.id === selectedTopicId);
            if (selectedTopic) {
                publishData.topic_id = selectedTopic.id;
                publishData.circle_type = selectedTopic.circle_type;
            }
        } else if (topicUrl) {
            publishData.topic_url = topicUrl;
        }

        let successCount = 0;
        let failedCount = 0;

        // 并发发布所有文章
        const publishPromises = validPosts.map(async (post, index) => {
            try {
                // 添加关键词到内容前面
                let finalContent = post.content;
                if (this.selectedKeyword) {
                    finalContent = `${this.selectedKeyword} ${post.content}`;
                }
                
                const postData = {
                    title: post.title,
                    content: finalContent,
                    ...publishData
                };

                const response = await fetch('/api/publish', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(postData),
                    signal: AbortSignal.timeout(180000)
                });
                const result = await response.json();
                
                if (result.success) {
                    successCount++;
                    this.updateStatus(`第 ${index + 1} 篇发布成功: ${post.title}`, 'success');
                } else {
                    failedCount++;
                    this.updateStatus(`第 ${index + 1} 篇发布失败: ${post.title} - ${result.error}`, 'error');
                }
            } catch (error) {
                failedCount++;
                this.updateStatus(`第 ${index + 1} 篇发布异常: ${post.title} - ${error.message}`, 'error');
            }
        });

        try {
            await Promise.all(publishPromises);
            
            if (successCount === validPosts.length) {
                this.updateStatus(`🎉 所有文章发布成功！共 ${successCount} 篇`, 'success');
                this.clearContent();
            } else if (successCount > 0) {
                this.updateStatus(`部分发布成功：成功 ${successCount} 篇，失败 ${failedCount} 篇`, 'warning');
            } else {
                this.updateStatus(`所有文章发布失败！共 ${failedCount} 篇`, 'error');
            }
        } catch (error) {
            this.updateStatus(`批量发布过程异常: ${error.message}`, 'error');
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
        if (this.isMultiplePosts) {
            // 多篇模式：切换回单篇模式
            this.switchToSingleMode();
        } else {
            // 单篇模式：清空内容
            if (this.generatedContentTextarea) {
                this.generatedContentTextarea.value = '';
                this.updatePublishButton();
            }
        }
        this.updateStatus('内容已清空', 'success');
    }

    // ===== 分组关键词管理 =====
    async loadGroupKeywords() {
        try {
            const response = await fetch('/api/group-keywords');
            const result = await response.json();
            if (result.success) {
                this.groupKeywords = result.data || {};
                // 加载完关键词分组后更新分组选择器
                this.updateKeywordGroupSelect();
                this.updateStatus('分组关键词加载完成', 'success');
            } else {
                throw new Error(result.error || '分组关键词加载失败');
            }
        } catch (error) {
            console.error('分组关键词加载失败:', error);
            this.updateStatus(`分组关键词加载失败: ${error.message}`, 'error');
            this.groupKeywords = {};
        }
    }

    onKeywordSelectChange() {
        this.selectedKeyword = this.keywordSelect?.value || '';
        this.updatePublishButton();
    }

    updateKeywordSelection() {
        if (!this.keywordSelectionDiv || !this.keywordSelect) return;
        
        // 获取当前选择的分组
        const selectedGroup = this.getCurrentSelectedGroup();
        
        if (!selectedGroup) {
            // 没有选择分组，隐藏关键词选择
            this.keywordSelectionDiv.style.display = 'none';
            this.currentGroupHasKeywords = false;
            this.selectedKeyword = '';
            return;
        }
        
        // 检查当前分组是否有关键词
        const keywords = this.groupKeywords[selectedGroup] || [];
        this.currentGroupHasKeywords = keywords.length > 0;
        
        if (this.currentGroupHasKeywords) {
            // 显示关键词选择
            this.keywordSelectionDiv.style.display = 'flex';
            
            // 更新关键词选择框
            this.keywordSelect.innerHTML = '<option value="">请选择关键词</option>';
            keywords.forEach(keyword => {
                const option = document.createElement('option');
                option.value = keyword;
                option.textContent = keyword;
                this.keywordSelect.appendChild(option);
            });
            
            // 重置选择
            this.selectedKeyword = '';
        } else {
            // 隐藏关键词选择
            this.keywordSelectionDiv.style.display = 'none';
            this.selectedKeyword = '';
        }
        
        this.updatePublishButton();
    }

    getCurrentSelectedGroup() {
        // 如果选择了话题，从话题中获取分组
        if (this.selectedTopicId) {
            const selectedTopic = this.topics.find(t => t.id === this.selectedTopicId);
            return selectedTopic?.group_name || null;
        }
        
        // 如果没有选择话题但有分组筛选，使用筛选的分组
        const groupFilter = this.topicGroupFilter?.value;
        return groupFilter || null;
    }

    // ===== 关键词管理弹窗 =====
    
    openKeywordManageModal() {
        if (!this.keywordModal) return;
        this.updateKeywordGroupSelect();
        this.resetKeywordModal();
        this.keywordModal.style.display = 'block';
    }
    
    closeKeywordManageModal() {
        if (!this.keywordModal) return;
        this.keywordModal.style.display = 'none';
        this.resetKeywordModal();
    }
    
    resetKeywordModal() {
        // 重置选择的分组
        if (this.keywordGroupSelect) this.keywordGroupSelect.value = '';
        if (this.currentGroupName) this.currentGroupName.textContent = '未选择';
        if (this.currentGroupCount) this.currentGroupCount.textContent = '0';
        
        // 清空输入框
        if (this.newKeywordInput) this.newKeywordInput.value = '';
        if (this.batchKeywordsInput) this.batchKeywordsInput.value = '';
        
        // 重置按钮状态
        this.updateKeywordButtons();
        
        // 清空关键词列表
        if (this.keywordsListContainer) {
            this.keywordsListContainer.innerHTML = '<p class="no-group-selected">请先选择一个分组</p>';
        }
    }
    
    updateKeywordGroupSelect() {
        if (!this.keywordGroupSelect) return;
        
        this.keywordGroupSelect.innerHTML = '<option value="">选择要管理的分组</option>';
        // 使用关键词分组数据而不是话题分组数据
        Object.keys(this.groupKeywords).forEach(group => {
            const option = document.createElement('option');
            option.value = group;
            option.textContent = group;
            this.keywordGroupSelect.appendChild(option);
        });
    }
    
    async onKeywordGroupSelectChange() {
        const selectedGroup = this.keywordGroupSelect?.value;
        if (!selectedGroup) {
            this.resetKeywordModalContent();
            return;
        }
        
        // 更新分组信息显示
        if (this.currentGroupName) {
            this.currentGroupName.textContent = selectedGroup;
        }
        
        // 加载该分组的关键词
        await this.loadGroupKeywordsForModal(selectedGroup);
        this.updateKeywordButtons();
    }
    
    resetKeywordModalContent() {
        if (this.currentGroupName) this.currentGroupName.textContent = '未选择';
        if (this.currentGroupCount) this.currentGroupCount.textContent = '0';
        if (this.keywordsListContainer) {
            this.keywordsListContainer.innerHTML = '<p class="no-group-selected">请先选择一个分组</p>';
        }
        this.updateKeywordButtons();
    }
    
    async loadGroupKeywordsForModal(groupName) {
        try {
            const response = await fetch(`/api/group-keywords/${encodeURIComponent(groupName)}`);
            const result = await response.json();
            
            if (result.success) {
                const keywords = result.data.keywords || [];
                this.renderKeywordsList(keywords);
                
                if (this.currentGroupCount) {
                    this.currentGroupCount.textContent = keywords.length.toString();
                }
                
                // 将关键词填入批量输入框
                if (this.batchKeywordsInput) {
                    this.batchKeywordsInput.value = keywords.join('\\n');
                }
            } else {
                throw new Error(result.error || '加载分组关键词失败');
            }
        } catch (error) {
            console.error('加载分组关键词失败:', error);
            this.updateStatus(`加载分组关键词失败: ${error.message}`, 'error');
            this.renderKeywordsList([]);
        }
    }
    
    renderKeywordsList(keywords) {
        if (!this.keywordsListContainer) return;
        
        if (keywords.length === 0) {
            this.keywordsListContainer.innerHTML = '<p class="no-keywords">该分组暂无关键词</p>';
            return;
        }
        
        this.keywordsListContainer.innerHTML = '';
        keywords.forEach((keyword, index) => {
            const item = document.createElement('div');
            item.className = 'keyword-item';
            item.innerHTML = `
                <span class="keyword-text">${this.escapeHtml(keyword)}</span>
                <button class="btn-danger small delete-keyword" data-keyword="${this.escapeHtml(keyword)}">删除</button>
            `;
            
            // 绑定删除事件
            const deleteBtn = item.querySelector('.delete-keyword');
            deleteBtn?.addEventListener('click', () => {
                this.deleteKeyword(keyword);
            });
            
            this.keywordsListContainer.appendChild(item);
        });
    }
    
    updateKeywordButtons() {
        const hasGroup = this.keywordGroupSelect?.value;
        const hasNewKeyword = this.newKeywordInput?.value.trim();
        const hasBatchKeywords = this.batchKeywordsInput?.value.trim();
        
        // 更新添加按钮
        if (this.addKeywordBtn) {
            this.addKeywordBtn.disabled = !hasGroup || !hasNewKeyword;
        }
        
        // 更新批量操作按钮
        if (this.batchSetKeywordsBtn) {
            this.batchSetKeywordsBtn.disabled = !hasGroup || !hasBatchKeywords;
        }
        
        if (this.clearAllKeywordsBtn) {
            this.clearAllKeywordsBtn.disabled = !hasGroup;
        }
    }
    
    async addKeyword() {
        const groupName = this.keywordGroupSelect?.value;
        const keyword = this.newKeywordInput?.value.trim();
        
        if (!groupName || !keyword) {
            this.updateStatus('请选择分组并输入关键词', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/group-keywords/${encodeURIComponent(groupName)}/keywords`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword })
            });
            const result = await response.json();
            
            if (result.success) {
                this.newKeywordInput.value = '';
                await this.loadGroupKeywordsForModal(groupName);
                await this.loadGroupKeywords(); // 更新全局关键词数据
                this.updateKeywordSelection(); // 更新发布页面的关键词选择
                this.updateStatus(`关键词 "${keyword}" 添加成功`, 'success');
            } else {
                throw new Error(result.error || '添加关键词失败');
            }
        } catch (error) {
            console.error('添加关键词失败:', error);
            this.updateStatus(`添加关键词失败: ${error.message}`, 'error');
        }
    }
    
    async deleteKeyword(keyword) {
        const groupName = this.keywordGroupSelect?.value;
        if (!groupName) return;
        
        if (!confirm(`确定要删除关键词 "${keyword}" 吗？`)) return;
        
        try {
            const response = await fetch(`/api/group-keywords/${encodeURIComponent(groupName)}/keywords/${encodeURIComponent(keyword)}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            
            if (result.success) {
                await this.loadGroupKeywordsForModal(groupName);
                await this.loadGroupKeywords(); // 更新全局关键词数据
                this.updateKeywordSelection(); // 更新发布页面的关键词选择
                this.updateStatus(`关键词 "${keyword}" 删除成功`, 'success');
            } else {
                throw new Error(result.error || '删除关键词失败');
            }
        } catch (error) {
            console.error('删除关键词失败:', error);
            this.updateStatus(`删除关键词失败: ${error.message}`, 'error');
        }
    }
    
    async batchSetKeywords() {
        const groupName = this.keywordGroupSelect?.value;
        const keywordsText = this.batchKeywordsInput?.value.trim();
        
        if (!groupName || !keywordsText) {
            this.updateStatus('请选择分组并输入关键词', 'error');
            return;
        }
        
        // 解析关键词列表
        const keywords = keywordsText.split('\\n')
            .map(k => k.trim())
            .filter(k => k.length > 0);
        
        if (keywords.length === 0) {
            this.updateStatus('请输入有效的关键词', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/group-keywords/${encodeURIComponent(groupName)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keywords })
            });
            const result = await response.json();
            
            if (result.success) {
                await this.loadGroupKeywordsForModal(groupName);
                await this.loadGroupKeywords(); // 更新全局关键词数据
                this.updateKeywordSelection(); // 更新发布页面的关键词选择
                this.updateStatus(`分组 "${groupName}" 关键词批量设置成功，共 ${keywords.length} 个`, 'success');
            } else {
                throw new Error(result.error || '批量设置关键词失败');
            }
        } catch (error) {
            console.error('批量设置关键词失败:', error);
            this.updateStatus(`批量设置关键词失败: ${error.message}`, 'error');
        }
    }
    
    async clearAllKeywords() {
        const groupName = this.keywordGroupSelect?.value;
        if (!groupName) return;
        
        if (!confirm(`确定要清空分组 "${groupName}" 的所有关键词吗？`)) return;
        
        try {
            const response = await fetch(`/api/group-keywords/${encodeURIComponent(groupName)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keywords: [] })
            });
            const result = await response.json();
            
            if (result.success) {
                await this.loadGroupKeywordsForModal(groupName);
                await this.loadGroupKeywords(); // 更新全局关键词数据
                this.updateKeywordSelection(); // 更新发布页面的关键词选择
                this.updateStatus(`分组 "${groupName}" 的所有关键词已清空`, 'success');
            } else {
                throw new Error(result.error || '清空关键词失败');
            }
        } catch (error) {
            console.error('清空关键词失败:', error);
            this.updateStatus(`清空关键词失败: ${error.message}`, 'error');
        }
    }

    // ===== 话题管理 =====
    async loadTopics() {
        try {
            const response = await fetch('/api/topics');
            const result = await response.json();
            if (result.success) {
                // API现在返回数组格式，需要转换为分组格式
                this.topics = result.data || [];
                
                // 将数组格式转换为分组格式
                this.groupedTopics = {};
                this.topics.forEach(topic => {
                    const groupName = topic.group_name || '未分组';
                    if (!this.groupedTopics[groupName]) {
                        this.groupedTopics[groupName] = [];
                    }
                    this.groupedTopics[groupName].push(topic);
                });
                
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
        
        // 更新关键词选择
        this.updateKeywordSelection();
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
            
            // 将话题名称添加到聊天输入框
            if (selectedTopic && this.chatInput) {
                const currentText = this.chatInput.value.trim();
                const topicText = `${selectedTopic.name} 3篇`;
                if (currentText) {
                    this.chatInput.value = currentText + ' ' + topicText;
                } else {
                    this.chatInput.value = topicText;
                }
                this.updateStatus(`已将话题"${selectedTopic.name}"添加到消息框`, 'success');
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
        
        // 更新关键词选择
        this.updateKeywordSelection();
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
        const publishType = this.newTopicPublishTypeSelect?.value || 'anonymous';
        
        if (!topicId || !name || !circleType) {
            this.updateStatus('请填写话题ID、名称和圈子类型', 'error');
            return;
        }

        try {
            const requestData = { 
                id: topicId, 
                name, 
                circle_type: circleType,
                publish_type: publishType
            };
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
                this.newTopicPublishTypeSelect.value = 'anonymous';  // 重置为默认值
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
                // API现在返回数组格式，需要转换为分组格式
                const topics = result.data || [];
                const groupedTopics = {};
                
                topics.forEach(topic => {
                    const groupName = topic.group_name || '未分组';
                    if (!groupedTopics[groupName]) {
                        groupedTopics[groupName] = [];
                    }
                    groupedTopics[groupName].push(topic);
                });
                
                this.renderTopicListByGroups(groupedTopics);
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
        // 先检查分组下有多少话题
        const groupTopics = this.topics.filter(topic => topic.group === groupName);
        const topicCount = groupTopics.length;
        
        let confirmMessage = `确定要删除分组 "${groupName}" 吗？`;
        if (topicCount > 0) {
            confirmMessage += `\n\n该分组包含 ${topicCount} 个话题。\n\n选择操作：\n- 点击"确定"：删除分组，话题变为未分组状态\n- 点击"取消"：不删除`;
        }
        
        if (!confirm(confirmMessage)) return;
        
        // 如果分组包含话题，询问是否要同时删除话题
        let deleteTopics = false;
        if (topicCount > 0) {
            deleteTopics = confirm(`是否要同时删除分组内的所有 ${topicCount} 个话题？\n\n- 点击"确定"：删除分组和话题\n- 点击"取消"：只删除分组，话题变为未分组`);
        }

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
                
                if (deleteTopics && topicCount > 0) {
                    this.updateStatus(`分组 "${groupName}" 及其包含的 ${topicCount} 个话题删除成功`, 'success');
                } else {
                    this.updateStatus(`分组 "${groupName}" 删除成功${topicCount > 0 ? `，${topicCount} 个话题已变为未分组状态` : ''}`, 'success');
                }
            } else {
                this.updateStatus(`分组删除失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`分组删除异常: ${error.message}`, 'error');
        }
    }

    // ===== 定时发布管理 =====
    async schedulePublish() {
        if (this.isMultiplePosts) {
            // 多篇定时发布模式
            await this.scheduleMultiplePosts();
        } else {
            // 单篇定时发布模式
            await this.scheduleSinglePost();
        }
    }
    
    // 单篇定时发布
    async scheduleSinglePost() {
        const title = this.titleInput?.value.trim() || '';  // 允许标题为空
        const content = this.generatedContentTextarea?.value.trim();
        const topicUrl = this.topicUrlInput?.value.trim();
        const selectedTopicId = this.selectedTopicId;

        if (!content) {
            this.updateStatus('请确保内容已填写', 'error');
            return;
        }

        // 检查关键词要求
        if (this.currentGroupHasKeywords && !this.selectedKeyword) {
            this.updateStatus('当前话题分组需要选择关键词才能定时发布', 'error');
            return;
        }

        // 添加关键词到内容前面
        let finalContent = content;
        if (this.selectedKeyword) {
            finalContent = `${this.selectedKeyword} ${content}`;
        }

        this.setButtonLoading(this.schedulePublishBtn, true);
        this.updateStatus('正在添加到定时发布队列...', 'info');

        try {
            let publishData = { title, content: finalContent };
            
            // 获取发布方式
            const publishType = this.publishTypeSelect?.value || 'anonymous';
            publishData.publish_type = publishType;
            
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
    
    // 多篇定时发布
    async scheduleMultiplePosts() {
        if (!this.currentPosts || this.currentPosts.length === 0) {
            this.updateStatus('没有可定时发布的内容', 'error');
            return;
        }

        const validPosts = this.currentPosts.filter(post => 
            post.content.trim()  // 只验证内容不为空
        );

        if (validPosts.length === 0) {
            this.updateStatus('没有有效的文章内容（内容不能为空）', 'error');
            return;
        }

        // 检查关键词要求
        if (this.currentGroupHasKeywords && !this.selectedKeyword) {
            this.updateStatus('当前话题分组需要选择关键词才能定时发布', 'error');
            return;
        }

        this.setButtonLoading(this.schedulePublishBtn, true);
        this.updateStatus(`开始添加 ${validPosts.length} 篇文章到定时发布队列...`, 'info');

        const topicUrl = this.topicUrlInput?.value.trim();
        const selectedTopicId = this.selectedTopicId;
        
        let publishData = {};
        
        // 获取发布方式
        const publishType = this.publishTypeSelect?.value || 'anonymous';
        publishData.publish_type = publishType;
        
        if (selectedTopicId) {
            const selectedTopic = this.topics.find(t => t.id === selectedTopicId);
            if (selectedTopic) {
                publishData.topic_id = selectedTopic.id;
                publishData.circle_type = selectedTopic.circle_type;
            }
        } else if (topicUrl) {
            publishData.topic_url = topicUrl;
        }

        let successCount = 0;
        let failedCount = 0;
        const scheduledTimes = [];

        // 按顺序添加到定时发布队列（这样能保证正确的时间间隔）
        for (let i = 0; i < validPosts.length; i++) {
            const post = validPosts[i];
            try {
                // 添加关键词到内容前面
                let finalContent = post.content;
                if (this.selectedKeyword) {
                    finalContent = `${this.selectedKeyword} ${post.content}`;
                }
                
                const postData = {
                    title: post.title,
                    content: finalContent,
                    ...publishData
                };

                const response = await fetch('/api/scheduled-publish', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(postData),
                    signal: AbortSignal.timeout(180000)
                });
                const result = await response.json();
                
                if (result.success) {
                    successCount++;
                    const scheduledTime = new Date(result.scheduled_at).toLocaleString();
                    scheduledTimes.push(scheduledTime);
                    this.updateStatus(`第 ${i + 1} 篇已添加: ${post.title} (${scheduledTime})`, 'success');
                } else {
                    failedCount++;
                    this.updateStatus(`第 ${i + 1} 篇添加失败: ${post.title} - ${result.error}`, 'error');
                }
            } catch (error) {
                failedCount++;
                this.updateStatus(`第 ${i + 1} 篇添加异常: ${post.title} - ${error.message}`, 'error');
            }
        }

        try {
            if (successCount === validPosts.length) {
                this.updateStatus(`🎉 所有文章已添加到定时发布队列！共 ${successCount} 篇`, 'success');
                this.clearContent();
            } else if (successCount > 0) {
                this.updateStatus(`部分添加成功：成功 ${successCount} 篇，失败 ${failedCount} 篇`, 'warning');
            } else {
                this.updateStatus(`所有文章添加失败！共 ${failedCount} 篇`, 'error');
            }
            
            // 更新待发布计数
            await this.loadScheduledPostsCount();
        } catch (error) {
            this.updateStatus(`批量定时发布过程异常: ${error.message}`, 'error');
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
        
        // 按发布时间排序，显示发布队列顺序
        const sortedPosts = posts.filter(post => post.status === 'pending')
            .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at));
        
        const failedPosts = posts.filter(post => post.status === 'failed');
        
        // 先显示待发布任务（按队列顺序）
        sortedPosts.forEach((post, index) => {
            this.scheduledListContainer.appendChild(this.createScheduledPostItem(post, index + 1));
        });
        
        // 然后显示失败任务
        failedPosts.forEach(post => {
            this.scheduledListContainer.appendChild(this.createScheduledPostItem(post));
        });
    }

    createScheduledPostItem(post, queueNumber = null) {
        const item = document.createElement('div');
        item.className = `scheduled-post-item ${post.status}`;
        
        const scheduledTime = new Date(post.scheduled_at).toLocaleString();
        
        let statusText = '';
        let statusClass = '';
        if (post.status === 'pending') {
            const now = new Date();
            const scheduled = new Date(post.scheduled_at);
            if (now >= scheduled) {
                statusText = '准备发布';
                statusClass = 'status-ready';
            } else {
                statusText = queueNumber ? `队列第${queueNumber}位` : '等待中';
                statusClass = 'status-pending';
            }
        } else if (post.status === 'failed') {
            statusText = '发布失败';
            statusClass = 'status-failed';
        }
        
        // 话题信息显示
        let topicInfo = '';
        if (post.topic_name && post.topic_id) {
            topicInfo = `<div class="topic-info">话题: ${this.escapeHtml(post.topic_name)} (ID: ${this.escapeHtml(post.topic_id)})</div>`;
        } else if (post.topic_url) {
            topicInfo = `<div class="topic-info">话题链接: ${this.escapeHtml(post.topic_url)}</div>`;
        }
        
        // 队列序号显示
        let queueBadge = '';
        if (queueNumber) {
            queueBadge = `<div class="queue-number">#${queueNumber}</div>`;
        }
        
        item.innerHTML = `
            <div class="post-header">
                <div class="post-title-container">
                    ${queueBadge}
                    <div class="post-title">${this.escapeHtml(post.title)}</div>
                </div>
                <div class="post-status ${statusClass}">${statusText}</div>
            </div>
            ${topicInfo}
            <div class="post-content">${this.escapeHtml(post.content.substring(0, 100))}...</div>
            <div class="post-meta">
                <small>预计发布: ${scheduledTime}</small>
                <div class="post-actions">
                    <button class="btn-primary small edit-scheduled-post" data-id="${post.id}">编辑</button>
                    <button class="btn-danger small delete-scheduled-post" data-id="${post.id}">删除</button>
                </div>
            </div>
            ${post.error ? `<div class="post-error">错误: ${this.escapeHtml(post.error)}</div>` : ''}
        `;

        const editBtn = item.querySelector('.edit-scheduled-post');
        editBtn?.addEventListener('click', () => {
            this.editScheduledPost(post);
        });

        const deleteBtn = item.querySelector('.delete-scheduled-post');
        deleteBtn?.addEventListener('click', () => {
            if (confirm('确定要删除这个定时发布任务吗？')) {
                this.deleteScheduledPost(post.id);
            }
        });

        return item;
    }

    editScheduledPost(post) {
        // 创建编辑弹窗
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'block';
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>编辑定时发布</h3>
                    <button class="modal-close" id="close-edit-modal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <label>标题:</label>
                        <input type="text" id="edit-title" value="${this.escapeHtml(post.title)}" placeholder="文章标题">
                    </div>
                    <div class="row">
                        <label>内容:</label>
                        <textarea id="edit-content" rows="10" placeholder="文章内容">${this.escapeHtml(post.content)}</textarea>
                    </div>
                    <div class="post-info">
                        <small>预计发布时间: ${new Date(post.scheduled_at).toLocaleString()}</small>
                    </div>
                </div>
                <div class="modal-footer">
                    <button id="save-edit" class="btn-success">保存修改</button>
                    <button id="cancel-edit" class="btn-secondary">取消</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 绑定事件
        const closeBtn = modal.querySelector('#close-edit-modal');
        const cancelBtn = modal.querySelector('#cancel-edit');
        const saveBtn = modal.querySelector('#save-edit');
        const titleInput = modal.querySelector('#edit-title');
        const contentTextarea = modal.querySelector('#edit-content');
        
        const closeModal = () => {
            document.body.removeChild(modal);
        };
        
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        
        // 点击模态框外部关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
        
        saveBtn.addEventListener('click', async () => {
            const title = titleInput.value.trim();
            const content = contentTextarea.value.trim();
            
            if (!content) {
                alert('内容不能为空');
                return;
            }
            
            try {
                this.setButtonLoading(saveBtn, true);
                
                const response = await fetch(`/api/scheduled-posts/${post.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, content })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.updateStatus('定时发布任务修改成功', 'success');
                    this.loadScheduledPosts(); // 刷新列表
                    closeModal();
                } else {
                    this.updateStatus(`修改失败: ${result.error}`, 'error');
                }
            } catch (error) {
                this.updateStatus(`修改异常: ${error.message}`, 'error');
            } finally {
                this.setButtonLoading(saveBtn, false);
            }
        });
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
        if (!this.publishBtn) return;
        
        let hasContent = false;
        
        if (this.isMultiplePosts) {
            // 多篇模式：检查是否有有效的文章
            hasContent = this.currentPosts.length > 0 && 
                        this.currentPosts.some(post => post.content.trim());  // 只检查内容
        } else {
            // 单篇模式：检查文本框内容
            hasContent = this.generatedContentTextarea && 
                        this.generatedContentTextarea.value.trim().length > 0;
        }
        
        // 检查关键词要求
        const canPublish = hasContent && (!this.currentGroupHasKeywords || this.selectedKeyword);
        
        this.publishBtn.disabled = !canPublish;
        
        // 同时更新定时发布按钮
        if (this.schedulePublishBtn) {
            this.schedulePublishBtn.disabled = !canPublish;
        }
        
        // 更新按钮文字
        if (this.isMultiplePosts && this.currentPosts.length > 0) {
            const btnText = this.publishBtn.querySelector('.btn-text');
            const schedBtnText = this.schedulePublishBtn?.querySelector('.btn-text');
            
            if (btnText) btnText.textContent = `发布 (${this.currentPosts.length}篇)`;
            if (schedBtnText) schedBtnText.textContent = `定时发布 (${this.currentPosts.length}篇)`;
        } else {
            const btnText = this.publishBtn.querySelector('.btn-text');
            const schedBtnText = this.schedulePublishBtn?.querySelector('.btn-text');
            
            if (btnText) btnText.textContent = '发布';
            if (schedBtnText) schedBtnText.textContent = '定时发布';
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

    // ===== AI配置管理 =====

    async loadAiConfigs() {
        try {
            const response = await fetch('/api/ai-configs');
            const result = await response.json();
            
            if (result.success) {
                this.aiConfigs = result.data;
                this.currentAiConfigId = result.current_config_id;
                this.updateAiConfigUI();
                this.updateStatus('AI配置加载成功', 'success');
            } else {
                throw new Error(result.error || '获取AI配置失败');
            }
        } catch (error) {
            console.error('加载AI配置失败:', error);
            this.updateStatus('加载AI配置失败: ' + error.message, 'error');
        }
    }

    updateAiConfigUI() {
        // 更新右侧栏的当前AI配置显示
        if (this.currentAiName) {
            const currentConfig = this.aiConfigs.find(config => config.id === this.currentAiConfigId);
            this.currentAiName.textContent = currentConfig ? currentConfig.name : '未知';
        }

        // 更新右侧栏的AI配置选择下拉框
        if (this.aiConfigSelect) {
            this.aiConfigSelect.innerHTML = '';
            this.aiConfigs.forEach(config => {
                const option = document.createElement('option');
                option.value = config.id;
                option.textContent = config.name;
                option.selected = config.id === this.currentAiConfigId;
                this.aiConfigSelect.appendChild(option);
            });
        }

        // 更新弹窗中的当前配置显示
        if (this.modalCurrentAiName) {
            const currentConfig = this.aiConfigs.find(config => config.id === this.currentAiConfigId);
            this.modalCurrentAiName.textContent = currentConfig ? currentConfig.name : '未知';
        }

        // 更新弹窗中的配置列表
        this.renderAiConfigsList();
    }

    renderAiConfigsList() {
        if (!this.aiConfigsContainer) return;

        this.aiConfigsContainer.innerHTML = '';
        
        this.aiConfigs.forEach(config => {
            const configId = config.id;
            const configItem = document.createElement('div');
            configItem.className = `ai-config-item ${configId === this.currentAiConfigId ? 'current' : ''}`;
            configItem.setAttribute('data-config-id', configId);  // 添加数据属性
            
            configItem.innerHTML = `
                <div class="ai-config-info">
                    <div class="ai-config-name">${this.escapeHtml(config.name)}</div>
                    <div class="ai-config-description">${this.escapeHtml(config.description)}</div>
                    <div class="ai-config-details">
                        ${this.escapeHtml(config.base_url)} | ${this.escapeHtml(config.main_model)}
                    </div>
                    <div class="ai-config-status-badge ${config.enabled ? 'status-enabled' : 'status-disabled'}">
                        ${config.enabled ? '启用' : '禁用'}
                    </div>
                    ${configId === this.currentAiConfigId ? '<div class="ai-config-status-badge status-current">当前</div>' : ''}
                </div>
                <div class="ai-config-item-actions">
                    <button class="btn-primary small" onclick="app.testAiConfigConnection('${configId}')">测试</button>
                    ${configId !== this.currentAiConfigId && config.enabled ? 
                        `<button class="btn-success small" onclick="app.switchAiConfig('${configId}')">切换</button>` : 
                        ''}
                    <button class="btn-warning small" onclick="app.editAiConfig('${configId}')">编辑</button>
                    <button class="btn-danger small" onclick="app.deleteAiConfig('${configId}')">删除</button>
                </div>
            `;
            
            this.aiConfigsContainer.appendChild(configItem);
        });
    }

    async switchAiConfig(configId) {
        if (!configId || configId === this.currentAiConfigId) return;

        try {
            const response = await fetch('/api/ai-configs/current', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config_id: configId })
            });

            const result = await response.json();
            
            if (result.success) {
                this.currentAiConfigId = configId;
                this.updateAiConfigUI();
                this.updateStatus(result.message, 'success');
            } else {
                throw new Error(result.error || '切换AI配置失败');
            }
        } catch (error) {
            console.error('切换AI配置失败:', error);
            this.updateStatus('切换AI配置失败: ' + error.message, 'error');
        }
    }

    async testCurrentAiConfig() {
        await this.testAiConfigConnection(this.currentAiConfigId);
    }

    async testAiConfigConnection(configId) {
        try {
            this.updateStatus('正在测试AI配置连接...', 'info');
            
            // 更新界面显示测试状态
            const configElement = this.findConfigElement(configId);
            if (configElement) {
                const testBtn = configElement.querySelector('button[onclick*="testAiConfigConnection"]');
                if (testBtn) {
                    testBtn.disabled = true;
                    testBtn.textContent = '测试中...';
                }
            }
            
            const response = await fetch(`/api/ai-configs/${configId}/test`, {
                method: 'POST'
            });

            const result = await response.json();
            
            if (result.success) {
                const config = this.aiConfigs.find(c => c.id === configId);
                this.updateStatus(`AI配置 "${config ? config.name : 'Unknown'}" 连接测试成功`, 'success');
                this.updateConfigTestResult(configId, 'success', '连接正常');
            } else {
                throw new Error(result.error || '连接测试失败');
            }
        } catch (error) {
            console.error('测试AI配置连接失败:', error);
            this.updateStatus(`AI配置连接测试失败: ${error.message}`, 'error');
            this.updateConfigTestResult(configId, 'error', error.message);
        } finally {
            // 恢复按钮状态
            const configElement = this.findConfigElement(configId);
            if (configElement) {
                const testBtn = configElement.querySelector('button[onclick*="testAiConfigConnection"]');
                if (testBtn) {
                    testBtn.disabled = false;
                    testBtn.textContent = '测试';
                }
            }
        }
    }

    findConfigElement(configId) {
        if (!this.aiConfigsContainer) return null;
        return this.aiConfigsContainer.querySelector(`[data-config-id="${configId}"]`);
    }

    updateConfigTestResult(configId, status, message) {
        const configElement = this.findConfigElement(configId);
        if (!configElement) return;
        
        let resultElement = configElement.querySelector('.test-result');
        if (!resultElement) {
            resultElement = document.createElement('div');
            resultElement.className = 'test-result';
            configElement.querySelector('.ai-config-info').appendChild(resultElement);
        }
        
        resultElement.className = `test-result test-${status}`;
        resultElement.textContent = `测试结果: ${message}`;
        
        // 3秒后自动清除结果
        setTimeout(() => {
            if (resultElement.parentNode) {
                resultElement.remove();
            }
        }, 3000);
    }

    async testAllAiConfigs() {
        this.updateStatus('正在测试所有AI配置...', 'info');
        
        for (const [configId, config] of Object.entries(this.aiConfigs)) {
            if (config.enabled) {
                await this.testAiConfigConnection(configId);
                // 添加短暂延迟避免请求过于频繁
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
        
        this.updateStatus('所有AI配置测试完成', 'success');
    }

    async addAiConfig() {
        try {
            const configData = {
                name: this.newAiNameInput?.value.trim(),
                description: this.newAiDescriptionInput?.value.trim(),
                base_url: this.newAiBaseUrlInput?.value.trim(),
                api_key: this.newAiApiKeyInput?.value.trim(),
                main_model: this.newAiMainModelInput?.value.trim(),
                assistant_model: this.newAiAssistantModelInput?.value.trim(),
                enabled: true
            };
            
            // 验证必填字段
            if (!configData.name || !configData.base_url || !configData.api_key || !configData.main_model) {
                this.updateStatus('请填写所有必填字段（名称、API地址、API密钥、主模型）', 'error');
                return;
            }
            
            this.setButtonLoading(this.addAiConfigBtn, true);
            
            const response = await fetch('/api/ai-configs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(configData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.updateStatus(result.message, 'success');
                this.clearAiForm();
                await this.loadAiConfigs();
                this.renderAiConfigsList();
            } else {
                this.updateStatus(`添加AI配置失败: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('添加AI配置异常:', error);
            this.updateStatus(`添加AI配置异常: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(this.addAiConfigBtn, false);
        }
    }
    
    clearAiForm() {
        if (this.newAiNameInput) this.newAiNameInput.value = '';
        if (this.newAiDescriptionInput) this.newAiDescriptionInput.value = '';
        if (this.newAiBaseUrlInput) this.newAiBaseUrlInput.value = '';
        if (this.newAiApiKeyInput) this.newAiApiKeyInput.value = '';
        if (this.newAiMainModelInput) this.newAiMainModelInput.value = '';
        if (this.newAiAssistantModelInput) this.newAiAssistantModelInput.value = '';
    }
    
    editAiConfig(configId) {
        // 找到要编辑的配置
        const config = this.aiConfigs.find(c => c.id === configId);
        if (!config) {
            this.updateStatus('配置不存在', 'error');
            return;
        }
        
        // 创建编辑弹窗
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'block';
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>编辑AI配置</h3>
                    <button class="modal-close" id="close-edit-ai-modal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <label>配置名称:</label>
                        <input type="text" id="edit-ai-name" value="${this.escapeHtml(config.name)}" placeholder="配置名称">
                    </div>
                    <div class="row">
                        <label>描述:</label>
                        <input type="text" id="edit-ai-description" value="${this.escapeHtml(config.description || '')}" placeholder="描述（可选）">
                    </div>
                    <div class="row">
                        <label>API地址:</label>
                        <input type="url" id="edit-ai-base-url" value="${this.escapeHtml(config.base_url)}" placeholder="API地址">
                    </div>
                    <div class="row">
                        <label>API密钥:</label>
                        <input type="text" id="edit-ai-api-key" value="${this.escapeHtml(config.api_key)}" placeholder="API密钥">
                    </div>
                    <div class="row">
                        <label>主模型:</label>
                        <input type="text" id="edit-ai-main-model" value="${this.escapeHtml(config.main_model)}" placeholder="主模型名称">
                    </div>
                    <div class="row">
                        <label>助手模型:</label>
                        <input type="text" id="edit-ai-assistant-model" value="${this.escapeHtml(config.assistant_model || '')}" placeholder="助手模型（可选）">
                    </div>
                    <div class="row">
                        <label>
                            <input type="checkbox" id="edit-ai-enabled" ${config.enabled ? 'checked' : ''}>
                            启用此配置
                        </label>
                    </div>
                </div>
                <div class="modal-footer">
                    <button id="save-ai-edit" class="btn-success">保存修改</button>
                    <button id="cancel-ai-edit" class="btn-secondary">取消</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 绑定事件
        const closeBtn = modal.querySelector('#close-edit-ai-modal');
        const cancelBtn = modal.querySelector('#cancel-ai-edit');
        const saveBtn = modal.querySelector('#save-ai-edit');
        
        const nameInput = modal.querySelector('#edit-ai-name');
        const descriptionInput = modal.querySelector('#edit-ai-description');
        const baseUrlInput = modal.querySelector('#edit-ai-base-url');
        const apiKeyInput = modal.querySelector('#edit-ai-api-key');
        const mainModelInput = modal.querySelector('#edit-ai-main-model');
        const assistantModelInput = modal.querySelector('#edit-ai-assistant-model');
        const enabledCheckbox = modal.querySelector('#edit-ai-enabled');
        
        const closeModal = () => {
            document.body.removeChild(modal);
        };
        
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        
        // 点击模态框外部关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
        
        saveBtn.addEventListener('click', async () => {
            const name = nameInput.value.trim();
            const description = descriptionInput.value.trim();
            const baseUrl = baseUrlInput.value.trim();
            const apiKey = apiKeyInput.value.trim();
            const mainModel = mainModelInput.value.trim();
            const assistantModel = assistantModelInput.value.trim();
            const enabled = enabledCheckbox.checked;
            
            if (!name || !baseUrl || !apiKey || !mainModel) {
                alert('配置名称、API地址、API密钥和主模型不能为空');
                return;
            }
            
            try {
                this.setButtonLoading(saveBtn, true);
                
                const updateData = {
                    name,
                    description,
                    base_url: baseUrl,
                    api_key: apiKey,
                    main_model: mainModel,
                    assistant_model: assistantModel,
                    enabled
                };
                
                const response = await fetch(`/api/ai-configs/${configId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updateData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.updateStatus('AI配置修改成功', 'success');
                    await this.loadAiConfigs(); // 重新加载配置列表
                    this.renderAiConfigsList(); // 刷新显示
                    closeModal();
                } else {
                    this.updateStatus(`修改失败: ${result.error}`, 'error');
                }
            } catch (error) {
                this.updateStatus(`修改异常: ${error.message}`, 'error');
            } finally {
                this.setButtonLoading(saveBtn, false);
            }
        });
    }
    
    async deleteAiConfig(configId) {
        if (!confirm('确定要删除这个AI配置吗？此操作不可撤销。')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/ai-configs/${configId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.updateStatus(result.message, 'success');
                await this.loadAiConfigs();
                this.renderAiConfigsList();
            } else {
                this.updateStatus(`删除AI配置失败: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('删除AI配置异常:', error);
            this.updateStatus(`删除AI配置异常: ${error.message}`, 'error');
        }
    }
    
    openAiConfigModal() {
        if (this.aiConfigModal) {
            this.aiConfigModal.style.display = 'block';
            this.renderAiConfigsList();
        }
    }

    closeAiConfigModal() {
        if (this.aiConfigModal) {
            this.aiConfigModal.style.display = 'none';
        }
    }

    // ===== 自动发布管理 =====

    async openAutoPublishModal() {
        if (this.autoPublishModal) {
            this.autoPublishModal.style.display = 'block';
            await this.loadAutoPublishTopics();
            await this.loadAutoPublishPrompts();
            await this.loadAutoPublishConfigs();
        }
    }

    closeAutoPublishModal() {
        if (this.autoPublishModal) {
            this.autoPublishModal.style.display = 'none';
        }
    }

    async loadAutoPublishPrompts() {
        try {
            // 填充提示词选择下拉框
            if (this.autoPublishPromptSelect) {
                this.autoPublishPromptSelect.innerHTML = '<option value="">使用当前选定的提示词</option>';
                
                // 获取所有提示词
                const promptKeys = Object.keys(this.prompts);
                promptKeys.forEach(key => {
                    const option = document.createElement('option');
                    option.value = key;
                    option.textContent = key;
                    this.autoPublishPromptSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('加载自动发布提示词失败:', error);
        }
    }

    async loadAutoPublishTopics() {
        try {
            // 重用现有的话题加载逻辑
            if (this.topics.length === 0) {
                await this.loadTopics();
            }
            
            // 填充话题选择下拉框
            if (this.autoPublishTopicSelect) {
                this.autoPublishTopicSelect.innerHTML = '<option value="">请选择话题</option>';
                
                // 按分组组织话题
                const groupedTopics = {};
                this.topics.forEach(topic => {
                    const groupName = topic.group_name || '未分组';
                    if (!groupedTopics[groupName]) {
                        groupedTopics[groupName] = [];
                    }
                    groupedTopics[groupName].push(topic);
                });
                
                // 渲染分组选项
                Object.keys(groupedTopics).sort().forEach(groupName => {
                    const optgroup = document.createElement('optgroup');
                    optgroup.label = groupName;
                    
                    groupedTopics[groupName].forEach(topic => {
                        const option = document.createElement('option');
                        option.value = topic.id;
                        option.textContent = `${topic.name} (${topic.id})`;
                        optgroup.appendChild(option);
                    });
                    
                    this.autoPublishTopicSelect.appendChild(optgroup);
                });
            }
        } catch (error) {
            console.error('加载自动发布话题失败:', error);
            this.updateStatus('加载话题失败: ' + error.message, 'error');
        }
    }

    async loadAutoPublishConfigs() {
        try {
            const response = await fetch('/api/auto-publish');
            const result = await response.json();
            
            if (result.success) {
                this.renderAutoPublishConfigs(result.data);
                this.updateAutoPublishStats(result.data);
            } else {
                this.updateStatus('加载自动发布配置失败: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('加载自动发布配置失败:', error);
            this.updateStatus('加载自动发布配置失败: ' + error.message, 'error');
        }
    }

    renderAutoPublishConfigs(configs) {
        if (!this.autoPublishListContainer) return;
        
        if (configs.length === 0) {
            this.autoPublishListContainer.innerHTML = `
                <div class="auto-publish-empty-state">
                    <div class="empty-icon">🤖</div>
                    <div class="empty-text">暂无自动发布配置</div>
                    <div class="empty-hint">创建第一个自动发布配置开始使用</div>
                </div>
            `;
            return;
        }
        
        const html = configs.map(config => {
            const isActive = config.is_active;
            const progress = config.max_posts === -1 ? 0 : 
                            (config.current_posts / config.max_posts) * 100;
            const progressText = config.max_posts === -1 ? 
                                `已发布: ${config.current_posts} 篇 (无限制)` :
                                `已发布: ${config.current_posts}/${config.max_posts} 篇`;
            
            return `
                <div class="auto-publish-config-item">
                    <div class="auto-publish-config-info">
                        <div class="config-title">${config.topic_name || '未知话题'}</div>
                        <div class="config-details">
                            <div class="config-detail-item">
                                <span class="config-detail-label">话题ID:</span>
                                <span>${config.topic_id}</span>
                            </div>
                            <div class="config-detail-item">
                                <span class="config-detail-label">分组:</span>
                                <span>${config.topic_group || '未分组'}</span>
                            </div>
                            <div class="config-detail-item">
                                <span class="config-detail-label">发布方式:</span>
                                <span>${config.publish_type === 'anonymous' ? '匿名' : '实名'}</span>
                            </div>
                            <div class="config-detail-item">
                                <span class="config-detail-label">发布间隔:</span>
                                <span class="interval-display">${config.min_interval || 30}-${config.max_interval || 60}分钟</span>
                            </div>
                            <div class="config-detail-item">
                                <span class="config-detail-label">状态:</span>
                                <span class="auto-publish-status ${isActive ? 'active' : 'inactive'}">
                                    ${isActive ? '激活' : '停用'}
                                </span>
                            </div>
                            <div class="config-detail-item">
                                <span class="config-detail-label">最后发布:</span>
                                <span>${config.last_published_at ? new Date(config.last_published_at).toLocaleString() : '从未发布'}</span>
                            </div>
                        </div>
                        ${config.max_posts !== -1 ? `
                            <div class="auto-publish-progress">
                                <div class="auto-publish-progress-bar">
                                    <div class="auto-publish-progress-fill" style="width: ${Math.min(progress, 100)}%"></div>
                                </div>
                                <div class="auto-publish-progress-text">${progressText}</div>
                            </div>
                        ` : `
                            <div class="auto-publish-progress">
                                <div class="auto-publish-progress-text">${progressText}</div>
                            </div>
                        `}
                    </div>
                    <div class="auto-publish-config-actions">
                        <button class="btn btn-toggle ${isActive ? 'active' : ''}" 
                                onclick="app.toggleAutoPublishConfig('${config.id}', ${!isActive})">
                            ${isActive ? '停用' : '激活'}
                        </button>
                        <button class="btn btn-reset" 
                                onclick="app.resetAutoPublishPosts('${config.id}')"
                                title="重置发布数量">
                            重置
                        </button>
                        <button class="btn btn-danger" 
                                onclick="app.deleteAutoPublishConfig('${config.id}')"
                                title="删除配置">
                            删除
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        this.autoPublishListContainer.innerHTML = html;
    }

    updateAutoPublishStats(configs) {
        const totalCount = configs.length;
        const activeCount = configs.filter(config => config.is_active).length;
        
        if (this.autoPublishTotalCount) {
            this.autoPublishTotalCount.textContent = totalCount;
        }
        if (this.autoPublishActiveCount) {
            this.autoPublishActiveCount.textContent = activeCount;
        }
    }

    async createAutoPublishConfig() {
        try {
            const topicId = this.autoPublishTopicSelect?.value;
            const promptKey = this.autoPublishPromptSelect?.value;
            const publishType = this.autoPublishPublishTypeSelect?.value || 'anonymous';
            const maxPosts = parseInt(this.autoPublishMaxPostsInput?.value || '-1');
            const minInterval = parseInt(document.getElementById('auto-publish-min-interval')?.value || '30');
            const maxInterval = parseInt(document.getElementById('auto-publish-max-interval')?.value || '60');
            
            if (!topicId) {
                this.updateStatus('请选择话题', 'error');
                return;
            }
            
            // 验证间隔设置
            if (minInterval < 1 || maxInterval < 1) {
                this.updateStatus('发布间隔必须大于0分钟', 'error');
                return;
            }
            
            if (minInterval > maxInterval) {
                this.updateStatus('最小间隔不能大于最大间隔', 'error');
                return;
            }
            
            const data = {
                topic_id: topicId,
                publish_type: publishType,
                max_posts: maxPosts,
                min_interval: minInterval,
                max_interval: maxInterval
            };
            
            // 如果选择了特定的提示词，添加到数据中
            if (promptKey) {
                data.prompt_key = promptKey;
            }
            
            const response = await fetch('/api/auto-publish', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 显示详细的成功信息
                let message = result.message;
                if (result.cycle_started) {
                    message += ' - 自动循环已启动！';
                } else {
                    message += ' - 警告：自动循环启动失败，请检查日志';
                }
                this.updateStatus(message, result.cycle_started ? 'success' : 'warning');
                
                // 重置表单
                if (this.autoPublishTopicSelect) this.autoPublishTopicSelect.value = '';
                if (this.autoPublishPromptSelect) this.autoPublishPromptSelect.value = '';
                if (this.autoPublishPublishTypeSelect) this.autoPublishPublishTypeSelect.value = 'anonymous';
                if (this.autoPublishMaxPostsInput) this.autoPublishMaxPostsInput.value = '-1';
                const minIntervalInput = document.getElementById('auto-publish-min-interval');
                const maxIntervalInput = document.getElementById('auto-publish-max-interval');
                if (minIntervalInput) minIntervalInput.value = '30';
                if (maxIntervalInput) maxIntervalInput.value = '60';
                // 重新加载配置列表
                await this.loadAutoPublishConfigs();
            } else {
                this.updateStatus('创建配置失败: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('创建自动发布配置失败:', error);
            this.updateStatus('创建配置失败: ' + error.message, 'error');
        }
    }

    async toggleAutoPublishConfig(configId, isActive) {
        try {
            const response = await fetch(`/api/auto-publish/${configId}/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ is_active: isActive })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.updateStatus(result.message, 'success');
                await this.loadAutoPublishConfigs();
            } else {
                this.updateStatus('切换配置状态失败: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('切换自动发布配置状态失败:', error);
            this.updateStatus('切换配置状态失败: ' + error.message, 'error');
        }
    }

    async resetAutoPublishPosts(configId) {
        if (!confirm('确定要重置该配置的发布数量吗？')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/auto-publish/${configId}/reset`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.updateStatus(result.message, 'success');
                await this.loadAutoPublishConfigs();
            } else {
                this.updateStatus('重置发布数量失败: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('重置自动发布发布数量失败:', error);
            this.updateStatus('重置发布数量失败: ' + error.message, 'error');
        }
    }

    async deleteAutoPublishConfig(configId) {
        if (!confirm('确定要删除这个自动发布配置吗？删除后不可恢复。')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/auto-publish/${configId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.updateStatus(result.message, 'success');
                await this.loadAutoPublishConfigs();
            } else {
                this.updateStatus('删除配置失败: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('删除自动发布配置失败:', error);
            this.updateStatus('删除配置失败: ' + error.message, 'error');
        }
    }
}

// 全局实例，供HTML中的onclick事件使用
let app;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    app = new MaimaiPublisher();
});
