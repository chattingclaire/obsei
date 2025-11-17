# 🧠 集成开源Context/Memory方案

## 推荐方案对比

### 1. **Mem0** (强烈推荐) ⭐⭐⭐⭐⭐

**GitHub**: https://github.com/mem0ai/mem0

```bash
pip install mem0ai
```

**特性：**
- ✅ 专为AI智能体设计的记忆层
- ✅ 支持多种LLM（Claude、GPT等）
- ✅ 自动记忆管理（添加、更新、删除）
- ✅ 语义搜索（基于向量）
- ✅ 用户/会话/智能体级别的记忆隔离
- ✅ 支持多种存储后端（Qdrant、Postgres、Redis）
- ✅ 简单易用的API

**代码示例：**
```python
from mem0 import Memory

# 初始化（使用Qdrant作为向量存储）
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333
        }
    },
    "llm": {
        "provider": "anthropic",
        "config": {
            "model": "claude-sonnet-4-20250514",
            "api_key": "your-key"
        }
    }
}

memory = Memory.from_config(config)

# 添加记忆
memory.add(
    "用户喜欢AI和Web3领域的创业项目",
    user_id="user123",
    agent_id="signal_agent"
)

# 搜索相关记忆
results = memory.search(
    "AI创业项目",
    user_id="user123",
    limit=5
)

# 获取所有记忆
all_memories = memory.get_all(user_id="user123")

# 更新记忆
memory.update(
    memory_id="mem_123",
    data="用户最近关注AI Agent方向"
)

# 删除记忆
memory.delete(memory_id="mem_123")
```

**集成到你的Signal Agent：**
```python
# agents/signal_agent_chat.py
from mem0 import Memory
from anthropic import Anthropic

class SignalAgentChat:
    def __init__(self):
        # 使用Mem0替代自己的memory系统
        self.memory = Memory.from_config({
            "vector_store": {
                "provider": "qdrant",
                "config": {"host": "localhost", "port": 6333}
            }
        })

        self.claude = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

    async def process_user_request(self, user_message: str, user_id: str):
        # 1. 搜索相关记忆
        relevant_memories = self.memory.search(
            user_message,
            user_id=user_id,
            agent_id="signal_agent",
            limit=5
        )

        # 2. 查询知识库（保留你的逻辑）
        kb_results = self.query_knowledge_base(user_message)

        # 3. 构建上下文
        context = f"""
        [相关记忆]
        {relevant_memories}

        [知识库]
        {kb_results}

        [用户问题]
        {user_message}
        """

        # 4. 调用Claude
        response = self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": context}]
        )

        # 5. 自动提取并保存新记忆
        self.memory.add(
            response.content[0].text,
            user_id=user_id,
            agent_id="signal_agent"
        )

        return response
```

---

### 2. **Zep** (生产级记忆存储) ⭐⭐⭐⭐⭐

**GitHub**: https://github.com/getzep/zep

```bash
# 使用Docker运行Zep服务器
docker run -d -p 8000:8000 ghcr.io/getzep/zep:latest

# 安装Python客户端
pip install zep-python
```

**特性：**
- ✅ 专为生产环境设计
- ✅ 长期记忆持久化
- ✅ 自动记忆摘要和提取
- ✅ 会话管理
- ✅ 向量搜索
- ✅ 事实提取
- ✅ 低延迟（<50ms）

**代码示例：**
```python
from zep_python import ZepClient
from zep_python.memory import Memory, Message

# 初始化Zep客户端
zep = ZepClient(base_url="http://localhost:8000")

# 创建用户
zep.user.add(user_id="user123", metadata={"name": "Claire"})

# 添加会话记忆
session_id = "signal_agent_session_001"

# 添加消息到会话
zep.memory.add_memory(
    session_id=session_id,
    messages=[
        Message(role="user", content="帮我找AI创业项目"),
        Message(role="assistant", content="我找到了3个项目...")
    ]
)

# 搜索记忆
search_results = zep.memory.search_memory(
    session_id=session_id,
    search_query="AI项目",
    limit=5
)

# 获取会话记忆
memory = zep.memory.get_memory(session_id=session_id)

# 获取会话摘要（自动生成）
summary = memory.summary
```

