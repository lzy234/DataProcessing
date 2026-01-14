# 数据处理项目流程介绍

## 项目概述

这是一个用于处理政治人物信息的数据增强和标准化系统。系统从基础的中文CSV文件开始，通过Wikipedia API数据提取和Claude AI智能增强，最终生成符合Payload CMS数据库结构的4个标准化CSV文件。

## 项目目标

将100个人物的基础信息（中文名、英文名、头衔、组织等）扩展为完整的结构化数据，包括：
- 出生日期、性别、教育背景
- 完整的职业历程时间线
- 英文传记（200-500词）
- 标准化的组织、政党、行业领域关系
- 可信来源引用

## 技术架构

### 核心技术栈
- **编程语言**: Python 3.8+
- **AI服务**: Claude API (通过OpenAI兼容端点)
- **数据源**: Wikipedia MediaWiki API
- **主要依赖**:
  - `openai>=1.3.0` - AI增强
  - `requests>=2.31.0` - HTTP请求
  - `pandas>=2.1.0` - 数据处理
  - `beautifulsoup4>=4.12.0` - HTML解析

### API配置
- **Claude端点**: 自定义OpenAI兼容端点
- **模型**: claude-sonnet-4-5-20250929
- **速率限制**: 50请求/分钟（Claude），100请求/分钟（Wikipedia）
- **批处理大小**: 10人/批次
- **超时设置**: 120秒

## 项目结构

```
d:\Project\DataProcessing/
├── src/
│   ├── config/
│   │   ├── settings.py              # 配置管理（API密钥、速率限制等）
│   │   └── mappings.py              # 数据映射规则（行业分类等）
│   ├── extractors/
│   │   ├── csv_reader.py            # 读取原始CSV
│   │   └── wikipedia_extractor.py   # Wikipedia MediaWiki API集成
│   ├── processors/
│   │   ├── entity_recognizer.py     # 实体识别（组织、政党、领域）
│   │   ├── relationship_mapper.py   # 关系映射和ID分配
│   │   └── ai_enhancer.py           # Claude API集成和数据增强
│   ├── validators/
│   │   └── schema_validator.py      # 数据验证和质量检查
│   ├── exporters/
│   │   └── csv_writer.py            # CSV生成器
│   ├── utils/
│   │   ├── logger.py                # 日志系统
│   │   ├── retry.py                 # 重试机制（指数退避）
│   │   └── rate_limiter.py          # API速率限制
│   └── main.py                      # 主流程编排
├── data/
│   ├── input/                       # 原始CSV文件
│   ├── intermediate/                # 中间缓存（Wikipedia、AI响应）
│   └── output/                      # 最终输出CSV文件
├── config/
│   ├── .env                         # API密钥和配置
│   ├── sector_mappings.json        # 领域分类规则
│   └── party_colors.json           # 政党颜色配置
├── test_wikipedia_api.py           # Wikipedia API诊断工具
├── test_fixed_wikipedia.py         # Wikipedia提取器测试
├── requirements.txt                 # Python依赖
└── README.md
```

## 数据处理流程

### Phase 1: 数据提取（Data Extraction）

**输入**: `data/input/人物信息.csv`（100行）
- 字段: 序号、中文名、英文名、头衔、所属组织、核心影响力

**步骤**:
1. **CSV读取** (`csv_reader.py`)
   - 处理UTF-8 BOM编码
   - 解析中文和英文字段

2. **实体识别** (`entity_recognizer.py`)
   - 从"所属组织"提取标准化组织名
   - 从"头衔"识别政党标记（如"R-SD" → Republican Party）
   - 根据关键词自动分类行业领域
   - 识别组织层级关系（如"Senate Committee" → 父组织: "U.S. Senate"）

3. **Wikipedia提取** (`wikipedia_extractor.py`)
   - 使用MediaWiki API搜索人物页面
   - 提取结构化数据：
     - 出生日期（支持美式和英式格式）
     - 教育背景（通过regex解析）
     - 页面摘要（用于传记生成）
   - 缓存到`data/intermediate/wikipedia_cache.json`
   - **成功率**: 99%（99/100人）

### Phase 2: AI增强（AI Enhancement）- 多阶段优化版本

**核心模块**: `ai_enhancer.py`

