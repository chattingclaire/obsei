# 🧠 Memory & Context Engineering - 完整实现

## 概览

你的多智能体系统配备了三个核心的记忆和上下文管理模块：

1. **GlobalContextManager** (`core/context_manager.py`) - 跨智能体共享上下文
2. **MemoryStore** (`core/memory_store.py`) - 智能体记忆系统
3. **MineContextManager** (`core/minecontext_wrapper.py`) - 高级上下文工程

---

## 1️⃣ GlobalContextManager - 跨智能体上下文共享

**文件**: `core/context_manager.py` (407行)

### 核心功能

```python
from core.context_manager import get_context_manager

# 获取全局上下文管理器
ctx = get_context_manager(max_size_mb=10)

# Data Agent 设置上下文
ctx.set(
    key="trending_repos",
    value=["project1", "project2", "project3"],
    agent_name="data_agent",
    ttl_seconds=3600  # 1小时后过期
)

# Classify Agent 读取上下文
repos = ctx.get("trending_repos")  # ["project1", "project2", "project3"]

# 跨智能体共享上下文
ctx.share_context(
    from_agent="data_agent",
    to_agent="signal_agent",
    keys=["trending_repos"]  # 可选：指定要共享的键
)
```

### 主要特性

| 特性 | 说明 |
|------|------|
| **命名空间隔离** | 每个智能体有独立的上下文空间 |
| **TTL过期管理** | 支持自定义过期时间 |
| **大小限制** | 最大10MB，自动淘汰旧条目 |
| **跨智能体共享** | 智能体间可共享特定上下文 |
| **线程安全** | 支持并发访问 |
| **持久化** | 可保存/加载到文件 |
| **统计信息** | 实时监控使用情况 |

### 核心方法

```python
# 设置上下文
ctx.set(key, value, agent_name, ttl_seconds=None, metadata=None)

# 获取上下文
ctx.get(key, agent_name=None)

# 获取所有上下文（可按智能体过滤）
ctx.get_all(agent_name=None)

# 删除上下文
ctx.delete(key, agent_name=None)

# 清空上下文
ctx.clear(agent_name=None)

# 跨智能体共享
ctx.share_context(from_agent, to_agent, keys=None)

# 获取统计信息
stats = ctx.get_stats()
# {
#   "total_entries": 15,
#   "total_size_bytes": 2048,
#   "utilization_percent": 0.2,
#   "agents": {"data_agent": 5, "classify_agent": 10}
# }

# 保存到文件
ctx.save_to_file("/path/to/context.json")

# 从文件加载
ctx.load_from_file("/path/to/context.json")
```

### 自动管理机制

1. **自动淘汰**：当超过大小限制时，自动删除最旧的条目
2. **过期清理**：定期检查并删除过期条目
3. **内存优化**：使用高效的数据结构减少内存占用

---

## 2️⃣ MemoryStore - 智能体记忆系统

**文件**: `core/memory_store.py` (484行)

### 核心架构

```
┌────────────────────────────────────┐
│  Short-term Memory (短期记忆)       │
│  - 最近100条                        │
│  - TTL: 24小时                      │
│  - 自动FIFO淘汰                     │
│  - 高重要性自动晋升到长期记忆        │
└────────────────────────────────────┘
              ↓ (重要性 ≥ 0.8 或访问 ≥ 3次)
┌────────────────────────────────────┐
│  Long-term Memory (长期记忆)        │
│  - 最多1000条                       │
│  - TTL: 30天                        │
│  - 按重要性淘汰                     │
│  - 可持久化到磁盘                   │
└────────────────────────────────────┘
```

### 使用示例

```python
from core.memory_store import get_memory_store

# 获取智能体的记忆存储
memory = get_memory_store(
    agent_name="signal_agent",
    short_term_max_items=100,
    long_term_max_items=1000,
    storage_path="./data/signal_agent_memory.json"
)

# 添加短期记忆
memory.add_short_term(
    content={
        "user_query": "找AI创业项目",
        "result_count": 5
    },
    importance=0.6,
    tags=["query", "ai", "startup"],
    metadata={"user_id": "user123"}
)

# 添加长期记忆（重要信息）
memory.add_long_term(
    content={
        "user_preference": "偏好AI和Web3领域",
        "interaction_count": 15
    },
    importance=0.9,
    tags=["preference", "user_profile"]
)

# 搜索记忆
results = memory.search(
    query="AI",
    tags=["startup"],
    min_importance=0.5,
    limit=10
)

# 获取最近记忆
recent = memory.get_recent(memory_type="all", limit=20)

# 整合记忆（晋升重要的短期记忆）
promoted = memory.consolidate()  # 返回晋升数量

# 清理过期记忆
cleaned = memory.cleanup_expired()  # 返回清理数量

# 保存到磁盘
memory.save()

# 获取统计信息
stats = memory.get_stats()
# {
#   "short_term_count": 45,
#   "long_term_count": 123,
#   "total_count": 168,
#   "short_term_utilization_percent": 45.0,
#   "long_term_utilization_percent": 12.3
# }
```

