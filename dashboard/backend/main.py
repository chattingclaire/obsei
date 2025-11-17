"""
Dashboard Backend - FastAPI
Provides REST API for dashboard frontend
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.supabase_client import get_supabase_client

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
