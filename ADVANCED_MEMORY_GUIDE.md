# 🧠 Advanced Memory System - 使用指南

## 概览

你的多智能体系统现在集成了业界领先的开源Memory解决方案：

- **Mem0** - 长期语义记忆与向量搜索
- **Zep** - 会话记忆与自动摘要

## ✅ 已完成的集成

### 1. 核心模块
- ✅ `core/advanced_memory.py` - Mem0 + Zep 统一封装
- ✅ `requirements.txt` - 添加了 mem0ai, zep-python, qdrant-client
- ✅ `docker-compose.yml` - 一键启动 Zep + Qdrant + Postgres

### 2. 智能体更新
- ✅ **Signal Agent** - 使用新memory系统
- ✅ **Insight Agent** - 使用新memory系统
- ✅ **Venture Agent** - 使用新memory系统

### 3. 配置
- ✅ `.env` - 添加了 ZEP_API_URL, QDRANT_HOST, QDRANT_PORT
- ✅ `test_advanced_memory.py` - 完整测试套件

---

## 🚀 快速开始

### 第1步：启动Memory服务（5分钟）

```bash
# 启动 Zep + Qdrant + Postgres
docker-compose up -d

# 验证服务状态
docker-compose ps

# 应该看到3个服务都在运行：
# obsei-zep       Up
# obsei-postgres  Up
# obsei-qdrant    Up
```

### 第2步：安装依赖（2分钟）

```bash
# 安装新的Python包
pip install mem0ai zep-python qdrant-client

# 或者重新安装所有依赖
pip install -r requirements.txt
```

### 第3步：验证系统（1分钟）

```bash
# 运行测试脚本
python test_advanced_memory.py

# 应该看到：
# ✅ Zep is running and healthy
# ✅ Qdrant is running and healthy
# ✅ Memory managers initialized
# ✅ All tests passed
```

---

## 💬 使用示例

### 与Signal Agent对话

```python
from agents.signal_agent_chat import SignalAgentChat
import asyncio

async def main():
    agent = SignalAgentChat()

    # 第1轮对话
    response1 = await agent.process_user_request(
        user_message="帮我找最近的AI创业项目",
        user_id="user_claire",
        session_id="session_001"
    )
    print(response1["message"])

    # 第2轮对话（记得第1轮的内容）
    response2 = await agent.process_user_request(
        user_message="第一个项目的详情是什么？",  # ← 智能体记得"第一个项目"
        user_id="user_claire",
        session_id="session_001"
    )
    print(response2["message"])

    # 查看memory统计
    print(f"Session: {response2['session_id']}")
    print(f"Memory stats: {response2['memory_stats']}")

asyncio.run(main())
```

### 跨会话记忆

```python
# 会话1
response1 = await agent.process_user_request(
    user_message="我喜欢AI和Web3领域的项目",
    user_id="user_claire",
    session_id="session_morning"
)

# 会话2（几小时后）- 智能体还记得用户偏好
response2 = await agent.process_user_request(
    user_message="推荐一些项目给我",  # ← 自动使用"AI和Web3"偏好
    user_id="user_claire",
    session_id="session_afternoon"
)
```

---

## 🧠 Memory系统架构

### 三层记忆

```
用户消息
    ↓
┌─────────────────────────────────────┐
│ Immediate Context (即时上下文)      │
│ - Zep: 最近10条对话                 │
│ - 自动生成会话摘要                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Session Memory (会话记忆)           │
│ - Zep: 当前会话的所有对话           │
│ - 语义搜索历史消息                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Long-term Memory (长期记忆)         │
│ - Mem0: 重要信息永久存储            │
│ - 向量搜索用户偏好和洞察            │
└─────────────────────────────────────┘
    ↓
整合所有上下文 → Claude API
```

### 自动记忆管理

**自动保存到长期记忆的条件：**
- 重要性评分 > 0.7
- 包含关键词：重要、记住、偏好、喜欢等
- 对话长度 > 500字符

**示例：**
```python
# 这句话会自动保存到长期记忆
"记住，我总是偏好种子轮和A轮的AI创业公司"
# ↑ 包含"记住"、"偏好"关键词，重要性高

# 这句话只保存到会话记忆
"今天天气不错"
# ↑ 重要性低，不会进入长期记忆
```

---

## 🔧 高级配置

### 环境变量

在 `.env` 文件中配置：

```bash
# Zep服务地址
ZEP_API_URL=http://localhost:8000

# Qdrant向量数据库
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Claude模型（用于memory operations）
CLAUDE_MODEL=claude-sonnet-4-20250514
```

### Docker配置

编辑 `docker-compose.yml` 自定义：

