# AI模型配置指南

## 概述

系统现在支持通过环境变量配置不同的AI模型。这允许你根据需求选择最适合的模型。

---

## 配置方法

### 1. 编辑 `.env` 文件

在 `config/.env` 文件中设置 `AI_MODEL` 环境变量：

```bash
# config/.env
AI_MODEL=deepseek-reasoner
```

### 2. 重启应用程序

修改 `.env` 后，重新运行你的脚本以使新配置生效。

---

## 推荐模型

### 🚀 推荐：Deepseek Reasoner

```bash
AI_MODEL=deepseek-reasoner
```

**优势：**
- 🧠 **更强的推理能力**：专门优化用于复杂推理任务
- 📊 **更好的数据提取**：在结构化信息提取方面表现出色
- 💡 **理解复杂上下文**：能更好地处理长文本和复杂的Wikipedia文章
- 💰 **性价比高**：与高级模型相比成本更低

**适用场景：**
- 提取复杂的教育背景、职业历史
- 生成准确的传记摘要
- 从长文本中提取关键信息

---

## 其他可用模型

### Deepseek Chat

```bash
AI_MODEL=deepseek-chat
```

**特点：**
- 通用聊天模型
- 速度较快
- 适合简单的提取任务

**适用场景：**
- 快速原型开发
- 简单的数据提取任务

### Claude 3.5 Sonnet (如果使用Anthropic API)

```bash
ANTHROPIC_BASE_URL=https://api.anthropic.com
AI_MODEL=claude-3-5-sonnet-20241022
```

**特点：**
- Anthropic最新的高性能模型
- 卓越的文本理解和生成能力
- 支持大上下文窗口（200K tokens）

**注意：** 需要直接使用Anthropic API密钥

### Claude 3 Opus (如果使用Anthropic API)

```bash
AI_MODEL=claude-3-opus-20240229
```

**特点：**
- Anthropic最强大的模型
- 最高的准确性
- 成本最高

---

## 当前系统优化

基于我们刚完成的改进，现在系统可以处理更多上下文：

| 处理阶段 | 上下文长度 | 推荐模型 |
|---------|-----------|---------|
| **Basic Info** | 1,600字符 | deepseek-chat或reasoner |
| **Education** | 6,000字符 | deepseek-reasoner ⭐ |
| **Career History** | 8,000字符 | deepseek-reasoner ⭐ |
| **Biography** | 10,000字符 | deepseek-reasoner ⭐ |
| **Organization** | 4,000字符 | deepseek-chat或reasoner |

### 为什么推荐Deepseek Reasoner？

对于我们的数据提取任务，**deepseek-reasoner** 特别合适，因为：

1. **处理长文本能力强**
   - 现在Biography阶段需要处理10,000字符
   - Reasoner能更好地理解和总结长文本

2. **结构化提取准确**
   - 需要从非结构化文本中提取结构化信息
   - Reasoner在这方面表现优秀

3. **理解复杂关系**
   - 职业历史涉及时间线、职位变化
   - Reasoner能更好地理解这些关系

4. **成本效益好**
   - 每次API调用处理的字符数增加了100-150%
   - 使用高推理能力的模型保证质量

---

## 配置示例

### 场景1：使用Deepseek Reasoner（推荐）

```bash
# config/.env
ANTHROPIC_API_KEY=sk-xxxxx  # 你的Deepseek API密钥
ANTHROPIC_BASE_URL=https://api.deepseek.com  # Deepseek API端点
AI_MODEL=deepseek-reasoner

MAX_CLAUDE_REQUESTS_PER_MINUTE=50
```

### 场景2：使用Deepseek Chat（快速开发）

```bash
# config/.env
ANTHROPIC_API_KEY=sk-xxxxx
ANTHROPIC_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-chat

MAX_CLAUDE_REQUESTS_PER_MINUTE=100  # Chat模型可以更快
```

### 场景3：使用Claude 3.5 Sonnet

```bash
# config/.env
ANTHROPIC_API_KEY=sk-ant-xxxxx  # Anthropic API密钥
ANTHROPIC_BASE_URL=https://api.anthropic.com
AI_MODEL=claude-3-5-sonnet-20241022

MAX_CLAUDE_REQUESTS_PER_MINUTE=50
```

---

## 验证配置

运行以下命令验证模型配置：

```bash
python -c "from src.config.settings import Settings; print(f'Current Model: {Settings.AI_MODEL}')"
```

或者运行测试：

```bash
python -m src.processors.ai_enhancer
```

查看日志输出：
```
INFO - Initialized ClaudeAIEnhancer with model deepseek-reasoner
INFO - Using API endpoint: https://api.deepseek.com
```

---

## 性能对比（预估）

基于我们的改进后的系统：

| 模型 | 准确性 | 速度 | 成本 | 推荐场景 |
|------|--------|------|------|---------|
| **deepseek-reasoner** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **生产环境** ✅ |
| deepseek-chat | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 快速开发 |
| claude-3-5-sonnet | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 高质量需求 |
| claude-3-opus | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 最高质量 |

---

## 常见问题

### Q1: 更换模型后需要清除缓存吗？

**是的！** 如果你更换了模型，建议清除AI响应缓存：

```bash
rm data/intermediate/ai_responses.json
```

这样可以确保使用新模型重新生成所有响应。

### Q2: 为什么推荐deepseek-reasoner而不是deepseek-chat？

**主要原因：**
1. 我们刚刚将处理的文本量增加了100-150%
2. 更长的上下文需要更强的推理能力
3. reasoner在复杂信息提取方面表现更好
4. 成本差异不大，但质量提升明显

### Q3: 可以在不同阶段使用不同模型吗？

**目前不支持。** 但这是一个很好的优化方向：
- Basic Info可以用chat模型（简单提取）
- Biography可以用reasoner模型（需要推理和总结）

可以在未来版本中实现这个功能。

### Q4: 如何监控API成本？

**建议：**
1. 查看API提供商的使用dashboard
2. 设置合理的 `MAX_CLAUDE_REQUESTS_PER_MINUTE`
3. 使用缓存减少重复调用
4. 监控日志中的请求数量

---

## 总结

**当前推荐配置：**

```bash
AI_MODEL=deepseek-reasoner
```

这个配置在质量、速度和成本之间达到了最佳平衡，特别适合我们改进后的系统（10,000字符的Biography上下文）。

如需更改，只需修改 `config/.env` 文件中的 `AI_MODEL` 参数即可。
