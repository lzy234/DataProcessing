# AI增强阶段改进策略：分层文本处理

## 核心理念

**不同类型的数据需要不同的文本量：**
- ✅ **基础数据**（gender, dateOfBirth）：只需要少量精准文本（intro部分）
- ✅ **结构化数据**（education, organization）：需要中等量的相关文本（关键sections）
- ✅ **综合叙述**（biography, careerHistory）：需要大量全面的文本（多个sections）

---

## 当前实现的合理性重新评估

### ✅ 合理的设计部分

1. **分阶段处理策略**
   ```python
   # ai_enhancer.py 的5个独立阶段
   - Stage 1: Basic Info (800 chars)
   - Stage 2: Education (3,000 chars)
   - Stage 3: Career History (3,500 chars)
   - Stage 4: Biography (4,000 chars)
   - Stage 5: Organization (2,000 chars)
   ```
   **✅ 这个设计是合理的**：每个阶段可以针对性地选择相关文本

2. **关键词优先级机制**
   ```python
   # _get_relevant_text() 支持关键词过滤
   wiki_extract = self._get_relevant_text(
       wiki,
       keywords=['education', 'university', ...],
       max_chars=3000
   )
   ```
   **✅ 这个思路是正确的**：用关键词筛选相关chunks

3. **intro chunks获得高优先级**
   ```python
   # text_chunker.py:276
   if chunk['is_intro']:
       score += 100
   ```
   **✅ 对于基础信息提取很合理**：gender、birth date通常在intro

### ❌ 需要改进的部分

1. **Chunking覆盖率低（技术bug）**
   - 只识别二级标题，忽略三级及以下
   - 导致22%覆盖率
   - **这是bug，不是设计问题**

2. **Biography阶段字符限制过低**
   - 当前：4,000字符固定
   - 问题：对长文本（>100K）不够用
   - **需要针对性增加**

3. **没有区分"精准提取"和"综合总结"的策略**
   - 所有阶段都用相同的chunk selection逻辑
   - **需要分层策略**

---

## 改进方案：分层文本处理策略

### 策略1: 精准提取（基础数据）

**适用于：**
- Gender
- Date of Birth
- Organization（当前职位）

**原则：**
- ✅ 少量文本（500-1000字符）
- ✅ 高精度：优先intro和infobox
- ✅ 明确来源：只提取明确提到的信息

**当前实现评估：**
```python
# Basic Info: 800 chars from intro
# Organization: 2,000 chars with keywords
```
**✅ 基本合理**，但可以优化：

```python
def _enhance_basic_info(self, person: Dict, wiki: Dict) -> Dict:
    # 策略：只使用intro chunks（最相关）
    wiki_extract = self._get_relevant_text(
        wiki,
        keywords=[],  # 不需要关键词，直接用intro
        max_chars=1000,  # 1000字符足够
        prefer_intro_only=True  # 新参数：只用intro
    )
```

### 策略2: 结构化提取（教育、早期经历）

**适用于：**
- Education
- Early Career

**原则：**
- ✅ 中等文本（3,000-6,000字符）
- ✅ 相关性优先：用关键词筛选相关sections
- ✅ 结构化输出：提取特定字段

**当前实现评估：**
```python
# Education: 3,000 chars with keywords
```
**✅ 基本合理**，但对于有详细教育背景的人物可能不够：

**改进建议：**
```python
def _enhance_education(self, person: Dict, wiki: Dict) -> Dict:
    # 策略：优先Education section，补充Early Life
    wiki_extract = self._get_relevant_text(
        wiki,
        keywords=['education', 'university', 'college', 'graduated', 'degree', 'studied'],
        max_chars=5000,  # 从3000增加到5000
        prioritize_sections=['Education', 'Early life', 'Background']  # 新参数
    )
```

### 策略3: 综合总结（传记、职业历史）

**适用于：**
- Biography（200-500词的综合传记）
- Career History（时间线总结）

**原则：**
- ✅ 大量文本（10,000-30,000字符）
- ✅ 全面覆盖：需要多个sections的信息
- ✅ 综合能力：AI需要总结提炼

