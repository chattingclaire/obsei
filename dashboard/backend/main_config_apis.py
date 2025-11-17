
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