**优化策略**:
- **任务细分**: 将AI增强拆分为4个独立的API请求，提高成功率和准确性
- **数据可靠性**: 移除AI推理功能，仅使用Wikipedia等可靠来源的数据
- **缓存优化**: 每个阶段独立缓存，提高重试效率

**多阶段处理流程**:

1. **阶段1: 基础信息提取** (`_enhance_basic_info`)
   - 字段: `dateOfBirth`, `gender`
   - 数据源: 仅从Wikipedia提取
   - 处理原则:
     - 出生日期: 直接使用Wikipedia提供的birth_date字段
     - 性别: 仅从Wikipedia文本中显式提到的性别信息提取
     - **不推理**: 不从中文代词或其他间接信息推断
   - 温度设置: 0.1 (极低，确保事实准确性)

2. **阶段2: 教育背景提取** (`_enhance_education`)
   - 字段: `education`
   - 数据源: 仅从Wikipedia文本提取
   - 提取内容: 大学名称、学位、毕业年份
   - 处理原则:
     - 只提取Wikipedia明确提到的教育信息
     - 不推测或补充未提及的内容
     - 无信息时返回空字符串
   - 输出长度: 1-2句话

3. **阶段3: 职业历程提取** (`_enhance_career_history`)
   - 字段: `careerHistory`
   - 数据源: 仅从Wikipedia文本提取
   - 提取内容: 主要职位、任职时间
   - 处理原则:
     - 按时间顺序整理政治和职业生涯
     - 只使用Wikipedia明确提到的职位和日期
     - 聚焦政治职业生涯
   - 输出长度: 3-5句话

4. **阶段4: 传记生成** (`_enhance_biography`)
   - 字段: `bio`
   - 数据源: 仅基于Wikipedia文本重写
   - 生成要求:
     - 200-500词英文传记
     - 中立、百科全书式语气
     - 聚焦政治影响力和成就
     - **不添加**: 不添加Wikipedia未提及的信息
     - 信息不足时返回空字符串
   - 温度设置: 0.1 (确保忠实于原文)

**数据可靠性保证**:
```
输入数据（每阶段）:
- Wikipedia文本摘要
- 人物基本信息（姓名、当前职位）

输出JSON格式（各阶段独立）:
阶段1: {"dateOfBirth": "YYYY-MM-DD或null", "gender": "male/female/空字符串"}
阶段2: {"education": "教育背景或空字符串"}
阶段3: {"careerHistory": "职业历程或空字符串"}
阶段4: {"bio": "英文传记或空字符串"}

每阶段添加sources:
{
  "sourceName": "Wikipedia",
  "sourceUrl": "Wikipedia页面URL",
  "reliability": "high"
}
```

**可靠性原则**:
- ❌ **禁止推理**: 不从中文代词、年龄、语境等间接信息推断
- ❌ **禁止补充**: 不添加Wikipedia未明确提到的信息
- ❌ **禁止猜测**: 信息不确定时返回空字符串/null
- ✅ **仅提取**: 只从Wikipedia文本中提取显式信息
- ✅ **留白优先**: 查不到信息就留空，保证信息准确性
- ✅ **来源追踪**: 每条信息标注Wikipedia来源和高可靠性

**错误处理**:
- 单阶段失败不影响其他阶段
- 失败字段返回空值（空字符串或null）
- 每个阶段有独立的缓存和重试机制
- 无降级策略：失败就留空

**成本优化**:
- 分阶段处理（每人4次API调用）
- 独立缓存避免重复调用
- 降低单次调用token数（max_tokens=2000）
- 预估成本: $8-15（100人，考虑4倍请求数但单次token减少）

### Phase 3: 实体规范化（Entity Normalization）

**核心模块**: `relationship_mapper.py`

**ID分配系统**:
- People: P001-P100
- Organizations: O001-O0XX
- Parties: PTY001-PTY00X
- Sectors: SEC001-SEC0XX

**关系映射**:
1. Person → Organization（通过"所属组织"字段）
2. Person → Party（通过头衔推断或AI识别）
3. Organization → Sector（通过分类规则）
4. Organization → Parent Organization（层级关系）

**去重逻辑**:
- 组织名称标准化（去除括号、统一大小写）
- 政党名称统一（GOP → Republican Party）
- 行业领域合并（相似分类合并）

