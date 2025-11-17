"""
Dashboard Backend - FastAPI
Provides REST API for dashboard frontend
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.supabase_client import get_supabase_client

# Import chat agents
from agents.signal_agent_chat import SignalAgentChat
from agents.insight_agent_chat import InsightAgentChat
from agents.venture_agent_chat import VentureAgentChat

app = FastAPI(
    title="Multi-Agent Intelligence Dashboard API",
    description="REST API for multi-agent intelligence system dashboard",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database client
db = get_supabase_client()


# Models
class AgentStatusResponse(BaseModel):
    agent_name: str
    status: str
    last_heartbeat: str
    processed_count: int
    error_count: int


class PipelineMetricsResponse(BaseModel):
    raw_items: int
    classified_items: int
    signals: int
    insights: int
    investments: int


class ChatMessage(BaseModel):
    message: str
    agent_name: str
    auto_query_kb: bool = True


class ChatResponse(BaseModel):
    message: str
    agent: str
    timestamp: str
    success: bool
    tokens_used: Optional[int] = None
    generated_signals: Optional[List[Dict]] = None
    custom_analysis: Optional[Dict] = None
    recommendations: Optional[List[Dict]] = None


# Initialize chat agents
chat_agents = {
    "signal_agent": None,
    "insight_agent": None,
    "venture_agent": None
}


def get_chat_agent(agent_name: str):
    """Get or initialize chat agent"""
    if agent_name not in chat_agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    if chat_agents[agent_name] is None:
        if agent_name == "signal_agent":
            chat_agents[agent_name] = SignalAgentChat()
        elif agent_name == "insight_agent":
            chat_agents[agent_name] = InsightAgentChat()
        elif agent_name == "venture_agent":
            chat_agents[agent_name] = VentureAgentChat()

    return chat_agents[agent_name]


# Routes
@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "name": "Multi-Agent Intelligence Dashboard API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    db_healthy = db.health_check()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/agents/status", response_model=List[AgentStatusResponse])
def get_agent_status():
    """Get status of all agents"""
    try:
        agents = db.get_agent_status()
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_name}/status")
def get_specific_agent_status(agent_name: str):
    """Get status of specific agent"""
    try:
        agents = db.get_agent_status(agent_name=agent_name)
        if not agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agents[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/pipeline", response_model=PipelineMetricsResponse)
def get_pipeline_metrics():
    """Get pipeline metrics"""
    try:
        metrics = db.get_pipeline_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/categories")
def get_category_distribution():
    """Get category distribution"""
    try:
        distribution = db.get_category_distribution()
        return distribution
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/signals/recent")
def get_recent_signals(limit: int = 100):
    """Get recent signals"""
    try:
        signals = db.get_published_signals_for_rss(limit=limit)
        return signals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/insights/recent")
def get_recent_insights(insight_type: str = "weekly", limit: int = 10):
    """Get recent insights"""
    try:
        insights = db.get_recent_insights(insight_type=insight_type, limit=limit)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/investments/high-score")
def get_high_score_investments(min_score: float = 0.7, limit: int = 50):
    """Get high-scoring investment opportunities"""
    try:
        investments = db.get_high_score_investments(min_score=min_score, limit=limit)
        return investments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_name}/run")
async def trigger_agent_run(agent_name: str):
    """Trigger manual agent run"""
    try:
        # In production, trigger agent execution
        # For now, return success
        return {
            "status": "triggered",
            "agent": agent_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Chat endpoints
@app.post("/chat/{agent_name}", response_model=ChatResponse)
async def chat_with_agent(agent_name: str, chat_message: ChatMessage):
    """
    Chat with an agent

    Supported agents: signal_agent, insight_agent, venture_agent
    """
    try:
        agent = get_chat_agent(agent_name)

        if agent_name == "signal_agent":
            response = await agent.process_user_request(
                chat_message.message,
                auto_query_kb=chat_message.auto_query_kb
            )
        else:
            response = agent.process_user_request(
                chat_message.message,
                auto_query_kb=chat_message.auto_query_kb
            )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/{agent_name}/history")
def get_chat_history(agent_name: str, limit: int = 50):
    """Get chat history for an agent"""
    try:
        agent = get_chat_agent(agent_name)
        history = agent.get_chat_history(limit=limit)
        return {
            "agent": agent_name,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/chat/{agent_name}/history")
def clear_chat_history(agent_name: str):
    """Clear chat history for an agent"""
    try:
        agent = get_chat_agent(agent_name)
        agent.clear_chat_history()
        return {
            "agent": agent_name,
            "status": "cleared",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/list")
def list_agents():
    """List all available agents"""
    return {
        "agents": [
            {
                "name": "data_agent",
                "display_name": "数据采集Agent",
                "description": "从多个源采集数据",
                "chat_enabled": False,
                "status": "background"
            },
            {
                "name": "classify_agent",
                "display_name": "分类Agent",
                "description": "对数据进行分类和标注",
                "chat_enabled": False,
                "status": "background"
            },
            {
                "name": "signal_agent",
                "display_name": "信号Agent",
                "description": "生成小红书风格的信号",
                "chat_enabled": True,
                "capabilities": ["生成信号", "查询知识库", "验证信息"]
            },
            {
                "name": "insight_agent",
                "display_name": "洞察Agent",
                "description": "生成投资洞察和分析",
                "chat_enabled": True,
                "capabilities": ["趋势分析", "类别分析", "定制报告"]
            },
            {
                "name": "venture_agent",
                "display_name": "投资Agent",
                "description": "分析投资机会和创始人",
                "chat_enabled": True,
                "capabilities": ["投资推荐", "创始人研究", "公司分析"]
            }
        ]
    }


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket for realtime logs"""
    await websocket.accept()

    try:
        while True:
            # In production, stream logs from agent_logs table
            # For now, send periodic updates
            await websocket.send_json({
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Log stream active"
            })
            await asyncio.sleep(5)

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
