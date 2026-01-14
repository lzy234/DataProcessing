# 组织处理功能总结

本文档总结了系统中所有与组织相关的功能模块。

## 功能概览

### 1. 组织提取（AI驱动）✅
- **位置**: `src/processors/ai_enhancer.py` - `_extract_organization()`
- **功能**: 从 Wikipedia 文本中提取当前组织
- **方法**: AI 分析 Wikipedia 摘要
- **输出**: 组织的官方英文名称

### 2. 组织去重（AI驱动）✅ **新增**
- **位置**: `src/processors/organization_deduplicator.py`
- **功能**: 识别并合并同一组织的不同表述
- **方法**: AI 批量分析组织名称相似性
- **识别类型**:
  - 缩写 vs 全称（CIA ↔ Central Intelligence Agency）
  - 有无前缀（Department of State ↔ U.S. Department of State）
  - 标点差异（U.S. Senate ↔ US Senate）
  - 同义表述（State Department ↔ U.S. Department of State）

### 3. 组织层级分析（AI驱动）✅
- **位置**: `src/processors/organization_hierarchy.py`
- **功能**: 确定组织的父级组织
- **方法**: AI 基于 Wikipedia 上下文分析层级关系
- **输出**: 组织 → 父组织映射（可为空）

### 4. 实体识别（规则+AI）✅
- **位置**: `src/processors/entity_recognizer.py`
- **功能**: 
  - 从文本中识别组织实体
  - 推断组织所属部门
  - 基于规则的父组织识别（已被AI方法替代）

### 5. 关系映射 ✅
- **位置**: `src/processors/relationship_mapper.py`
- **功能**:
  - 分配组织唯一ID（O001, O002...）
  - 映射人员到组织关系
  - 映射组织父级关系
  - 验证引用完整性

## 完整处理流程

```
Phase 1: 数据加载
  ↓
Phase 2: AI 增强（包含组织提取）
  ├─ Step 2.1: 提取基本信息（生日、性别）
  ├─ Step 2.2: 提取教育背景
  ├─ Step 2.3: 提取职业历史
  ├─ Step 2.4: 生成英文简介
  └─ Step 2.5: 提取当前组织 ✅ (从 Wikipedia)
  ↓
Phase 3: 标准化与关系建立
  ├─ Step 3.0: 从AI数据中提取组织
  ├─ Step 3.0.3: 组织去重 ✅ **新增**
  │   └─ AI 识别重复 → 生成标准名称映射
  ├─ Step 3.0.5: 分析组织层级 ✅
  │   └─ AI 确定父组织关系
  ├─ Step 3.1: 分配唯一ID
  ├─ Step 3.2: 映射关系
  └─ Step 3.3: 验证引用
  ↓
Phase 4: 导出CSV
```

## 数据流示例

### 输入（原始CSV）
```
姓名: Marco Rubio
职位: Secretary of State
所属组织: 美国国务院
```

### Wikipedia 数据
```
"Marco Rubio serves as United States Secretary of State since 2025.
The Department of State is responsible for foreign policy..."
```

### AI 提取组织
```
organization: "U.S. Department of State"
```

### 多人数据示例
```
Person A: "Department of State"
Person B: "U.S. Department of State"
Person C: "State Department"
```

### 去重后
```
所有人的组织 → "U.S. Department of State" (标准名称)
```

### 层级分析
```
U.S. Department of State → U.S. Federal Government
```

### 最终输出
```csv
id,name,organization,organizationParent
O001,U.S. Department of State,GOVT_001,U.S. Federal Government
P001,Marco Rubio,O001,...
```

## 关键改进点

### ✅ 改进1：从Wikipedia提取组织（非CSV）
- **之前**: 使用CSV中的"所属组织"字段（可能不准确）
- **现在**: 从Wikipedia文本中AI提取当前组织
- **好处**: 数据更权威、更及时

### ✅ 改进2：AI驱动的组织去重（新增）
- **之前**: 仅基于精确字符串匹配去重
- **现在**: AI识别同义表述并合并
- **好处**: 大幅减少重复组织，提高数据质量