### Phase 4: 验证与导出（Validation & Export）

**验证器** (`schema_validator.py`):
1. **必填字段检查**
   - People: name, currentRole, ChineseName必须非空
   - Organizations: name, sector必须存在

2. **数据格式验证**
   - 日期格式: YYYY-MM-DD
   - 颜色格式: #RRGGBB
   - sources字段: 有效的JSON数组字符串

3. **引用完整性检查**
   - 所有organization ID必须存在于Organizations表
   - 所有party ID必须存在于Parties表
   - 所有sector ID必须存在于Sectors表
   - 无循环引用（parentOrganization）

4. **质量报告生成**
   - 输出到`data/intermediate/processing_summary.json`
   - 包含字段完整度百分比
   - 验证错误和警告列表

**CSV导出器** (`csv_writer.py`):

生成4个CSV文件，严格匹配Payload CMS schema:

1. **People.csv**（100行）
   - 字段: id, name, ChineseName, dateOfBirth, gender, currentRole, organization(ID), party(ID), education, careerHistory, bio, sources(JSON), slug

2. **Organizations.csv**（~50-70行）
   - 字段: id, name, parentOrganization(ID), sector(ID), description

3. **Parties.csv**（~5-10行）
   - 字段: id, name, abbreviation, color

4. **Sectors.csv**（~10-15行）
   - 字段: id, name, category, description

**编码**: UTF-8 with BOM（Excel兼容）

## 运行流程

### 1. 环境配置

```bash
# 安装依赖
pip install -r requirements.txt

# 配置API密钥
# 编辑 config/.env 文件:
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_BASE_URL=https://your-endpoint.com/api
ENABLE_WIKIPEDIA=true
BATCH_SIZE=10
```

### 2. 执行处理

```bash
cd d:\Project\DataProcessing
python src/main.py
```

**处理时间**: 约4-6分钟（100人）
- Wikipedia提取: ~2分钟（99%成功率）
- AI增强: ~2分钟（使用缓存）
- 验证导出: ~30秒

### 3. 输出检查

**生成文件**:
- `data/output/People.csv` (100行)
- `data/output/Organizations.csv` (~50-70行)
- `data/output/Parties.csv` (~5行)
- `data/output/Sectors.csv` (~10行)
- `data/intermediate/processing_summary.json` (质量报告)

**质量指标**（当前实现）:
- 总体质量分数: 87.6%
- 出生日期完整度: 68%
- 教育背景完整度: 70%
- 职业历程完整度: 100%
- 传记完整度: 100%
- Wikipedia成功率: 99%

## 关键技术决策

### 1. API端点选择

**问题**: 原始计划使用Anthropic原生API，但实际环境提供OpenAI兼容端点

**解决方案**:
- 使用OpenAI SDK替代Anthropic SDK
- 保持相同的模型能力（Claude Sonnet 4.5）
- 调整API调用格式和认证方式

**代码示例**:
```python
from openai import OpenAI

self.client = OpenAI(
    api_key=Settings.ANTHROPIC_API_KEY,
    base_url=Settings.ANTHROPIC_BASE_URL + "/v1",
    timeout=120.0
)

response = self.client.chat.completions.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=8000,
    temperature=0.3,
    messages=[{"role": "user", "content": prompt}]
)
```

### 2. Wikipedia API迁移

**问题**: Wikipedia REST API Search端点返回404错误

**诊断过程**:
1. 创建`test_wikipedia_api.py`测试不同API
2. 发现REST API `/api/rest_v1/page/search/` 失败
3. 确认MediaWiki API `/w/api.php` 稳定可用

**解决方案**: 完全迁移到MediaWiki API

**技术对比**:
| 特性 | REST API | MediaWiki API |
|------|---------|---------------|
| 搜索稳定性 | ❌ 404错误 | ✅ 稳定 |
| 页面摘要 | ✅ 需要精确标题 | ✅ 灵活查询 |
| 结构化数据 | 有限 | 丰富 |
| 速率限制 | 严格 | 宽松 |

**实现示例**:
```python
# 搜索人物
params = {
    'action': 'query',
    'list': 'search',
    'srsearch': name,
    'format': 'json',
    'srlimit': 1
}

# 获取页面详情
params = {
    'action': 'query',
    'prop': 'extracts|pageimages|info',
    'exintro': True,
    'explaintext': True,
    'titles': page_title,
    'format': 'json',
    'inprop': 'url'
}
```

