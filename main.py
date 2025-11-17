"""
Main Entry Point for Multi-Agent Intelligence System
"""

import os
import sys
import argparse
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config/.env")
load_dotenv("config/keys.env")
load_dotenv("config/supabase.env")

from core.logger import get_system_logger
from run_pipeline import PipelineOrchestrator

logger = get_system_logger()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Multi-Agent Intelligence System")

    parser.add_argument(
        "--mode",
        type=str,
        choices=["pipeline", "single-agent", "dashboard"],
        default="pipeline",
        help="Execution mode"
    )

    parser.add_argument(
        "--agent",
        type=str,
        choices=["data", "classify", "signal", "insight", "venture"],
        help="Agent to run (for single-agent mode)"
    )

    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous mode"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Interval in seconds for continuous mode"
    )

    args = parser.parse_args()

    if args.mode == "pipeline":
        # Run full pipeline
        orchestrator = PipelineOrchestrator()

        if args.continuous:
            print(f"Starting continuous pipeline (interval: {args.interval}s)...")
            print("Press Ctrl+C to stop")
            asyncio.run(orchestrator.run_continuous(args.interval))
        else:
            print("Running pipeline (single run)...")
            stats = asyncio.run(orchestrator.run_pipeline(mode="full"))
            print(f"\nPipeline completed in {stats.get('duration_seconds', 0):.2f}s")
            print(f"Results: {stats.get('results', {})}")

    elif args.mode == "single-agent":
        if not args.agent:
            print("Error: --agent required for single-agent mode")
            sys.exit(1)

        # Run single agent
        print(f"Running {args.agent} agent...")

        if args.agent == "data":
            from agents.data_agent import DataAgent
            agent = DataAgent()
            stats = asyncio.run(agent.run())

        elif args.agent == "classify":
            from agents.classify_agent import ClassifyAgent
            agent = ClassifyAgent()
            stats = agent.run()

        elif args.agent == "signal":
            from agents.signal_agent import SignalAgent
            agent = SignalAgent()
            stats = asyncio.run(agent.run())

        elif args.agent == "insight":
            from agents.insight_agent import InsightAgent
            agent = InsightAgent()
            stats = agent.run()

        elif args.agent == "venture":
            from agents.venture_agent import VentureAgent
            agent = VentureAgent()
            stats = agent.run()

        print(f"\nAgent completed: {stats}")

    elif args.mode == "dashboard":
        print("Starting dashboard...")
        print("Dashboard URL: http://localhost:3000")
        print("API URL: http://localhost:8000")
        # In production, start dashboard processes
        os.system("cd dashboard/backend && uvicorn main:app --reload &")
        os.system("cd dashboard/frontend && npm run dev")


if __name__ == "__main__":
    main()