```yaml
# 调整Postgres数据库
postgres:
  environment:
    - POSTGRES_PASSWORD=your_secure_password

# 调整Qdrant存储路径
qdrant:
  volumes:
    - /your/custom/path:/qdrant/storage
```

---

## 📊 监控和调试

### 查看服务日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 只看Zep日志
docker-compose logs -f zep

# 只看Qdrant日志
docker-compose logs -f qdrant
```

### 访问服务UI

- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **Zep Health**: http://localhost:8000/healthz

### 测试Memory系统

```bash
# 运行完整测试
python test_advanced_memory.py

# 测试单个智能体
python -c "
from agents.signal_agent_chat import SignalAgentChat
agent = SignalAgentChat()
print('Memory stats:', agent.memory.get_stats())
"
```

---

## 🎯 最佳实践

### 1. Session管理

```python
# 为每个用户生成唯一session_id
import uuid

session_id = f"user_{user_id}_{uuid.uuid4().hex[:8]}"

# 同一用户的不同对话任务使用不同session
session_id_morning = f"user_{user_id}_morning"
session_id_project_review = f"user_{user_id}_project_review_{project_id}"
```

### 2. 添加元数据

```python
# 添加有用的元数据帮助后续检索
response = await agent.process_user_request(
    user_message="分析这个项目",
    user_id="user_claire",
    session_id="session_001",
    # 自动附加元数据到memory
)
```

### 3. 清理会话

```python
from core.advanced_memory import get_advanced_memory_manager

memory = get_advanced_memory_manager("signal_agent")

# 清理旧会话
memory.clear_session("old_session_id")
```

---

## 🔄 与旧系统对比

| 功能 | 旧系统 | 新系统 (Mem0+Zep) |
|------|--------|-------------------|
| **对话历史** | 内存中10轮 | Zep持久化+自动摘要 |
| **长期记忆** | 手动管理 | Mem0自动向量化 |
| **语义搜索** | 关键词匹配 | 向量相似度搜索 |
| **会话摘要** | 无 | Zep自动生成 |
| **跨会话记忆** | 不支持 | Mem0用户级记忆 |
| **性能** | 需加载全部历史 | 智能检索相关上下文 |
| **成本** | 高（重复发送历史） | 低（只发送相关上下文） |

---

## 🆘 故障排除

### 问题1：Zep连接失败

```bash
# 检查Zep是否运行
curl http://localhost:8000/healthz

# 如果失败，重启服务
docker-compose restart zep

# 查看日志
docker-compose logs zep
```

### 问题2：Qdrant连接失败

```bash
# 检查Qdrant是否运行
curl http://localhost:6333/

# 重启Qdrant
docker-compose restart qdrant
```

### 问题3：Memory无法保存

```python
# 检查memory系统状态
from core.advanced_memory import get_advanced_memory_manager

memory = get_advanced_memory_manager("signal_agent")
stats = memory.get_stats()

print(f"Mem0 enabled: {stats['mem0_enabled']}")
print(f"Zep enabled: {stats['zep_enabled']}")
print(f"Zep status: {stats.get('zep_status')}")
```

**常见原因：**
- Docker服务未启动
- 端口被占用（8000, 6333, 5432）
- 依赖未安装（mem0ai, zep-python）

---

## 📚 进一步学习

### Mem0文档
- GitHub: https://github.com/mem0ai/mem0
- 文档: https://docs.mem0.ai

### Zep文档
- GitHub: https://github.com/getzep/zep
- 文档: https://docs.getzep.com

### Qdrant文档
- 官网: https://qdrant.tech
- 文档: https://qdrant.tech/documentation/

---

## ✅ 完成检查清单

设置完成后，确认：

- [ ] Docker服务运行正常（`docker-compose ps`）
- [ ] 依赖已安装（`pip list | grep -E "mem0|zep|qdrant"`）
- [ ] 测试通过（`python test_advanced_memory.py`）
- [ ] 智能体可以对话（测试任意chat agent）
- [ ] Memory正确保存（查看Qdrant dashboard）

---

## 🎉 总结

你现在拥有：

1. ✅ **生产级Memory系统** - Mem0 + Zep组合
2. ✅ **智能上下文检索** - 向量搜索+相关性评分
3. ✅ **自动会话摘要** - Zep智能压缩长对话
4. ✅ **跨会话记忆** - 用户偏好永久保存
5. ✅ **成本优化** - 只发送相关上下文给Claude

**保留的自定义开发：**
- ✅ 数据采集系统（10+数据源）
- ✅ 3层分类系统
- ✅ Supabase知识库
- ✅ 5个智能体逻辑
- ✅ Next.js Dashboard

**升级的Memory层：**
- 🔄 context_manager.py → Mem0
- 🔄 memory_store.py → Zep
- 🔄 minecontext_wrapper.py → Mem0+Zep组合

完美的混合架构！🚀