**集成示例：**
```python
from zep_python import ZepClient

class SignalAgentChat:
    def __init__(self):
        self.zep = ZepClient("http://localhost:8000")
        self.claude = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

    async def chat(self, user_message: str, session_id: str, user_id: str):
        # 1. 获取会话记忆
        memory = self.zep.memory.get_memory(session_id=session_id)

        # 2. 搜索相关上下文
        search_results = self.zep.memory.search_memory(
            session_id=session_id,
            search_query=user_message,
            limit=5
        )

        # 3. 构建上下文（包含会话摘要）
        context = f"""
        [会话摘要]
        {memory.summary.content if memory.summary else ""}

        [相关历史]
        {[r.message for r in search_results]}

        [知识库]
        {self.query_knowledge_base(user_message)}
        """

        # 4. 调用Claude
        response = self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": context}]
        )

        # 5. 保存到Zep
        self.zep.memory.add_memory(
            session_id=session_id,
            messages=[
                Message(role="user", content=user_message),
                Message(role="assistant", content=response.content[0].text)
            ]
        )

        return response
```

---

### 3. **LangChain Memory** (最成熟生态) ⭐⭐⭐⭐

```bash
pip install langchain langchain-anthropic
```

**特性：**
- ✅ 多种记忆类型（ConversationBuffer, Summary, KG等）
- ✅ 与LangChain生态完全集成
- ✅ 支持所有主流向量数据库
- ✅ 文档丰富、社区大

**代码示例：**
```python
from langchain.memory import ConversationBufferMemory, VectorStoreRetrieverMemory
from langchain_anthropic import ChatAnthropic
from langchain.chains import ConversationChain
from langchain_community.vectorstores import Qdrant

# 方案A: 简单的对话缓冲记忆
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="output"
)

# 方案B: 向量存储记忆（语义搜索）
vectorstore = Qdrant(
    client=qdrant_client,
    collection_name="signal_agent_memory",
    embeddings=embeddings
)

memory = VectorStoreRetrieverMemory(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    memory_key="chat_history"
)

# 创建对话链
llm = ChatAnthropic(model="claude-sonnet-4-20250514")

conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

# 使用
response = conversation.predict(input="帮我找AI创业项目")
```

**集成示例：**
```python
from langchain.memory import ConversationSummaryBufferMemory
from langchain_anthropic import ChatAnthropic

class SignalAgentChat:
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("CLAUDE_API_KEY")
        )

        # 使用摘要缓冲记忆（自动压缩长对话）
        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=2000,
            return_messages=True
        )

    async def chat(self, user_message: str):
        # 1. 加载记忆上下文
        context = self.memory.load_memory_variables({})

        # 2. 查询知识库
        kb_results = self.query_knowledge_base(user_message)

        # 3. 构建完整提示
        full_prompt = f"""
        {context['history']}

        [知识库]
        {kb_results}

        [用户]
        {user_message}
        """

        # 4. 调用LLM
        response = self.llm.invoke(full_prompt)

        # 5. 保存到记忆
        self.memory.save_context(
            {"input": user_message},
            {"output": response.content}
        )

        return response
```

---

### 4. **MemGPT** (超长期记忆) ⭐⭐⭐⭐

**GitHub**: https://github.com/cpacker/MemGPT

```bash
pip install pymemgpt
```

**特性：**
- ✅ 操作系统式的记忆管理
- ✅ 主记忆+归档记忆
- ✅ 自动记忆分页
- ✅ 超长上下文支持
- ✅ 记忆编辑和管理

**适合：** 需要极长对话历史的场景

---

## 🎯 推荐方案：Mem0 + Zep

### 为什么选这两个？

| 需求 | Mem0 | Zep | LangChain | MemGPT |
|------|------|-----|-----------|--------|
| **易用性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **智能体优化** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **生产就绪** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **性能** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Claude支持** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **向量搜索** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **自动摘要** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **文档** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

### 组合使用方案