### 记忆条目结构

```python
@dataclass
class MemoryEntry:
    id: str                    # 唯一ID
    content: Any               # 记忆内容（任意类型）
    memory_type: str           # "short_term" | "long_term"
    agent_name: str            # 所属智能体
    timestamp: str             # ISO 8601时间戳
    importance: float          # 重要性评分 (0.0-1.0)
    access_count: int          # 访问次数
    last_accessed: str         # 最后访问时间
    tags: List[str]            # 标签列表
    metadata: Dict[str, Any]   # 元数据
```

### 智能特性

#### 1. 自动晋升机制

```python
# 短期记忆自动晋升到长期记忆的条件：
- 重要性 ≥ 0.8
- 访问次数 ≥ 3次
- 手动调用 consolidate()

# 示例：
memory.add_short_term(
    content="用户询问ProjectX详情3次",
    importance=0.9  # ← 自动晋升到长期记忆
)
```

#### 2. 智能淘汰策略

```python
# 长期记忆超出容量时：
# 按 (重要性, 访问次数) 排序，删除最不重要的10%

# 短期记忆超出容量时：
# FIFO（先进先出），最旧的自动删除
```

#### 3. 搜索和检索

```python
# 多维度搜索
results = memory.search(
    query="AI创业",           # 文本搜索
    tags=["startup", "ai"],  # 标签过滤
    memory_type="long_term", # 类型过滤
    min_importance=0.7,      # 重要性阈值
    limit=10                 # 结果数量
)

# 结果按 (重要性, 时间) 排序
```

### 使用场景

| 智能体 | 短期记忆 | 长期记忆 |
|--------|----------|----------|
| **Signal Agent** | 当前会话的用户请求 | 用户偏好、常用查询模式 |
| **Insight Agent** | 本次分析的中间结果 | 历史趋势、关键洞察 |
| **Venture Agent** | 当前评估的项目 | 投资决策规则、成功案例 |
| **Data Agent** | 本轮采集的临时数据 | 数据源状态、采集统计 |
| **Classify Agent** | 当前批次的分类结果 | 分类模式、常见类别 |

---

## 3️⃣ MineContextManager - 高级上下文工程

**文件**: `core/minecontext_wrapper.py` (已在之前展示)

### 三层上下文架构

```python
from core.minecontext_wrapper import MineContextManager

# 创建上下文管理器
mine_ctx = MineContextManager(
    agent_name="signal_agent",
    db_client=supabase_client
)

# 添加即时上下文（对话）
mine_ctx.add_context(
    content="用户问：帮我找AI项目",
    context_type="conversation",
    relevance_score=1.0
)

# 添加会话上下文（任务）
mine_ctx.add_context(
    content={"task": "查找AI创业项目", "results": [...]},
    context_type="session",
    relevance_score=0.8
)

# 添加长期上下文（知识）
mine_ctx.add_context(
    content={"user_id": "user123", "preferences": ["AI", "Web3"]},
    context_type="knowledge",
    relevance_score=0.9
)

# 智能检索相关上下文
relevant = mine_ctx.retrieve_relevant_context(
    query="AI创业项目推荐",
    max_contexts=5,
    context_types=["knowledge", "session"],
    min_relevance=0.5
)

# 将知识库结果添加到上下文
mine_ctx.add_knowledge_from_db([
    {"title": "ProjectX", "category": "AI", "stars": 2000},
    {"title": "AIFlow", "category": "AI", "stars": 1500}
])
```

### 三层对比

