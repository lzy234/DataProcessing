# AI增强阶段Wikipedia文本处理分析

## 执行摘要

经过分析，发现AI增强阶段对Wikipedia长文本的处理**存在严重问题**，导致大量有价值信息被忽略。

---

## 核心问题

### 1. Chunking覆盖率极低（最严重的问题）

**现状：**
- Trump的Wikipedia文本：198,387字符
- 生成的chunks总长度：43,791字符
- **覆盖率仅22.1%** - 78%的文本被丢弃！

**根本原因：**
在 [text_chunker.py](src/processors/text_chunker.py#L112-L146) 的 `_parse_sections()` 方法中：
```python
section_pattern = r'\n==\s*([^=]+)\s*==\n'
```

这个正则表达式**只能识别二级标题**（`== Title ==`），但Wikipedia文章包含：
- 二级标题 `== Section ==`
- 三级标题 `=== Subsection ===`
- 四级标题 `==== Details ====`

**实际效果：**
```
Trump文章结构：
├── Introduction (9,351 chars) ✓ 被chunker识别
├── == Early life == (可能被识别)
│   ├── === Family background === ✗ 被忽略
│   └── === Education === ✗ 被忽略
├── == Business career == (可能被识别)
│   ├── === Real estate === ✗ 被忽略
│   ├── === The Apprentice === ✗ 被忽略
│   └── === Financial issues === ✗ 被忽略
└── == Presidency == (可能被识别)
    ├── === First term === ✗ 被忽略
    └── === Second term === ✗ 被忽略
```

因此，chunker只能识别5个顶层section，导致覆盖率只有22%。

---

### 2. AI增强阶段的字符限制过于严格

**当前设置** ([ai_enhancer.py:159-205](src/processors/ai_enhancer.py#L159-L205))：

| 处理阶段 | 最大字符数 | 占Trump文本的比例 |
|---------|-----------|------------------|
| 基础信息 | 800 | 0.4% |
| 教育背景 | 3,000 | 1.5% |
| 职业历史 | 3,500 | 1.8% |
| 传记 | 4,000 | 2.0% |
| 组织机构 | 2,000 | 1.0% |

**问题分析：**
1. **固定字符限制不合理**：
   - 对于短文本（1,552字符）：4,000字符足够
   - 对于长文本（198,387字符）：4,000字符只能覆盖2%

2. **即使chunks覆盖率提高到100%，这些限制仍然会丢失信息**：
   - Education阶段：最多使用3,000字符
   - 如果Education相关内容超过3,000字符，多余部分会被截断

---

### 3. Chunk优先级算法的局限性

**当前算法** ([text_chunker.py:223-259](src/processors/text_chunker.py#L223-L259))：

```python
def prioritize_chunks(self, chunks: List[Dict], max_chunks: int = 5) -> List[Dict]:
    # 只返回前5个chunks
```

**评分机制：**
- Introduction（intro）: +100分
- 关键词匹配: 每个+5-10分
- 日期出现: 每个+2分

**问题：**
- 固定返回5个chunks（`max_chunks=5`）
- 对于有50个section的文章，90%的内容被丢弃
- 评分机制没有考虑section的重要性层级

---

## 数据统计

### Wikipedia文本长度分布

```
总人数: 99人
平均长度: 29,835字符
中位数长度: 22,662字符
最小长度: 1,552字符
最大长度: 198,387字符

前10名最长文本：
1. Donald J. Trump: 198,387字符 (5 chunks, 22.1%覆盖)
2. Glenn Youngkin: 104,143字符 (5 chunks, 29.7%覆盖)
3. Brett Kavanaugh: 90,617字符 (5 chunks)
4. Chuck Grassley: 89,117字符 (5 chunks, 66.6%覆盖)
```

**覆盖率统计：**
- 平均覆盖率：66.3%
- 中位数覆盖率：70.0%
- 最低覆盖率：11.6%
- 最高覆盖率：100.0%

**问题：有33.7%的信息在chunking阶段就已经丢失！**

---

## 根本原因总结

### Wikipedia HTML解析问题

在 [wikipedia_extractor.py:234-286](src/extractors/wikipedia_extractor.py#L234-L286) 的HTML解析器中：

```python
class HTMLToText(HTMLParser):
    def handle_starttag(self, tag, attrs):
        # 只标记了 h2 和 h3
        if tag == 'h2':
            self.text.append('\n\n== ')
        elif tag == 'h3':
            self.text.append('\n\n=== ')
```

**问题：**
1. **h3标签被标记了，但chunker不识别`===`**
2. 没有标记h4、h5、h6标签
3. Wikipedia的复杂层级结构被扁平化

**结果：**
- 解析出的plain text中，三级标题虽然有`=== Title ===`标记
- 但text_chunker只识别`== Title ==`
- 导致大量section被合并成一个大chunk，然后被truncate

---

## 影响评估

### 对数据质量的影响

1. **教育信息提取**：
   - 如果教育信息在第6-10个chunk中 → 完全丢失
   - 如果在前5个chunk中但超过3,000字符 → 部分丢失

2. **职业历史提取**：
   - 对于政治人物，职业历史往往很长
   - 3,500字符可能只能覆盖早期career
   - 近期重要职位可能被遗漏

3. **传记生成**：
   - 4,000字符限制对于复杂人物严重不足
   - AI被迫基于不完整信息生成传记
   - 可能遗漏关键成就和争议

### 具体案例：Donald Trump

```
总文本: 198,387字符
可用chunks: 43,791字符 (22%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Biography阶段实际使用: 4,000字符 (2%)

丢失的可能重要内容：
- Business career细节
- Presidency详细政策
- Controversies完整描述
- Legal issues全面记录
- 2024 campaign信息
```

---

## 是否合理？

### ❌ 不合理的方面

1. **Chunking覆盖率22%不合理**
   - 技术问题，不是设计决策
   - 应该修复section识别逻辑

2. **固定字符限制不合理**
   - 应该采用自适应限制
   - 或者至少针对长文本增加限制

3. **固定5个chunks不合理**
   - 应该基于总长度动态调整
   - 或者使用更智能的chunk selection

### ✅ 部分合理的方面

1. **使用chunking策略本身是合理的**
   - 不能把200K字符全部送给AI
   - 需要优先级和筛选机制

2. **分阶段处理是合理的**
   - 5个独立的AI调用针对不同字段
   - 可以针对性地选择相关文本

3. **关键词优先级是合理的**
   - 但需要更好的实现

---

## 建议改进方案

### 短期修复（高优先级）

1. **修复section识别**
   ```python
   # 在 text_chunker.py 中
   section_pattern = r'\n(==+)\s*([^=]+)\s*\1\n'  # 识别所有级别
   ```

2. **增加chunk数量**
   ```python
   # 在 wikipedia_extractor.py 中
   prioritized_chunks = self.chunker.prioritize_chunks(
       chunks,
       max_chunks=10  # 从5增加到10
   )
   ```

3. **增加字符限制**
   ```python
   # 在 ai_enhancer.py 中
   wiki_extract = self._get_relevant_text(
       wiki,
       keywords=['career', ...],
       max_chars=8000  # 从3500增加到8000
   )
   ```

### 中期改进

1. **自适应字符限制**
   ```python
   def _get_adaptive_limit(self, extract_length: int, base_limit: int) -> int:
       """根据文本长度调整限制"""
       if extract_length > 100000:
           return base_limit * 3
       elif extract_length > 50000:
           return base_limit * 2
       return base_limit
   ```

2. **改进chunk优先级算法**
   - 使用section层级信息
   - 考虑section在文章中的位置
   - 为不同处理阶段选择不同的chunks

### 长期优化

1. **使用语义搜索**
   - 对chunks进行embedding
   - 基于query选择最相关的chunks
   - 而不是简单的关键词匹配

2. **分段summarization**
   - 对超长section先做summarization
   - 再传给AI增强阶段

3. **RAG-style检索**
   - 让AI能够"检索"额外信息
   - 而不是一次性传入所有上下文

---

## 结论

**当前的Wikipedia文本处理方式存在严重问题，不合理。**

主要问题：
1. ❌ Chunking只覆盖22%的文本（技术bug）
2. ❌ 字符限制对长文本过于严格
3. ❌ 固定5个chunks无法适应不同长度

**建议立即修复section识别bug，并增加字符限制和chunk数量。**

当前配置下，对于长文本（>100K字符）的人物，AI增强阶段只能看到不到5%的完整信息，严重影响数据质量。
