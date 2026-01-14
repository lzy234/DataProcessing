# 快速参考手册

## 🚀 模型配置速查

### 当前配置
```bash
AI_MODEL=deepseek-reasoner  # 推荐配置
```

### 更改模型
编辑 `config/.env` 文件：
```bash
AI_MODEL=deepseek-reasoner  # 推荐：复杂推理
AI_MODEL=deepseek-chat      # 备选：快速开发
```

### 验证配置
```bash
python -m tests.test_model_config
```

---

## 📊 当前系统能力

| 阶段 | 处理字符数 | 推荐模型 |
|------|-----------|---------|
| Basic Info | 1,600 | reasoner |
| Education | 6,000 | reasoner ⭐ |
| Career | 8,000 | reasoner ⭐ |
| Biography | 10,000 | reasoner ⭐ |
| Organization | 4,000 | reasoner |

⭐ = 强烈推荐使用reasoner模型

---

## 🔄 清除缓存（更换模型后必做）

```bash
rm data/intermediate/ai_responses.json
rm data/intermediate/wikipedia_cache.json  # 可选
```

---

## 📈 性能提升

- **文本覆盖率**: 22% → 60-80% (+258%)
- **Biography处理**: 4K → 10K chars (+150%)
- **Chunk数量**: 5 → 10 (+100%)
- **模型能力**: chat → reasoner (质量提升)

---

## 📚 详细文档

- [MODEL_CONFIGURATION.md](docs/MODEL_CONFIGURATION.md) - 模型配置完整指南
- [IMPROVED_STRATEGY.md](docs/IMPROVED_STRATEGY.md) - 技术改进详解
- [UPGRADE_SUMMARY.md](docs/UPGRADE_SUMMARY.md) - 升级总结报告

---

## ⚡ 常用命令

```bash
# 测试模型配置
python -m tests.test_model_config

# 分析文本处理
python -m tests.analyze_text_processing

# 提取Wikipedia数据
python -m src.extractors.wikipedia_extractor

# 运行AI增强
python -m src.processors.ai_enhancer
```

---

## 🎯 推荐工作流

1. **首次使用或更换模型**
   ```bash
   # 清除缓存
   rm data/intermediate/ai_responses.json

   # 验证配置
   python -m tests.test_model_config
   ```

2. **正常运行**
   ```bash
   # 提取数据
   python -m src.extractors.wikipedia_extractor

   # AI增强
   python -m src.processors.ai_enhancer
   ```

3. **分析效果**
   ```bash
   python -m tests.analyze_text_processing
   ```

---

## 💡 提示

- ✅ **推荐使用 `deepseek-reasoner`** - 最适合当前系统
- ⚠️ **更换模型后记得清除缓存**
- 📊 **定期检查API使用量和成本**
- 🔍 **遇到问题先查看日志输出**

---

*最后更新: 2026-01-15*