| 层级 | 容量 | 生命周期 | 持久化 | 用途 |
|------|------|----------|--------|------|
| **Immediate** | 20条 | 当前对话 | 否 | 即时对话历史 |
| **Session** | 无限制 | 当前会话 | 会话结束时 | 任务上下文、中间结果 |
| **Long-term** | 无限制 | 永久 | 是（Supabase） | 知识库、用户档案 |

### 相关性评分

```python
def retrieve_relevant_context(query, max_contexts=5):
    """
    智能检索最相关的上下文

    评分维度：
    1. 文本相似度（关键词匹配）
    2. 时间衰减（越新越相关）
    3. 访问频率（常用的更相关）
    4. 手动设置的relevance_score

    最终分数 = 文本相似度 × relevance_score × 时间因子
    """
    # 返回排序后的top-K结果
```

---

## 🔄 三个模块的协同工作

### 场景：用户多轮对话

```python
# 用户第1轮：帮我找AI项目
# ================================

# 1. Chat History (AgentChatInterface)
chat_interface.chat_history.append({
    "role": "user",
    "content": "帮我找AI项目"
})

# 2. Short-term Memory (MemoryStore)
memory.add_short_term(
    content="用户查询：AI项目",
    importance=0.6,
    tags=["query", "ai"]
)

# 3. Session Context (MineContext)
mine_ctx.add_context(
    content="查询任务：AI创业项目",
    context_type="session"
)

# 4. Global Context (ContextManager)
ctx.set(
    key="current_query",
    value="AI项目",
    agent_name="signal_agent",
    ttl_seconds=1800  # 30分钟
)

# ================================
# 用户第2轮：第一个项目的详情
# ================================

# 1. 检索相关上下文
relevant = mine_ctx.retrieve_relevant_context("第一个项目")
# 返回：第1轮对话中提到的项目列表

# 2. 检索记忆
memories = memory.search(query="AI项目", limit=5)
# 返回：之前查询过的AI项目

# 3. 获取全局上下文
current_query = ctx.get("current_query")
# 返回："AI项目"

# 4. 整合所有上下文发送给Claude
response = claude.messages.create(
    messages=[
        {"role": "user", "content": f"""
        [历史对话] {chat_history}
        [相关记忆] {memories}
        [当前任务] {current_query}
        [用户问题] 第一个项目的详情
        """}
    ]
)

# 5. 更新记忆和上下文
memory.add_short_term(
    content="用户询问ProjectX详情",
    importance=0.7,
    tags=["projectx", "detail"]
)
```

---

## 📊 完整的数据流

```
用户输入
   ↓
┌─────────────────────────────────────────┐
│ 1. AgentChatInterface                  │
│    - 管理对话历史（最近10轮）            │
│    - 调用其他记忆系统                    │
└─────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────┐
│ 2. MineContextManager                   │
│    - 检索相关上下文（三层）              │
│    - 相关性评分排序                      │
└─────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────┐
│ 3. MemoryStore                          │
│    - 搜索短期/长期记忆                   │
│    - 按重要性排序                        │
└─────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────┐
│ 4. GlobalContextManager                 │
│    - 获取跨智能体共享的上下文            │
│    - 检查TTL有效性                       │
└─────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────┐
│ 5. 整合所有上下文                        │
│    - 历史对话 + 记忆 + 上下文 + 知识库   │
│    - 格式化成Claude可理解的格式          │
└─────────────────────────────────────────┘
   ↓
Claude API (带KV缓存)
   ↓
智能体响应
   ↓
┌─────────────────────────────────────────┐
│ 6. 更新所有记忆系统                      │
│    - 保存对话历史                        │
│    - 添加新记忆                          │
│    - 更新上下文                          │
│    - 持久化到数据库                      │
└─────────────────────────────────────────┘
```

---

## 🎯 实际应用示例

### Signal Agent 使用记忆系统

