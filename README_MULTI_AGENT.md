# Multi-Agent AI Intelligence Platform

A production-grade, modular, and configurable multi-agent system for discovering and analyzing emerging startups, technologies, and investment opportunities with a focus on Chinese and Overseas Chinese founders.

## 🚀 Features

### Multi-Agent Pipeline
- **Data Agent**: Multi-source ingestion (GitHub, Twitter/X, Reddit, ProductHunt, HackerNews, TechCrunch, YouTube, Kickstarter, Crunchbase)
- **Classify Agent**: 3-layer taxonomy classification using Claude SDK
- **Signal Agent**: Xiaohongshu-style signal generation with lightweight enrichment
- **Insight Agent**: Weekly USD-fund style long-form insights
- **Venture Agent**: Investment intelligence focused on Chinese/Overseas Chinese founders

### Infrastructure
- **Supabase Backend**: PostgreSQL with realtime subscriptions
- **Claude SDK with KV Cache**: Optimized LLM usage with caching
- **Browser Automation**: Playwright & Browserless integration
- **Tools/MCP System**: Reusable, modular tool architecture
- **Next.js Dashboard**: Real-time monitoring and control
- **Memory & Context**: Per-agent and global memory management

## 📁 Project Structure

See full project structure in repository.

## 🛠️ Installation & Usage

See detailed installation and usage instructions in the full documentation.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config/.env.example config/.env
# Edit config/.env with your API keys

# Run pipeline
python main.py --mode pipeline

# Run dashboard
python main.py --mode dashboard
```

## 📊 System Architecture

Data Agent → Classify Agent → [Signal Agent | Insight Agent | Venture Agent]

All agents write to Supabase and communicate via shared context.

## 📄 License

MIT License

---

**Multi-Agent AI Intelligence Platform** - Discovering tomorrow's opportunities, today.
