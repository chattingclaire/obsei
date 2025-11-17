# 🚀 Quick Start Guide

Your API keys have been configured! Follow these steps to get your Multi-Agent AI Platform running.

## ✅ What's Already Done

- ✅ All API keys configured in `.env` file
- ✅ Claude API key set
- ✅ Supabase credentials configured
- ✅ GitHub token added
- ✅ Twitter/X API keys added
- ✅ ProductHunt API keys added

## 📋 Next Steps

### Step 1: Install Dependencies (5 minutes)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd dashboard/frontend
npm install
cd ../..
```

### Step 2: Set Up Database (2 minutes)

**Option A: Automated Helper Script**
```bash
python setup_database.py
```

The script will guide you through:
1. Opening Supabase dashboard
2. Navigating to SQL Editor
3. Executing the schema from `database/schema.sql`

**Option B: Manual Setup**
1. Go to https://supabase.com/dashboard
2. Select project: `fftkazutsznpjvkqctvy`
3. Click "SQL Editor" → "New Query"
4. Copy all content from `database/schema.sql`
5. Paste and click "Run"

This will create 8 tables:
- `raw_items` - Original collected data
- `classified_items` - Categorized content
- `founders` - Founder profiles
- `signals` - Generated signals
- `insights` - Trend analysis
- `investments` - Investment opportunities
- `agent_status` - Agent health monitoring
- `agent_logs` - System logs

### Step 3: Verify Setup (1 minute)

```bash
python verify_setup.py
```

This will check:
- ✅ Claude API connectivity
- ✅ Supabase database connection
- ✅ GitHub API
- ✅ Twitter API
- ✅ ProductHunt API
- ✅ File structure
- ✅ Dependencies

### Step 4: Start the System

**Option A: Full System (All Components)**
```bash
# Terminal 1: Start backend API
cd dashboard/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend dashboard
cd dashboard/frontend
npm run dev

# Terminal 3: Start agent pipeline
python pipeline_orchestrator.py
```

**Option B: Simplified Start (Backend + Single Agent)**
```bash
# Terminal 1: Start backend
cd dashboard/backend
uvicorn main:app --reload

# Terminal 2: Test single agent
python -c "from agents.data_agent import DataAgent; agent = DataAgent(); agent.run_once()"
```

### Step 5: Access the Dashboard

1. Open browser: http://localhost:3000
2. You'll see:
   - **Pipeline Metrics** - Real-time agent status
   - **Agent Chat** - Interact with Signal, Insight, and Venture agents
   - **Configuration Panels** - Configure data sources and taxonomy

## 🎯 What Each Agent Does

### 1. Data Agent (Background Worker)
- Automatically collects data from:
  - GitHub trending repositories
  - Twitter/X tech discussions
  - ProductHunt launches
  - (Coming soon: Reddit, YouTube, TechCrunch, etc.)
- Runs continuously every 30 minutes
- Stores raw data in `raw_items` table

### 2. Classify Agent (Background Worker)
- Automatically categorizes collected data
- Uses 3-layer taxonomy (L1/L2/L3)
- Extracts keywords and entities
- Stores in `classified_items` table

### 3. Signal Agent (Conversational)
- **Chat with it!** Ask: "帮我查找最近的AI创业项目"
- Generates formatted signals for social media
- Outputs in Xiaohongshu style
- Queries the knowledge base built by agents 1 & 2

### 4. Insight Agent (Conversational)
- **Chat with it!** Ask: "分析最近一周的趋势"
- Provides trend analysis
- Identifies emerging patterns
- Cross-references multiple data sources

### 5. Venture Agent (Conversational)
- **Chat with it!** Ask: "推荐高分投资机会"
- Evaluates investment opportunities
- Scores projects 0-1 on investability
- Tracks founder backgrounds

## 🧪 Quick Test

Test individual agents:

```bash
# Test data collection
python -c "
from agents.data_agent import DataAgent
agent = DataAgent()
agent.run_once()
print('✅ Data agent working!')
"

# Test classification
python -c "
from agents.classify_agent import ClassifyAgent
agent = ClassifyAgent()
agent.run_once()
print('✅ Classify agent working!')
"

# Test chat with Signal Agent
python -c "
from agents.signal_agent_chat import SignalAgentChat
agent = SignalAgentChat()
response = agent.process_user_request('帮我查找AI相关的项目')
print(response)
"
```

## 📊 Monitoring

- **Agent Status**: Check `agent_status` table for heartbeats
- **Logs**: Check `agent_logs` table for activity
- **Dashboard**: http://localhost:3000 shows real-time metrics

## 🔧 Configuration

### Data Sources
Edit `config/settings.yaml` to:
- Enable/disable data sources
- Set collection intervals
- Add tracking keywords
- Configure API rate limits

### Taxonomy
Edit `config/taxonomy.json` to:
- Add new categories (L1/L2/L3)
- Define subcategories
- Set classification rules

### Agent Behavior
Edit agent prompt files in `config/prompts/`:
- `data_agent_prompt.md`
- `classify_agent_prompt.md`
- `signal_agent_prompt.md`
- `insight_agent_prompt.md`
- `venture_agent_prompt.md`

## 🆘 Troubleshooting

### Database Connection Error
```
Error: relation "agent_status" does not exist
```
**Solution**: Run `python setup_database.py` and execute the schema in Supabase

### Claude API Error
```
Error: AuthenticationError
```
**Solution**: Check your `CLAUDE_API_KEY` in `.env` file

### Import Errors
```
ModuleNotFoundError: No module named 'anthropic'
```
**Solution**: Run `pip install -r requirements.txt`

### Port Already in Use
```
Error: Address already in use
```
**Solution**: Change port in command or kill existing process

## 📚 Additional Resources

- **Full Documentation**: See `README_MULTI_AGENT.md`
- **Deployment Guide**: See `DEPLOYMENT_GUIDE.md`
- **Database Schema**: See `database/schema.sql`
- **API Reference**: http://localhost:8000/docs (when backend is running)

## 💡 Tips

1. **Start Small**: Begin with just GitHub data source, expand later
2. **Monitor Costs**: Claude API charges by tokens - check usage regularly
3. **Rate Limits**: Twitter API has strict limits - use carefully
4. **Cache Strategy**: KV cache reduces Claude API costs by ~90%
5. **Supabase Free Tier**: Includes 500MB database, 2GB bandwidth/month

## 🎉 You're All Set!

Your system is configured and ready to go. Run `python verify_setup.py` to confirm everything works, then start exploring!

Questions? Check the main documentation or configuration files for details.