### ✅ 改进3：AI驱动的层级分析
- **之前**: 基于硬编码规则（有限覆盖）
- **现在**: AI基于上下文理解确定层级
- **好处**: 更灵活、覆盖更广、允许无父级

## 测试覆盖

### 单元测试
1. `test_api_connection.py` - API连接测试
2. `test_organization_extraction.py` - 组织提取测试
3. `test_organization_deduplication.py` - 去重功能测试 ✅ **新增**
4. `test_full_organization_flow.py` - 完整流程测试 ✅ **新增**

### 测试结果示例

**去重测试结果**:
- 输入: 12个组织（包含重复）
- 输出: 5个唯一组织
- 合并: 7个重复项
- 准确率: 100%（所有重复正确识别）

**完整流程测试结果**:
- 4个人员数据
- 提取4个组织
- 去重后3个组织（合并1个重复）
- 3个组织全部成功分析出父级关系

## 性能指标

| 步骤 | API调用次数 | 平均耗时 |
|------|------------|---------|
| 组织提取 | 每人1次 | ~2-3秒/人 |
| 去重分析 | 每批1次 | ~5-10秒/批 |
| 层级分析 | 每组织1次 | ~2-3秒/组织 |

**优化措施**:
- ✅ 分字段缓存（`{name}_{field}` 格式）
- ✅ Rate limiting（50 req/min）
- ✅ 批处理（10人/批）

## 配置文件

### 必需配置 (`config/.env`)
```env
ANTHROPIC_API_KEY=your_api_key
ANTHROPIC_BASE_URL=https://api.deepseek.com
MAX_CLAUDE_REQUESTS_PER_MINUTE=50
BATCH_SIZE=10
```

### 缓存文件
- `data/intermediate/ai_responses.json` - AI增强缓存
- `data/intermediate/organization_dedup_cache.json` - 去重缓存 ✅ **新增**
- `data/intermediate/organization_hierarchy_cache.json` - 层级缓存

## 核心文件清单

### 处理器模块
1. `src/processors/ai_enhancer.py` - AI增强（含组织提取）
2. `src/processors/organization_deduplicator.py` - 组织去重 ✅ **新增**
3. `src/processors/organization_hierarchy.py` - 层级分析
4. `src/processors/entity_recognizer.py` - 实体识别
5. `src/processors/relationship_mapper.py` - 关系映射

### 测试脚本
1. `test_organization_extraction.py` - 提取测试
2. `test_organization_deduplication.py` - 去重测试 ✅ **新增**
3. `test_full_organization_flow.py` - 流程测试 ✅ **新增**

### 文档
1. `ORGANIZATION_DEDUPLICATION.md` - 去重功能详细说明 ✅ **新增**
2. `ORGANIZATION_FEATURES_SUMMARY.md` - 本文档 ✅ **新增**

## 使用示例

### 运行完整流程
```bash
python -m src.main
```

### 测试去重功能
```bash
python test_organization_deduplication.py
```

### 测试完整组织流程
```bash
python test_full_organization_flow.py
```

## 质量保证

### 数据质量提升
1. ✅ 组织数据来源权威（Wikipedia）
2. ✅ 自动去重减少冗余
3. ✅ 层级关系更准确
4. ✅ 允许无父级（灵活性）

### 可追溯性
1. ✅ 每个组织标注来源（Wikipedia URL）
2. ✅ 去重映射记录在缓存中
3. ✅ 层级分析理由记录在日志中
4. ✅ 所有AI决策可审查

## 下一步改进建议

### 短期改进
1. 为去重决策添加置信度评分
2. 支持手动定义组织别名映射
3. 增加组织数据验证规则

### 长期改进
1. 支持多语言组织名称
2. 集成更多数据源（LinkedIn、官网等）
3. 组织变更历史追踪
4. 组织关系可视化

## 总结

当前系统实现了完整的组织处理流程：

✅ **提取**: 从权威来源（Wikipedia）提取组织信息
✅ **去重**: AI智能识别并合并重复组织
✅ **层级**: AI分析组织父子关系
✅ **映射**: 建立人员-组织-层级完整关系网
✅ **验证**: 确保数据完整性和一致性

通过这些功能，系统能够生成高质量、结构化的组织数据，为后续分析提供可靠基础。
