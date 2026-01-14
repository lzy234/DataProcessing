# 政治人物数据采集和AI增强系统

该系统使用 Python + Claude API + Wikipedia API 将 100 个政治人物的基础信息补全为符合 Payload CMS 数据库结构的完整数据。

## 功能特点

- 📊 自动从原始CSV提取人物、组织、政党、领域等实体
- 🌐 集成Wikipedia API获取传记数据
- 🤖 使用Claude API智能补全缺失字段
- ✅ 完整的数据验证和质量报告
- 📁 输出4个标准CSV文件，可直接导入Payload CMS

## 输出文件

- `People.csv` - 100个人物的完整档案
- `Organizations.csv` - 提取的所有组织机构
- `Parties.csv` - 政党信息（含颜色编码）
- `Sectors.csv` - 行业领域分类

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

复制 `.env.example` 为 `.env` 并填入你的Claude API密钥：

```bash
cp config/.env.example config/.env
```

编辑 `config/.env`:
```env
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

### 3. 准备数据

确保原始CSV文件位于 `data/input/人物信息.csv`

### 4. 运行处理流程

```bash
python src/main.py
```

处理完成后，输出文件将保存在 `data/output/` 目录。

## 项目结构

```
DataProcessing/
├── src/                  # 源代码
│   ├── config/           # 配置管理
│   ├── extractors/       # 数据提取（CSV、Wikipedia）
│   ├── processors/       # 数据处理（AI增强、实体识别）
│   ├── validators/       # 数据验证
│   ├── exporters/        # CSV导出
│   ├── utils/            # 工具类（日志、重试、限流）
│   └── main.py           # 主流程
├── data/                 # 数据文件
│   ├── input/            # 原始CSV
│   ├── intermediate/     # 中间缓存和日志
│   └── output/           # 最终输出CSV
├── config/               # 配置文件
│   ├── .env              # API密钥（gitignored）
│   ├── sector_mappings.json  # 领域分类规则
│   └── party_colors.json     # 政党颜色
├── tests/                # 测试文件
│   ├── test_*.py         # 各模块单元测试
│   └── ...
├── scripts/              # 实用脚本
│   ├── check_progress.py     # 检查处理进度
│   ├── live_monitor.py       # 实时监控
│   ├── monitor_pipeline.py   # 管道监控
│   └── quick_status.bat      # 快速状态检查
├── docs/                 # 文档
│   ├── PROJECT_PROCESS_GUIDE.md          # 项目流程指南
│   ├── ORGANIZATION_FEATURES_SUMMARY.md  # 组织功能总结
│   ├── ORGANIZATION_DEDUPLICATION.md     # 组织去重文档
│   ├── NEXT_STEPS.md                     # 后续步骤
│   └── 数据库结构分析报告.md             # 数据库结构分析
├── requirements.txt      # Python依赖
└── README.md            # 项目说明
```

## 数据处理流程

1. **Phase 1: 数据提取**
   - 读取原始CSV
   - 实体识别（组织、政党、领域）
   - Wikipedia数据抓取

2. **Phase 2: AI增强**
   - 使用Claude API批量补全字段
   - 生成英文传记
   - 提取结构化信息（出生日期、教育、职业历程）

3. **Phase 3: 实体规范化**
   - 去重和ID分配
   - 建立关系映射
   - 组织层级识别

4. **Phase 4: 验证导出**
   - Schema验证
   - 引用完整性检查
   - 生成CSV文件和质量报告

## 配置选项

在 `config/.env` 中可配置：

- `BATCH_SIZE` - 每批处理的人数（默认10）
- `ENABLE_WIKIPEDIA` - 是否启用Wikipedia抓取（默认true）
- `MAX_CLAUDE_REQUESTS_PER_MINUTE` - Claude API速率限制（默认50）

## 数据质量

系统会生成质量报告：`data/intermediate/quality_report.json`

目标完整度：
- 必填字段：100%
- 出生日期：>85%
- 教育背景：>90%
- 职业历程：>95%

## 成本估算

- Claude API：约 $5-10 (100人，使用Claude 3.5 Sonnet)
- Wikipedia API：免费
- 处理时间：2-4小时

## 故障排除

### 1. ANTHROPIC_API_KEY错误
- 确保已在 `config/.env` 中设置API密钥
- 检查密钥格式：`sk-ant-...`

### 2. CSV读取失败
- 确认文件路径：`data/input/人物信息.csv`
- 检查文件编码（应为UTF-8）

### 3. API速率限制
- 系统会自动重试
- 可调整 `config/.env` 中的速率限制设置

## 后续工作

- 导入CSV到Payload CMS
- 创建Connections表（人物关系网络）
- 设置自动更新流程

## 许可证

MIT License