**当前实现评估：**
```python
# Biography: 4,000 chars
# Career History: 3,500 chars
```
**❌ 严重不足**，特别是对于复杂人物：

**改进建议：**
```python
def _enhance_biography(self, person: Dict, wiki: Dict) -> Dict:
    # 策略：提供尽可能多的上下文
    extract_length = len(wiki.get('extract', ''))

    # 自适应限制：根据文本长度调整
    if extract_length > 100000:
        max_chars = 30000  # 长文本：30K字符
    elif extract_length > 50000:
        max_chars = 20000  # 中等文本：20K字符
    elif extract_length > 20000:
        max_chars = 10000  # 一般文本：10K字符
    else:
        max_chars = 5000   # 短文本：5K字符

    wiki_extract = self._get_relevant_text(
        wiki,
        keywords=['born', 'early life', 'career', 'education', 'political', 'achievement'],
        max_chars=max_chars,  # 自适应限制
        diverse_sections=True  # 新参数：尽量覆盖多个不同sections
    )
```

---

## 具体改进实施计划

### 改进1: 增强 `_get_relevant_text()` 方法

**当前问题：**
- 只是简单按分数排序chunks
- 没有针对不同需求的策略

**改进方案：**

```python
def _get_relevant_text(
    self,
    wiki: Dict,
    keywords: List[str] = None,
    max_chars: int = 3000,
    prefer_intro_only: bool = False,      # 新：只用intro
    prioritize_sections: List[str] = None, # 新：优先特定sections
    diverse_sections: bool = False         # 新：多样化覆盖
) -> str:
    """
    Get relevant text from Wikipedia data with flexible strategies.

    Strategies:
    1. prefer_intro_only=True: 只返回intro chunks（用于基础信息）
    2. prioritize_sections: 优先选择特定section名（用于结构化提取）
    3. diverse_sections=True: 尽量从不同sections选取（用于综合总结）
    """
    if not wiki.get('chunks'):
        # Fallback to extract
        extract = wiki.get('extract', '')
        return extract[:max_chars] if len(extract) > max_chars else extract

    chunks = wiki['chunks']

    # Strategy 1: Intro only (for basic info)
    if prefer_intro_only:
        intro_chunks = [c for c in chunks if c.get('is_intro', False)]
        combined = self._combine_chunks(intro_chunks, max_chars)
        return combined

    # Strategy 2: Prioritize specific sections (for structured extraction)
    if prioritize_sections:
        scored_chunks = []
        for chunk in chunks:
            score = self._score_chunk_with_sections(
                chunk, keywords, prioritize_sections
            )
            scored_chunks.append((score, chunk))
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        sorted_chunks = [chunk for score, chunk in scored_chunks]
        return self._combine_chunks(sorted_chunks, max_chars)

    # Strategy 3: Diverse sections (for comprehensive bio)
    if diverse_sections:
        selected_chunks = self._select_diverse_chunks(chunks, keywords, max_chars)
        return self._combine_chunks(selected_chunks, max_chars)

    # Default: keyword-based scoring (current implementation)
    scored_chunks = []
    for chunk in chunks:
        score = chunk.get('is_intro', False) * 100
        text_lower = chunk['text'].lower()
        for keyword in (keywords or []):
            if keyword.lower() in text_lower:
                score += 10
        scored_chunks.append((score, chunk))

    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    sorted_chunks = [chunk for score, chunk in scored_chunks]
    return self._combine_chunks(sorted_chunks, max_chars)

def _select_diverse_chunks(
    self,
    chunks: List[Dict],
    keywords: List[str],
    max_chars: int
) -> List[Dict]:
    """
    Select chunks from diverse sections to get comprehensive coverage.

    策略：
    1. 确保intro被包含
    2. 从不同sections选择高分chunks
    3. 避免所有chunks来自同一个section
    """
    selected = []
    total_chars = 0
    seen_sections = set()

    # 1. Always include intro
    intro_chunks = [c for c in chunks if c.get('is_intro', False)]
    for chunk in intro_chunks:
        chunk_len = len(chunk['text'])
        if total_chars + chunk_len <= max_chars:
            selected.append(chunk)
            total_chars += chunk_len
            seen_sections.add('Introduction')

    # 2. Score remaining chunks
    other_chunks = [c for c in chunks if not c.get('is_intro', False)]
    scored_chunks = []
    for chunk in other_chunks:
        score = 0
        text_lower = chunk['text'].lower()

        # Keyword matching
        for keyword in (keywords or []):
            if keyword.lower() in text_lower:
                score += 10

        # Diversity bonus: prefer new sections
        section = chunk.get('section', '')
        if section not in seen_sections:
            score += 20  # Bonus for new section

        scored_chunks.append((score, chunk))

    # Sort by score
    scored_chunks.sort(reverse=True, key=lambda x: x[0])

    # 3. Add chunks greedily, preferring diverse sections
    for score, chunk in scored_chunks:
        chunk_len = len(chunk['text'])
        if total_chars + chunk_len <= max_chars:
            selected.append(chunk)
            total_chars += chunk_len
            seen_sections.add(chunk.get('section', ''))

    return selected

def _combine_chunks(self, chunks: List[Dict], max_chars: int) -> str:
    """Combine chunks into text, respecting max_chars limit."""
    combined = ""
    for chunk in chunks:
        chunk_text = chunk['text']
        section = chunk.get('section', '')

        if len(combined) + len(chunk_text) + 20 <= max_chars:
            if section and section != 'Introduction':
                combined += f"\n\n=== {section} ===\n{chunk_text}"
            else:
                combined += chunk_text if not combined else f"\n\n{chunk_text}"
        else:
            # Add partial chunk if space remains
            remaining = max_chars - len(combined)
            if remaining > 200:  # Only add if meaningful space
                combined += chunk_text[:remaining] + "..."
            break

    return combined.strip()

def _score_chunk_with_sections(
    self,
    chunk: Dict,
    keywords: List[str],
    prioritize_sections: List[str]
) -> float:
    """Score chunk with section name priority."""
    score = 0.0

    # Intro bonus
    if chunk.get('is_intro', False):
        score += 100

    # Section name priority
    section = chunk.get('section', '').lower()
    for priority_section in prioritize_sections:
        if priority_section.lower() in section:
            score += 50
            break

    # Keyword matching
    text_lower = chunk['text'].lower()
    for keyword in (keywords or []):
        if keyword.lower() in text_lower:
            score += 10

    return score
```