```python
# 使用Mem0做智能体级别的长期记忆
# 使用Zep做会话级别的对话历史

from mem0 import Memory
from zep_python import ZepClient

class SignalAgentChat:
    def __init__(self):
        # Mem0: 长期记忆（用户偏好、历史洞察）
        self.long_term_memory = Memory.from_config({
            "vector_store": {"provider": "qdrant", ...}
        })

        # Zep: 会话记忆（对话历史、会话摘要）
        self.zep = ZepClient("http://localhost:8000")

        self.claude = Anthropic(...)

    async def chat(self, user_message: str, user_id: str, session_id: str):
        # 1. 从Zep获取会话上下文
        session_memory = self.zep.memory.get_memory(session_id=session_id)

        # 2. 从Mem0搜索长期记忆
        long_term_context = self.long_term_memory.search(
            user_message,
            user_id=user_id,
            limit=3
        )

        # 3. 查询知识库（保留你的Supabase逻辑）
        kb_results = self.query_knowledge_base(user_message)

        # 4. 整合所有上下文
        context = f"""
        [长期记忆] {long_term_context}
        [会话摘要] {session_memory.summary}
        [知识库] {kb_results}
        [历史对话] {session_memory.messages[-5:]}
        """

        # 5. 调用Claude
        response = self.claude.messages.create(...)

        # 6. 保存到两个记忆系统
        # Zep: 保存对话
        self.zep.memory.add_memory(
            session_id=session_id,
            messages=[
                Message(role="user", content=user_message),
                Message(role="assistant", content=response.content[0].text)
            ]
        )

        # Mem0: 提取重要信息保存为长期记忆
        if self._is_important(response):
            self.long_term_memory.add(
                response.content[0].text,
                user_id=user_id,
                agent_id="signal_agent"
            )

        return response
```

---

## 📦 完整集成方案

### 步骤1: 安装依赖

```bash
# 添加到 requirements.txt
mem0ai>=0.1.0
zep-python>=2.0.0
qdrant-client>=1.7.0  # 向量数据库
```

### 步骤2: 启动Zep服务

```bash
# docker-compose.yml
version: '3.8'

services:
  zep:
    image: ghcr.io/getzep/zep:latest
    ports:
      - "8000:8000"
    environment:
      - ZEP_MEMORY_STORE_TYPE=postgres
      - ZEP_MEMORY_STORE_POSTGRES_DSN=postgresql://user:pass@postgres:5432/zep
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=zep

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
```

```bash
docker-compose up -d
```

### 步骤3: 创建新的Memory模块

```python
# core/advanced_memory.py
from mem0 import Memory
from zep_python import ZepClient, Message
from typing import List, Dict, Optional
import os

class AdvancedMemoryManager:
    """
    结合Mem0和Zep的高级记忆管理
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

        # Mem0: 长期语义记忆
        self.mem0 = Memory.from_config({
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": os.getenv("QDRANT_HOST", "localhost"),
                    "port": int(os.getenv("QDRANT_PORT", 6333)),
                    "collection_name": f"{agent_name}_memory"
                }
            },
            "llm": {
                "provider": "anthropic",
                "config": {
                    "model": "claude-sonnet-4-20250514",
                    "api_key": os.getenv("CLAUDE_API_KEY")
                }
            }
        })

        # Zep: 会话记忆和自动摘要
        self.zep = ZepClient(
            base_url=os.getenv("ZEP_API_URL", "http://localhost:8000")
        )

    def add_conversation(
        self,
        user_message: str,
        assistant_message: str,
        session_id: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ):
        """添加对话到记忆"""
        # 添加到Zep（会话记忆）
        self.zep.memory.add_memory(
            session_id=session_id,
            messages=[
                Message(
                    role="user",
                    content=user_message,
                    metadata=metadata or {}
                ),
                Message(
                    role="assistant",
                    content=assistant_message,
                    metadata={"agent": self.agent_name}
                )
            ]
        )

        # 如果重要，添加到Mem0（长期记忆）
        importance = self._calculate_importance(user_message, assistant_message)
        if importance > 0.7:
            self.mem0.add(
                assistant_message,
                user_id=user_id,
                agent_id=self.agent_name,
                metadata={
                    "importance": importance,
                    "session_id": session_id,
                    **(metadata or {})
                }
            )

    def retrieve_context(
        self,
        query: str,
        session_id: str,
        user_id: str,
        include_long_term: bool = True
    ) -> Dict[str, any]:
        """检索相关上下文"""
        context = {}

        # 1. 从Zep获取会话记忆
        try:
            session_memory = self.zep.memory.get_memory(session_id=session_id)

            context["session_summary"] = (
                session_memory.summary.content
                if session_memory.summary
                else ""
            )

            context["recent_messages"] = [
                {"role": msg.role, "content": msg.content}
                for msg in session_memory.messages[-10:]
            ]

            # 语义搜索会话历史
            search_results = self.zep.memory.search_memory(
                session_id=session_id,
                search_query=query,
                limit=5
            )

            context["relevant_history"] = [
                {"content": r.message.content, "score": r.score}
                for r in search_results
            ]

        except Exception as e:
            context["session_summary"] = ""
            context["recent_messages"] = []
            context["relevant_history"] = []

        # 2. 从Mem0获取长期记忆
        if include_long_term:
            long_term_memories = self.mem0.search(
                query,
                user_id=user_id,
                agent_id=self.agent_name,
                limit=5
            )

            context["long_term_memories"] = [
                {
                    "memory": mem.get("memory", ""),
                    "metadata": mem.get("metadata", {})
                }
                for mem in long_term_memories.get("results", [])
            ]
        else:
            context["long_term_memories"] = []

        return context

    def get_stats(self) -> Dict:
        """获取记忆统计"""
        return {
            "agent_name": self.agent_name,
            "zep_connected": self._check_zep_connection(),
            "mem0_connected": True,  # Mem0没有直接的连接检查
        }

    def _calculate_importance(self, user_msg: str, assistant_msg: str) -> float:
        """计算对话重要性（简化版）"""
        # 可以用LLM来判断，这里用简单规则
        keywords = ["重要", "记住", "偏好", "喜欢", "不喜欢", "总是", "从不"]
        score = 0.5

        for keyword in keywords:
            if keyword in user_msg or keyword in assistant_msg:
                score += 0.1

        return min(score, 1.0)

    def _check_zep_connection(self) -> bool:
        """检查Zep连接"""
        try:
            self.zep.memory.get_memory(session_id="test")
            return True
        except:
            return False
```

