# CLAUDE.md


## 项目架构

这是一个基于Flask的脉脉自动发布系统，使用AI生成内容并发布到脉脉平台。

### 核心组件

- **app.py**: Flask主应用，提供Web API和静态文件服务
- **config.py**: 配置管理，包含AI API、脉脉API和默认提示词配置
- **modules/**: 核心功能模块
  - `ai_generator.py`: AI内容生成器，封装OpenAI格式API调用
  - `maimai_api.py`: 脉脉API集成，处理内容发布和话题信息获取
  - `storage.py`: 数据存储，提供会话和草稿的本地JSON存储
  - `prompt_store.py`: 提示词管理

### 数据流

1. 前端发送生成请求 → AI API → 返回生成内容
2. 前端发送发布请求 → 脉脉API → 发布到平台
3. 会话和草稿通过JsonKVStore持久化存储

## 常用命令

### 启动开发服务器
```bash
python app.py
```
服务运行在 http://localhost:5000

### 安装依赖
```bash
pip install -r requirements.txt
```

### 查看日志
```bash
# 查看应用日志
tail -f logs/app.log
```

## API架构

### 核心API端点
- `POST /api/generate`: AI内容生成，支持对话历史和单次生成两种模式
- `POST /api/publish`: 发布内容到脉脉
- `POST /api/test-connection`: 测试AI和脉脉API连接状态
- `GET/POST /api/chats/*`: 会话管理（列表、保存、删除）
- `GET/POST /api/drafts/*`: 草稿管理
- `GET/POST /api/prompts`: 提示词模板管理

### AI生成器模式
- **对话模式**: 传递`messages`数组，支持多轮对话上下文
- **单次模式**: 传递`topic`+`custom_prompt`，兼容旧版接口

## 配置说明

### AI API配置 (config.py:14-19)
- 使用OpenAI格式API
- 主模型: claude-sonnet-4-20250514
- 助手模型: gemini-2.5-flash-search
- 已预配置API密钥和端点

### 脉脉API配置 (config.py:21-26)
- 需要在环境变量中设置`MAIMAI_ACCESS_TOKEN`
- 基础URL: https://maimai.cn/api
- 支持话题关联和内容发布

### 存储配置
- 会话存储: `data/chats.json`
- 草稿存储: `data/drafts.json`
- 提示词存储: `logs/prompts.json`
- 应用日志: `logs/app.log`

## 开发注意事项

- 所有API返回标准化的JSON格式: `{success: bool, data/error: any}`
- 使用UTF-8编码处理中文内容
- JsonKVStore提供线程安全的本地存储
- 支持脉脉话题URL解析和ID提取
- AI生成器支持模型切换和参数调整
- 详细的错误日志记录便于调试

## 脉脉API集成特点

- 话题URL解析支持从查询参数提取topic_id
- 发布接口支持HTML内容解析和状态检测
- 连接测试通过用户信息接口验证访问权限
- 支持非JSON响应的兼容性处理