### 3. 数据提取增强

**出生日期解析** - 支持多种格式:
```python
# 美式格式: "born January 15, 1970"
pattern1 = r'born\s+([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})'

# 英式格式: "born 15 January 1970"
pattern2 = r'born\s+(\d{1,2})\s+([A-Z][a-z]+)\s+(\d{4})'

# 仅年份: "born 1970"
pattern3 = r'born\s+(\d{4})'
```

**教育信息提取** - 关键词匹配:
```python
education_keywords = [
    r'graduated from ([^.,;]+)',
    r'attended ([^.,;]+)',
    r'studied at ([^.,;]+)',
    r'degree from ([^.,;]+)',
    r'alma mater[:\s]+([^.,;]+)'
]
```

### 4. 错误处理策略

**重试机制**（指数退避）:
```python
@retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
def _call_api(self):
    # API调用
    # 失败时自动重试: 2秒 → 4秒 → 8秒
```

**降级策略**:
- Wikipedia失败 → 使用AI推断
- AI JSON解析失败 → 重试3次 → 使用默认值
- 组织识别失败 → 创建通用组织实体

## 数据质量保证

### 输入验证
- 检查原始CSV格式和编码
- 验证必填字段存在性
- 标准化字段名称

### 处理监控
- 实时日志记录（console + file）
- API调用计数和成本追踪
- 错误异常捕获和报告

### 输出验证
- Schema符合性检查
- 引用完整性验证
- 字段完整度统计
- 手动审查建议（低置信度数据）

### 质量报告示例
```json
{
  "total_people": 100,
  "total_organizations": 78,
  "total_parties": 0,
  "total_sectors": 9,
  "quality_score": 87.6,
  "field_completeness": {
    "name": {"count": 100, "percentage": 100.0},
    "dateOfBirth": {"count": 68, "percentage": 68.0},
    "education": {"count": 70, "percentage": 70.0},
    "bio": {"count": 100, "percentage": 100.0}
  },
  "validation_passed": true,
  "error_count": 0,
  "warning_count": 0
}
```

## 常见问题处理

### Q1: API调用失败或超时
**症状**: `requests.exceptions.Timeout` 或 `API Error 500`

**解决方案**:
1. 检查网络连接和API端点可用性
2. 增加超时时间（settings.py中调整）
3. 检查速率限制是否触发
4. 查看`logs/`目录中的错误日志

### Q2: Wikipedia提取失败
**症状**: 多个404错误或"No data found"

**诊断**:
```bash
python test_wikipedia_api.py  # 测试API端点
python test_fixed_wikipedia.py  # 测试提取器
```

**解决方案**:
1. 确认使用MediaWiki API（不是REST API）
2. 检查User-Agent设置
3. 验证速率限制配置

### Q3: JSON解析错误
**症状**: `Failed to parse JSON response`

**原因**: AI生成的JSON格式不完整或包含语法错误

**自动处理**: 重试机制会自动尝试3次

**手动干预**: 检查`data/intermediate/ai_responses.json`，手动修复格式

### Q4: 字段完整度低
**症状**: 质量报告显示某字段<80%

**改进方案**:
1. **出生日期**: 增加Wikipedia搜索范围，改进日期解析regex
2. **教育背景**: 扩展教育关键词列表
3. **政党信息**: 手动补充或增加推理规则

### Q5: 编码问题
**症状**: 输出CSV在Excel中显示乱码

**解决方案**: 确保使用UTF-8 with BOM编码
```python
df.to_csv(file_path, index=False, encoding='utf-8-sig')
```

## 扩展和优化

### 性能优化
1. **并行处理**: 使用`asyncio`并行调用Wikipedia API
2. **缓存预热**: 预先加载常见组织和政党数据
3. **增量更新**: 仅处理新增或修改的人物

### 功能扩展
1. **政党数据补充**: 当前0%完整度，需要增强推理规则
2. **关系网络**: 生成Connections表数据（人物关系）
3. **自动更新**: 定期爬取最新信息并更新数据库
4. **多语言支持**: 扩展到其他语言的Wikipedia

