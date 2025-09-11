# 数据库目录

本目录包含脉脉自动发布系统的数据库相关文件。

## 文件结构

```
database/
├── schema.sql          # 完整的数据库表结构定义
├── init_db.py         # 数据库初始化脚本
├── migrations/        # 数据库迁移脚本目录
│   ├── README.md
│   ├── add_publish_type_fields.sql
│   ├── migrate_auto_publish_configs.sql
│   └── remove_topics_publish_type.sql
└── README.md          # 本文件
```

## 使用说明

### 1. 初始化数据库

对于新部署，使用初始化脚本：

```bash
cd database
python init_db.py
```

### 2. 重置数据库

如果需要完全重置数据库（会删除所有数据）：

```bash
python init_db.py --reset --force
```

### 3. 执行数据库迁移

如果系统已有数据，建议使用迁移脚本：

```bash
cd database/migrations
python migrate.py status    # 查看迁移状态
python migrate.py migrate   # 执行待迁移脚本
```

### 4. 手动执行SQL

如果需要手动执行schema：

```bash
mysql -h 116.205.244.106 -u root -p maimaichat < schema.sql
```

## 数据库表说明

### 核心表

- `ai_configs` - AI配置信息
- `topics` - 话题信息
- `auto_publish_configs` - 自动发布配置
- `scheduled_posts` - 定时发布任务
- `prompts` - 提示词模板

### 辅助表

- `ai_config_settings` - AI配置设置
- `keyword_groups` - 关键词分组
- `keywords` - 关键词数据
- `ai_conversations` - AI对话历史
- `scheduled_requests` - 定时HTTP请求
- `groups` - 话题分组（备用表）

## 迁移历史

重要的数据库结构变更记录在 `migrations/` 目录中。

## 注意事项

1. 数据库配置在 `init_db.py` 中硬编码，生产环境需要修改
2. 所有表使用 `utf8mb4` 字符集
3. 外键约束已配置，删除时需注意级联关系
4. 备份重要数据后再执行重置操作