```python
# agents/signal_agent_chat.py

class SignalAgentChat(AgentChatInterface):
    def __init__(self):
        super().__init__("signal_agent", system_prompt)

        # 初始化记忆系统
        self.memory = get_memory_store(
            "signal_agent",
            storage_path="./data/signal_agent_memory.json"
        )

        # 初始化MineContext
        self.mine_ctx = MineContextManager(
            "signal_agent",
            db_client=self.db
        )

        # 全局上下文
        self.global_ctx = get_context_manager()

    async def process_user_request(self, user_message: str):
        # 1. 搜索相关记忆
        relevant_memories = self.memory.search(
            query=user_message,
            min_importance=0.5,
            limit=5
        )

        # 2. 检索MineContext
        relevant_contexts = self.mine_ctx.retrieve_relevant_context(
            query=user_message,
            max_contexts=5
        )

        # 3. 获取全局上下文
        shared_context = self.global_ctx.get_all(agent_name="signal_agent")

        # 4. 查询知识库
        kb_results = self.query_knowledge_base(user_message)

        # 5. 整合所有上下文
        context = {
            "memories": relevant_memories,
            "mine_contexts": relevant_contexts,
            "shared_context": shared_context,
            "knowledge_base": kb_results
        }

        # 6. 发送给Claude
        response = self.chat(user_message, context=context)

        # 7. 保存新记忆
        self.memory.add_short_term(
            content={
                "query": user_message,
                "response": response["message"]
            },
            importance=0.7,
            tags=["user_interaction"]
        )

        # 8. 更新MineContext
        self.mine_ctx.add_context(
            content=response["message"],
            context_type="conversation"
        )

        return response
```

---

## 🔧 配置选项

### config/settings.yaml

```yaml
memory:
  short_term_max_items: 100
  long_term_max_items: 1000
  short_term_ttl_hours: 24
  long_term_ttl_days: 30

context:
  max_size_mb: 10
  storage_backend: memory  # memory | file | supabase

minecontext:
  immediate_max_items: 20
  enable_db_persistence: true
  relevance_threshold: 0.3
```

---

## 📈 监控和统计

### 获取所有系统的统计信息

```python
# 记忆系统统计
memory_stats = memory.get_stats()
print(f"短期记忆: {memory_stats['short_term_count']}/100")
print(f"长期记忆: {memory_stats['long_term_count']}/1000")

# 全局上下文统计
ctx_stats = ctx.get_stats()
print(f"总上下文条目: {ctx_stats['total_entries']}")
print(f"内存使用: {ctx_stats['utilization_percent']:.1f}%")

# MineContext统计
mine_stats = mine_ctx.get_statistics()
print(f"即时上下文: {mine_stats['immediate_count']}")
print(f"会话上下文: {mine_stats['session_count']}")
print(f"长期上下文: {mine_stats['long_term_count']}")
```

---

## ✅ 完整性检查清单

### Memory & Context Engineering 模块

- ✅ **GlobalContextManager** (407行)
  - ✅ 跨智能体上下文共享
  - ✅ TTL过期管理
  - ✅ 命名空间隔离
  - ✅ 自动淘汰机制
  - ✅ 线程安全
  - ✅ 文件持久化
  - ✅ 统计监控

- ✅ **MemoryStore** (484行)
  - ✅ 短期记忆（100条）
  - ✅ 长期记忆（1000条）
  - ✅ 重要性评分
  - ✅ 自动晋升机制
  - ✅ 智能搜索
  - ✅ 过期清理
  - ✅ 磁盘持久化
  - ✅ 统计监控

- ✅ **MineContextManager** (已实现)
  - ✅ 三层上下文架构
  - ✅ 相关性评分
  - ✅ 智能检索
  - ✅ 数据库持久化
  - ✅ 知识库集成

- ✅ **AgentChatInterface** (对话历史)
  - ✅ 多轮对话管理
  - ✅ 最近10轮历史
  - ✅ 数据库持久化
  - ✅ KV缓存优化

---

## 🎉 总结

你的系统拥有**完整的、生产级的记忆和上下文工程系统**：

### 四层记忆架构

1. **对话历史** (AgentChatInterface) - 最近10轮
2. **短期记忆** (MemoryStore) - 24小时内的100条
3. **长期记忆** (MemoryStore) - 30天内的1000条
4. **跨智能体上下文** (GlobalContextManager) - 共享信息

### 三层上下文系统

1. **即时上下文** (MineContext) - 当前对话20条
2. **会话上下文** (MineContext) - 当前任务
3. **长期上下文** (MineContext) - 永久知识库

### 智能特性

- ✅ 自动晋升（短期→长期）
- ✅ 智能淘汰（按重要性）
- ✅ 相关性评分和检索
- ✅ 多维度搜索
- ✅ TTL过期管理
- ✅ 跨智能体共享
- ✅ 数据库持久化
- ✅ 线程安全
- ✅ 实时统计监控

**完全满足生产环境的Memory & Context Engineering需求！** 🚀