### 步骤4: 更新智能体使用新Memory

```python
# agents/signal_agent_chat.py
from core.advanced_memory import AdvancedMemoryManager

class SignalAgentChat(AgentChatInterface):
    def __init__(self):
        super().__init__("signal_agent", system_prompt)

        # 使用高级记忆管理器（替换旧的memory系统）
        self.memory = AdvancedMemoryManager("signal_agent")

        self.claude = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

    async def process_user_request(
        self,
        user_message: str,
        user_id: str,
        session_id: str
    ):
        # 1. 检索上下文
        context = self.memory.retrieve_context(
            query=user_message,
            session_id=session_id,
            user_id=user_id,
            include_long_term=True
        )

        # 2. 查询知识库（保留你的逻辑）
        kb_results = self.query_knowledge_base(user_message)

        # 3. 构建完整上下文
        full_context = f"""
        [会话摘要]
        {context['session_summary']}

        [相关历史对话]
        {context['relevant_history']}

        [长期记忆]
        {context['long_term_memories']}

        [知识库]
        {kb_results}

        [最近对话]
        {context['recent_messages'][-5:]}

        [当前问题]
        {user_message}
        """

        # 4. 调用Claude
        response = self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": full_context}]
        )

        assistant_message = response.content[0].text

        # 5. 保存到记忆系统
        self.memory.add_conversation(
            user_message=user_message,
            assistant_message=assistant_message,
            session_id=session_id,
            user_id=user_id,
            metadata={"kb_query_count": len(kb_results)}
        )

        return {
            "message": assistant_message,
            "agent": "signal_agent",
            "context_used": {
                "long_term_memories": len(context['long_term_memories']),
                "relevant_history": len(context['relevant_history'])
            }
        }
```

---

## ✅ 最终架构

```
你的系统架构：

┌─────────────────────────────────────┐
│  Data Agent (你的代码)               │ ← 保留
│  - GitHub, Twitter, ProductHunt采集  │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Classify Agent (你的代码)           │ ← 保留
│  - 3层分类系统                       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Supabase (你的schema)               │ ← 保留
│  - 8张表的完整架构                   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  对话智能体 (你的代码)               │ ← 保留
│  ├─ Signal Agent                    │
│  ├─ Insight Agent                   │
│  └─ Venture Agent                   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Memory & Context (开源方案)         │ ← 替换
│  ├─ Mem0 (长期记忆)                 │ ✅ 新增
│  ├─ Zep (会话记忆)                  │ ✅ 新增
│  └─ Qdrant (向量存储)               │ ✅ 新增
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Next.js Dashboard (你的UI)          │ ← 保留
└─────────────────────────────────────┘
```

---

## 🚀 下一步

我可以帮你：
1. ✅ 更新 requirements.txt
2. ✅ 创建 docker-compose.yml（Zep + Qdrant）
3. ✅ 编写 core/advanced_memory.py
4. ✅ 更新所有对话智能体使用新Memory
5. ✅ 创建迁移脚本（可选：从旧Memory迁移数据）

需要我现在就开始集成吗？🔧
