# 项目结构说明

本文档详细说明了项目的目录结构和文件组织方式。

## 目录结构总览

```
DataProcessing/
├── src/                  # 核心源代码
├── data/                 # 数据存储
├── config/               # 配置文件
├── tests/                # 测试代码
├── scripts/              # 辅助脚本
├── docs/                 # 项目文档
├── requirements.txt      # Python依赖
└── README.md            # 项目说明
```

## 详细说明

### 📦 src/ - 源代码目录
包含项目的所有核心代码。

```
src/
├── config/           # 配置管理模块
│   ├── settings.py   # 配置加载和管理
│   └── __init__.py
├── extractors/       # 数据提取模块
│   ├── csv_reader.py         # CSV文件读取
│   ├── wikipedia_extractor.py # Wikipedia数据抓取
│   └── __init__.py
├── processors/       # 数据处理模块
│   ├── ai_enhancer.py              # AI增强处理
│   ├── entity_recognizer.py        # 实体识别
│   ├── organization_deduplicator.py # 组织去重
│   ├── organization_hierarchy.py    # 组织层级
│   ├── relationship_mapper.py       # 关系映射
│   ├── text_chunker.py             # 文本分块
│   ├── text_preprocessor.py        # 文本预处理
│   └── __init__.py
├── validators/       # 数据验证模块
│   ├── schema_validator.py # Schema验证
│   └── __init__.py
├── exporters/        # 数据导出模块
│   ├── csv_writer.py   # CSV文件写入
│   └── __init__.py
├── utils/            # 工具模块
│   ├── logger.py       # 日志记录
│   ├── rate_limiter.py # 速率限制
│   ├── retry.py        # 重试机制
│   └── __init__.py
└── main.py           # 主程序入口
```

### 📊 data/ - 数据目录
存储所有输入、输出和中间数据。

```
data/
├── input/            # 输入数据
│   └── 人物信息.csv  # 原始人物数据
├── intermediate/     # 中间数据和缓存
│   ├── ai_responses.json
│   ├── enhanced_people.json
│   ├── extracted_entities.json
│   ├── normalized_entities.json
│   ├── organization_dedup_cache.json
│   ├── organization_hierarchy_cache.json
│   ├── processing_summary.json
│   ├── quality_report.json
│   ├── wikipedia_cache.json
│   └── wikipedia_data.json
└── output/           # 最终输出
    ├── People.csv
    ├── Organizations.csv
    ├── Parties.csv
    └── Sectors.csv
```

### ⚙️ config/ - 配置目录
存储所有配置文件。

```
config/
├── .env                   # 环境变量和API密钥（不提交到Git）
├── .env.example           # 环境变量示例
├── party_colors.json      # 政党颜色配置
└── sector_mappings.json   # 行业领域映射
```

### 🧪 tests/ - 测试目录
包含所有测试文件。详见 [tests/README.md](../tests/README.md)

```
tests/
├── test_api_connection.py
├── test_api_key.py
├── test_ai_enhancer_api.py
├── test_wikipedia_*.py
├── test_organization_*.py
└── ...
```

### 🔧 scripts/ - 脚本目录
存储辅助脚本和监控工具。详见 [scripts/README.md](../scripts/README.md)

```
scripts/
├── check_progress.py      # 检查处理进度
├── live_monitor.py        # 实时监控
├── monitor_pipeline.py    # 管道监控
└── quick_status.bat       # 快速状态检查
```

### 📚 docs/ - 文档目录
项目相关的所有文档。

```
docs/
├── PROJECT_STRUCTURE.md                 # 本文件
├── PROJECT_PROCESS_GUIDE.md            # 项目流程指南
├── ORGANIZATION_FEATURES_SUMMARY.md    # 组织功能总结
├── ORGANIZATION_DEDUPLICATION.md       # 组织去重文档
├── NEXT_STEPS.md                       # 后续步骤
└── 数据库结构分析报告.md               # 数据库结构分析
```

## 文件命名规范

### Python模块
- 使用小写字母和下划线：`wikipedia_extractor.py`
- 类名使用驼峰命名：`WikipediaExtractor`
- 函数使用小写下划线：`extract_data()`

### 测试文件
- 以 `test_` 开头：`test_api_connection.py`
- 对应被测试的模块名称

### 配置文件
- JSON配置使用下划线：`party_colors.json`
- 环境变量文件：`.env`

### 文档文件
- Markdown格式：`.md`
- 大写加下划线：`PROJECT_STRUCTURE.md`
- 中文文档：`数据库结构分析报告.md`

## 数据流向

```
人物信息.csv (input)
    ↓
csv_reader.py → 读取原始数据
    ↓
entity_recognizer.py → 实体识别
    ↓
wikipedia_extractor.py → 获取Wikipedia数据
    ↓
ai_enhancer.py → AI增强补全
    ↓
organization_deduplicator.py → 组织去重
    ↓
relationship_mapper.py → 建立关系
    ↓
csv_writer.py → 导出CSV
    ↓
People.csv, Organizations.csv, etc. (output)
```

## 关键配置文件

### .env 环境变量
```env
ANTHROPIC_API_KEY=sk-ant-xxx
BATCH_SIZE=10
ENABLE_WIKIPEDIA=true
MAX_CLAUDE_REQUESTS_PER_MINUTE=50
```

### party_colors.json
定义各政党的颜色编码。

### sector_mappings.json
定义行业领域的分类规则和映射关系。

## 开发指南

### 添加新功能
1. 在 `src/` 对应模块下创建新文件
2. 在 `tests/` 下创建对应测试文件
3. 在 `docs/` 下更新相关文档

### 修改配置
1. 更新 `config/.env.example` 示例
2. 在 `src/config/settings.py` 中添加配置项
3. 更新 README.md 中的配置说明

### 添加依赖
1. 使用 pip 安装新依赖
2. 更新 `requirements.txt`：`pip freeze > requirements.txt`

## 版本控制

### .gitignore 规则
- 忽略 `config/.env`（敏感信息）
- 忽略 `data/intermediate/*`（临时文件）
- 忽略 `data/output/*`（生成文件）
- 忽略 `__pycache__/`（Python缓存）
- 忽略 `test_output/`（测试输出）

### 提交指南
- 提交前运行测试确保代码正常
- 使用有意义的提交信息
- 不要提交敏感信息（API密钥等）

## 常见问题

**Q: 如何重新组织项目结构？**
A: 项目结构已按照功能模块清晰划分，建议保持当前结构。

**Q: 在哪里添加新的数据处理模块？**
A: 在 `src/processors/` 目录下创建新的 Python 文件。

**Q: 如何管理临时文件？**
A: 所有临时文件应存放在 `data/intermediate/` 目录，该目录已配置在 .gitignore 中。

**Q: 文档应该放在哪里？**
A: 所有项目文档统一放在 `docs/` 目录，README.md 保留在根目录作为项目入口文档。
