"""
Agent Chat Interface Base Class
Enables agents to have conversational interactions with users
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json

from anthropic import Anthropic

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cache_manager import get_cache_manager
from database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class AgentChatInterface:
    """
    Base class for agent chat interfaces
    Allows agents to interact conversationally with users
    """

    def __init__(self, agent_name: str, system_prompt: str):
        """
        Initialize chat interface

        Args:
            agent_name: Name of the agent
            system_prompt: System prompt for the agent
        """
        self.agent_name = agent_name
        self.system_prompt = system_prompt

        # Initialize Claude client
        self.claude = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

        # Cache manager
        self.cache_manager = get_cache_manager()

        # Database client
        self.db = get_supabase_client()

        # Chat history (in-memory for now, can be persisted to DB)
        self.chat_history: List[Dict[str, str]] = []

        logger.info(f"Chat interface initialized for {agent_name}")

    def chat(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        use_tools: bool = True
    ) -> Dict[str, Any]:
        """
        Process user message and return agent response

        Args:
            user_message: User's message
            context: Optional context (knowledge base queries, etc.)
            use_tools: Whether to allow tool usage

        Returns:
            Response dict with message, tool calls, and metadata
        """
        try:
            # Build messages with history
            messages = self._build_messages(user_message, context)

            # Add to chat history
            self.chat_history.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            # Call Claude with cache
            cache_params = self.cache_manager.build_claude_cache_params(
                self.agent_name,
                json.dumps(messages),
                self.model
            )

            response = self.claude.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self._build_system_prompt(context),
                messages=messages,
                temperature=0.7,
                **cache_params
            )

            # Extract response
            assistant_message = response.content[0].text

            # Add to chat history
            self.chat_history.append({
                "role": "assistant",
                "content": assistant_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            # Save to database
            self._save_chat_to_db(user_message, assistant_message, context)

            return {
                "message": assistant_message,
                "agent": self.agent_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0,
                "success": True
            }

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "message": f"抱歉，处理您的请求时出现错误: {str(e)}",
                "agent": self.agent_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "success": False,
                "error": str(e)
            }

    def _build_messages(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Build messages array with history"""
        messages = []

        # Add recent chat history (last 10 messages)
        for msg in self.chat_history[-10:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add context if provided
        if context:
            context_str = self._format_context(context)
            if context_str:
                messages.append({
                    "role": "user",
                    "content": f"[知识库上下文]\n{context_str}\n\n[用户问题]\n{user_message}"
                })
            else:
                messages.append({
                    "role": "user",
                    "content": user_message
                })
        else:
            messages.append({
                "role": "user",
                "content": user_message
            })

        return messages

    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build system prompt with context"""
        base_prompt = self.system_prompt

        # Add chat mode instructions
        chat_instructions = """

## 对话模式

你现在处于对话模式。用户会用中文或英文与你交流，请用友好、专业的方式回应。

### 对话原则
- 使用中文回答（除非用户用英文）
- 简洁明了，重点突出
- 主动提供可操作的建议
- 如需使用工具，说明工具的作用
- 引用知识库中的具体数据时，注明来源

### 你可以做的事情
1. 查询和分析知识库中的数据
2. 使用工具获取实时信息
3. 生成报告和洞察
4. 提供投资建议和分析
5. 回答关于创业公司、技术趋势的问题

### 知识库访问
你可以访问以下知识库：
- raw_items: 原始数据（GitHub、Twitter、Reddit等来源）
- classified_items: 已分类的项目
- founders: 创始人信息
- signals: 生成的信号
- insights: 洞察报告
- investments: 投资机会

请始终基于知识库中的真实数据回答问题。
"""

        return base_prompt + chat_instructions

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompt"""
        formatted = []

        if context.get("knowledge_base"):
            kb = context["knowledge_base"]
            formatted.append("=== 相关知识库数据 ===")

            if kb.get("classified_items"):
                formatted.append(f"\n找到 {len(kb['classified_items'])} 个相关分类项目:")
                for item in kb["classified_items"][:5]:  # Top 5
                    formatted.append(f"- {item.get('title')}")
                    formatted.append(f"  分类: {item.get('category_l1')}/{item.get('category_l2')}/{item.get('category_l3')}")
                    formatted.append(f"  摘要: {item.get('summary', '')[:100]}")

            if kb.get("signals"):
                formatted.append(f"\n找到 {len(kb['signals'])} 个相关信号:")
                for signal in kb["signals"][:3]:  # Top 3
                    formatted.append(f"- {signal.get('title')}")
                    formatted.append(f"  评分: {signal.get('signal_score', 0):.2f}")

            if kb.get("founders"):
                formatted.append(f"\n找到 {len(kb['founders'])} 位相关创始人:")
                for founder in kb["founders"][:3]:
                    formatted.append(f"- {founder.get('name')}: {founder.get('bio', '')[:100]}")

        if context.get("stats"):
            formatted.append("\n=== 统计数据 ===")
            for key, value in context["stats"].items():
                formatted.append(f"{key}: {value}")

        return "\n".join(formatted) if formatted else ""

    def _save_chat_to_db(
        self,
        user_message: str,
        assistant_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Save chat to database"""
        try:
            self.db.log_agent_activity(
                agent_name=self.agent_name,
                log_level="INFO",
                message=f"Chat: {user_message[:100]}",
                operation="chat",
                metadata={
                    "user_message": user_message,
                    "assistant_message": assistant_message,
                    "context": context
                }
            )
        except Exception as e:
            logger.error(f"Error saving chat to DB: {e}")

    def get_chat_history(self, limit: int = 50) -> List[Dict[str, str]]:
        """Get chat history"""
        return self.chat_history[-limit:]

    def clear_chat_history(self):
        """Clear chat history"""
        self.chat_history = []
        logger.info(f"Chat history cleared for {self.agent_name}")

    def query_knowledge_base(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Query knowledge base for relevant information

        Args:
            query: Search query
            categories: Optional category filters
            limit: Maximum results

        Returns:
            Knowledge base results
        """
        try:
            results = {
                "classified_items": [],
                "signals": [],
                "founders": [],
                "insights": []
            }

            # Query classified items
            if categories:
                for category in categories:
                    items = self.db.get_classified_items(
                        category_l1=category,
                        limit=limit
                    )
                    results["classified_items"].extend(items)
            else:
                results["classified_items"] = self.db.get_classified_items(limit=limit)

            # Query signals
            results["signals"] = self.db.get_published_signals_for_rss(limit=limit)

            # Query recent insights
            results["insights"] = self.db.get_recent_insights(limit=5)

            # In production, implement full-text search on query
            # For now, return recent items

            return results

        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return {}