### 改进2: 更新各个enhance方法

**Basic Info - 保持简单**
```python
def _enhance_basic_info(self, person: Dict, wiki: Dict) -> Dict:
    wiki_extract = self._get_relevant_text(
        wiki,
        max_chars=1000,
        prefer_intro_only=True  # 只用intro
    )
```

**Education - 针对性选择**
```python
def _enhance_education(self, person: Dict, wiki: Dict) -> Dict:
    wiki_extract = self._get_relevant_text(
        wiki,
        keywords=['education', 'university', 'college', 'graduated', 'degree'],
        max_chars=6000,  # 增加到6000
        prioritize_sections=['Education', 'Early life']  # 指定sections
    )
```

**Career History - 适度增加**
```python
def _enhance_career_history(self, person: Dict, wiki: Dict) -> Dict:
    wiki_extract = self._get_relevant_text(
        wiki,
        keywords=['career', 'elected', 'appointed', 'served', 'position'],
        max_chars=8000,  # 增加到8000
        prioritize_sections=['Career', 'Political career', 'Presidency']
    )
```

**Biography - 大幅增加+自适应**
```python
def _enhance_biography(self, person: Dict, wiki: Dict) -> Dict:
    # 自适应计算max_chars
    extract_length = len(wiki.get('extract', ''))
    if extract_length > 100000:
        max_chars = 30000
    elif extract_length > 50000:
        max_chars = 20000
    else:
        max_chars = 10000

    wiki_extract = self._get_relevant_text(
        wiki,
        keywords=['born', 'early', 'career', 'education', 'political'],
        max_chars=max_chars,
        diverse_sections=True  # 多样化覆盖
    )
```

