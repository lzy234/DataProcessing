# 组织去重功能说明

## 概述

本系统现在包含基于 AI 的组织去重功能，可以智能识别和合并同一组织的不同表述方式。

## 功能特点

### 1. 智能识别重复组织

AI 可以识别以下类型的重复：

- **缩写 vs 全称**：`CIA` ↔ `Central Intelligence Agency`
- **有无国家前缀**：`Department of State` ↔ `U.S. Department of State`
- **标点符号差异**：`U.S. Senate` ↔ `US Senate`
- **不同写法**：`State Department` ↔ `U.S. Department of State`

### 2. 自动规范化

系统会自动选择最官方、最正式的名称作为标准名称（canonical name），并将所有变体映射到标准名称。

### 3. 级联更新

去重后，系统会自动更新：
- 人员的组织归属关系
- 组织层级关系
- 所有相关的 ID 映射

## 工作流程

完整的组织处理流程包含以下步骤：

```
1. 从 Wikipedia 提取组织名称（AI 提取）
   ↓
2. 组织去重（AI 识别重复）
   ↓
3. 分析组织层级关系（AI 分析父组织）
   ↓
4. 分配唯一 ID
   ↓
5. 建立人员-组织关系映射
```

## 测试示例

### 输入数据

```
原始组织（12个）：
1. CIA
2. Central Intelligence Agency
3. Department of Defense
4. Department of State
5. DoD
6. State Department
7. U.S. Department of Defense
8. U.S. Department of State
9. U.S. Senate
10. US Senate
11. United States Senate
12. White House
```

### 去重结果

```
去重后组织（5个）：
1. Central Intelligence Agency
2. U.S. Department of Defense
3. U.S. Department of State
4. United States Senate
5. White House

合并的重复项（7个）：
- CIA → Central Intelligence Agency
- Department of Defense → U.S. Department of Defense
- Department of State → U.S. Department of State
- DoD → U.S. Department of Defense
- State Department → U.S. Department of State
- U.S. Senate → United States Senate
- US Senate → United States Senate
```

## 技术实现

### 核心组件

1. **OrganizationDeduplicator** (`src/processors/organization_deduplicator.py`)
   - 使用 AI 分析组织名称相似性
   - 生成标准名称映射
   - 缓存去重结果以提高效率

2. **主流程集成** (`src/main.py`)
   - Step 3.0: 从 AI 增强数据中提取组织
   - Step 3.0.3: **AI 去重组织**（新增）
   - Step 3.0.5: 分析组织层级
   - Step 3.1: 分配唯一 ID

### AI Prompt 策略

去重器使用精心设计的 prompt，指导 AI：

1. 识别确定性重复（conservative approach）
2. 选择最官方的名称作为标准
3. 仅在有把握时才合并
4. 处理常见的美国政府组织模式

### 缓存机制

- 缓存文件：`data/intermediate/organization_dedup_cache.json`
- 缓存键：排序后的组织名称列表
- 好处：避免重复 API 调用，提高处理速度

## 使用方法

### 在主流程中自动运行

去重功能已集成到主流程中，运行 `main.py` 时会自动执行：

```bash
python -m src.main
```

日志中会显示：

```
Step 3.0.3: Deduplicating organizations with AI
After deduplication: X organizations (merged Y duplicates)
```

### 单独测试去重功能

运行测试脚本验证去重功能：

```bash
# 基础去重测试
python test_organization_deduplication.py

# 完整流程测试（提取 + 去重 + 层级）
python test_full_organization_flow.py
```

## 配置选项

去重功能需要以下配置：

```env
# config/.env
ANTHROPIC_API_KEY=your_api_key
ANTHROPIC_BASE_URL=https://api.deepseek.com
MAX_CLAUDE_REQUESTS_PER_MINUTE=50
```

## 性能考虑

1. **API 调用**：
   - 每批组织调用 1 次 AI API
   - 使用缓存避免重复调用
   - 受 rate limiter 限制

2. **处理时间**：
   - 小批量（<20 个组织）：~5-10 秒
   - 中批量（20-50 个组织）：~10-20 秒
   - 大批量（>50 个组织）：建议分批处理

3. **准确性**：
   - 保守策略：仅合并确定性重复
   - 对于不确定的情况，保持为独立组织
   - 可通过日志检查合并决策

## 未来改进

可能的增强方向：

1. **增量去重**：对新增组织与已有组织进行去重
2. **手动规则**：支持用户定义的组织别名映射
3. **批量优化**：对大规模组织列表进行分批去重
4. **质量评分**：为每个去重决策提供置信度评分

## 故障排查

### 问题：去重后组织数量没有减少

**可能原因**：
- 组织名称确实都是独立的（没有重复）
- AI 采取保守策略，不确定时不合并

**检查方法**：
- 查看日志中的 "Found X duplicate groups"
- 检查缓存文件 `organization_dedup_cache.json`

### 问题：某些明显重复的组织没有合并

**可能原因**：
- AI 的 prompt 需要调整
- 缺少必要的上下文信息

**解决方法**：
- 调整 `OrganizationDeduplicator._find_duplicate_groups()` 中的 prompt
- 清空缓存文件重新运行
- 考虑添加手动规则

### 问题：错误合并了不同的组织

**可能原因**：
- Prompt 不够保守
- 组织名称过于相似

**解决方法**：
- 在 prompt 中增加更严格的约束
- 清空对应的缓存条目
- 添加排除规则

## 示例代码

### 独立使用去重器

```python
from src.processors.organization_deduplicator import OrganizationDeduplicator

# 准备组织数据
organizations = {
    "CIA": {"name": "CIA", "sector": "Intelligence"},
    "Central Intelligence Agency": {"name": "Central Intelligence Agency", "sector": "Intelligence"}
}

# 执行去重
deduplicator = OrganizationDeduplicator()
deduplicated_orgs, name_mapping = deduplicator.deduplicate_organizations(organizations)

# 使用映射更新数据
for person in people:
    original_org = person['organization']
    person['organization'] = name_mapping.get(original_org, original_org)
```

## 相关文件

- 核心实现：`src/processors/organization_deduplicator.py`
- 主流程集成：`src/main.py` (Step 3.0.3)
- 测试脚本：`test_organization_deduplication.py`
- 完整流程测试：`test_full_organization_flow.py`
- 缓存文件：`data/intermediate/organization_dedup_cache.json`

## 总结

AI 去重功能大大提高了组织数据的质量：

✅ 自动识别同一组织的不同表述
✅ 使用官方标准名称
✅ 保持数据一致性
✅ 减少冗余组织条目
✅ 提高后续分析的准确性

通过智能去重，系统能够更好地理解组织结构，建立准确的人员-组织关系，并为数据分析提供高质量的基础。