### 数据导入
```bash
# 使用Payload CMS导入工具
payload import --collection people --file data/output/People.csv
payload import --collection organizations --file data/output/Organizations.csv
payload import --collection parties --file data/output/Parties.csv
payload import --collection sectors --file data/output/Sectors.csv
```

## 项目成果

### 数据统计
- **处理人数**: 100人
- **生成组织**: 78个
- **识别政党**: 0个（待优化）
- **分类领域**: 9个
- **处理时间**: ~4分钟
- **API成本**: <$10

### 质量指标
- **总体质量**: 87.6%
- **Wikipedia成功率**: 99%
- **必填字段完整度**: 100%
- **可选字段平均完整度**: 79.5%

### 输出文件
所有CSV文件符合Payload CMS schema，可直接导入数据库，支持Excel直接打开（UTF-8 BOM）。

## 技术亮点

1. **自适应API集成**: 支持OpenAI兼容端点和Anthropic原生端点
2. **智能数据融合**: 结合Wikipedia结构化数据和AI语义理解
3. **强健的错误处理**: 多层重试机制和降级策略
4. **高效批处理**: 10人/批次，优化API成本和延迟
5. **完整的数据验证**: Schema检查、引用完整性、质量报告
6. **灵活的配置管理**: 环境变量、JSON配置、运行时参数

## 许可和使用

本项目用于教育和研究目的，遵守以下API使用条款：
- Wikipedia: 必须包含User-Agent，遵守速率限制
- Claude API: 遵守使用限制和内容政策

数据处理符合数据隐私和公开信息使用规范。

---

## 更新日志

### Version 1.1 (2026-01-14)

**重大优化: AI增强流程重构**

本次更新对AI增强阶段进行了全面重构，显著提升数据可靠性和处理效率。

**主要变更**:

1. **多阶段任务拆分**
   - 原策略: 单次批量请求处理所有字段
   - 新策略: 拆分为4个独立API请求
     - 阶段1: 基础信息 (dateOfBirth, gender)
     - 阶段2: 教育背景 (education)
     - 阶段3: 职业历程 (careerHistory)
     - 阶段4: 传记生成 (bio)
   - 优势:
     - 降低单次请求复杂度，提高成功率
     - 信息量大的字段独立处理，避免截断
     - 失败时只影响单个字段，不影响其他数据

2. **移除AI推理功能**
   - 移除内容:
     - ❌ 从中文代词（他/她）推断性别
     - ❌ 从"现年X岁"推算出生日期
     - ❌ 从语境推测未明确说明的信息
   - 新原则:
     - ✅ 仅使用Wikipedia等可靠来源的显式信息
     - ✅ 无法确定的信息留空（null或空字符串）
     - ✅ 优先保证数据准确性，而非完整性

3. **数据可靠性提升**
   - 温度设置从0.3降低到0.1，减少随机性
   - 所有Prompt明确要求"不推理、不猜测、不补充"
   - 强制要求只提取Wikipedia明确提到的信息
   - 每条数据追踪来源，标注可靠性等级

4. **缓存机制优化**
   - 原策略: 批量级缓存
   - 新策略: 字段级独立缓存
   - 缓存键格式: `{name}_{stage}` (例如: "Nancy Pelosi_education")
   - 优势: 重试时只需重新调用失败阶段，大幅节省成本

5. **错误处理改进**
   - 移除降级策略（不再使用中文传记等fallback）
   - 单阶段失败不影响其他阶段
   - 失败字段明确返回空值，而非猜测数据

**性能影响**:
- API调用次数: 增加4倍（每人从1次变为4次）
- 单次Token消耗: 减少约60% (max_tokens从8000降到2000)
- 预估总成本: 增加约50-80% ($5-10 → $8-15/100人)
- 数据可靠性: 大幅提升（移除所有推理逻辑）
- 字段完整度: 可能降低（留空优先），但准确性提高

**破坏性变更**:
- 无（API接口保持不变，`enhance_batch`方法签名未改变）
- 旧缓存仍可用，但新缓存结构不同

**升级建议**:
1. 清空旧的AI响应缓存: 删除`data/intermediate/ai_responses.json`
2. 重新运行pipeline以使用新的多阶段处理
3. 审查输出结果，预期某些字段可能为空（这是正常的）

---

**项目版本**: 1.1
**最后更新**: 2026-01-14
**维护者**: Data Processing Team