**Organization - 保持精准**
```python
def _extract_organization(self, person: Dict, wiki: Dict) -> Dict:
    wiki_extract = self._get_relevant_text(
        wiki,
        keywords=['current', 'serves', 'member'],
        max_chars=2000,
        prefer_intro_only=True  # 当前职位通常在intro
    )
```

---

## 改进3: 修复Chunking Bug（必须）

**问题：**
```python
# text_chunker.py:112
section_pattern = r'\n==\s*([^=]+)\s*==\n'  # 只匹配 ==Title==
```

**修复：**
```python
def _parse_sections(self, text: str) -> List[Dict]:
    """
    Parse Wikipedia text into hierarchical sections.

    Matches:
    == Level 2 ==
    === Level 3 ===
    ==== Level 4 ====
    """
    sections = []

    # Match all heading levels (2-4)
    section_pattern = r'\n(={2,4})\s*([^=]+)\s*\1\n'
    matches = list(re.finditer(section_pattern, text))

    if not matches:
        return [{
            'name': 'Introduction',
            'text': text.strip(),
            'is_intro': True,
            'level': 1
        }]

    # Extract intro
    first_match = matches[0]
    intro_text = text[:first_match.start()].strip()
    if intro_text:
        sections.append({
            'name': 'Introduction',
            'text': intro_text,
            'is_intro': True,
            'level': 1
        })

    # Extract all sections with hierarchy info
    for i, match in enumerate(matches):
        heading_markers = match.group(1)
        level = len(heading_markers)  # 2, 3, or 4
        section_name = match.group(2).strip()

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end].strip()

        if len(section_text) > 50:
            sections.append({
                'name': section_name,
                'text': section_text,
                'is_intro': False,
                'level': level
            })

    return sections
```

---

## 改进4: 增加max_chunks限制

**问题：**
```python
# wikipedia_extractor.py:117
prioritized_chunks = self.chunker.prioritize_chunks(chunks, max_chunks=5)
```

**改进：**
```python
# 根据文本长度自适应
total_length = len(wiki_data['extract'])
if total_length > 100000:
    max_chunks = 20
elif total_length > 50000:
    max_chunks = 15
elif total_length > 20000:
    max_chunks = 10
else:
    max_chunks = 5

prioritized_chunks = self.chunker.prioritize_chunks(chunks, max_chunks=max_chunks)
```

---

## 预期效果

### Trump案例对比

**当前状态：**
```
总文本: 198,387字符
可用chunks: 43,791字符 (22%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
各阶段使用：
- Basic Info: 800字符 (0.4%)
- Education: 3,000字符 (1.5%)
- Career: 3,500字符 (1.8%)
- Biography: 4,000字符 (2.0%)
- Organization: 2,000字符 (1.0%)
```

**改进后：**
```
总文本: 198,387字符
可用chunks: 150,000字符 (75%) ← 修复chunking bug后
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
各阶段使用：
- Basic Info: 1,000字符 (0.5%) ← intro only
- Education: 6,000字符 (3.0%) ← 针对性section
- Career: 8,000字符 (4.0%) ← 针对性section
- Biography: 30,000字符 (15.1%) ← 自适应+多样化
- Organization: 2,000字符 (1.0%) ← intro only

Biography阶段使用的文本增加7.5倍！
```

---

## 总结

### ✅ 你的观点完全正确

**"基础数据只需少量文本，综合传记需要大量文本"** - 这正是改进的核心原则。

### 当前实现的问题

1. ❌ **Chunking bug导致覆盖率只有22%**（必须修复）
2. ❌ **没有区分"精准提取"和"综合总结"的策略**
3. ❌ **Biography字符限制太低**（4K vs 需要20-30K）
4. ✅ 分阶段处理的思路是对的
5. ✅ 关键词优先级机制是合理的

### 改进优先级

**P0（立即修复）：**
1. 修复section识别bug（从22%提升到70%+覆盖率）
2. 增加Biography的max_chars到自适应（20-30K）

**P1（重要改进）：**
3. 实现分层文本处理策略（prefer_intro_only, diverse_sections等）
4. 增加max_chunks的自适应逻辑

**P2（优化）：**
5. 改进chunk优先级算法
6. 添加section层级信息

这样改进后，系统会更加合理和高效！
