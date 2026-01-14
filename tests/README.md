# 测试文件说明

本目录包含项目的所有测试文件。

## 测试文件列表

### API连接测试
- `test_api_connection.py` - 测试API连接状态
- `test_api_key.py` - 测试API密钥有效性
- `test_openai_compatible_api.py` - 测试OpenAI兼容API

### AI增强测试
- `test_ai_enhancer_api.py` - 测试AI增强器API调用

### Wikipedia相关测试
- `test_wikipedia_api.py` - 测试Wikipedia API基本功能
- `test_wikipedia_api_direct.py` - 测试Wikipedia直接API调用
- `test_wikipedia_chunking.py` - 测试Wikipedia文本分块
- `test_fixed_wikipedia.py` - 测试修复后的Wikipedia功能

### 组织相关测试
- `test_organization_extraction.py` - 测试组织信息提取
- `test_organization_deduplication.py` - 测试组织去重功能

### 完整流程测试
- `test_full_organization_flow.py` - 测试完整的组织处理流程
- `test_new_person_full_text.py` - 测试新人物的完整文本处理

### 其他测试
- `test_sample.py` - 示例测试文件

## 运行测试

### 运行单个测试文件
```bash
python tests/test_api_connection.py
```

### 运行所有测试（如果使用pytest）
```bash
pytest tests/
```

### 运行特定模块的测试
```bash
python tests/test_wikipedia_api.py
```

## 注意事项

1. 运行测试前确保已配置好 `config/.env` 文件
2. 某些测试需要有效的API密钥才能运行
3. 网络相关的测试需要稳定的网络连接
4. 部分测试可能会消耗API配额，请谨慎运行
