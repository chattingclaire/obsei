"""
Pipeline Orchestrator
Manages execution of all agents in the correct order
"""

import os
import sys
import logging
import asyncio
import yaml
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from core.logger import get_pipeline_logger
from database.supabase_client import get_supabase_client

# Import agents
from agents.data_agent import DataAgent
from agents.classify_agent import ClassifyAgent
from agents.signal_agent import SignalAgent
from agents.insight_agent import InsightAgent
from agents.venture_agent import VentureAgent

logger = get_pipeline_logger()


class PipelineOrchestrator:
    """
    Orchestrates the multi-agent pipeline
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        Initialize pipeline orchestrator

        Args:
            config_path: Path to settings configuration
        """
        self.config = self._load_config(config_path)
        self.db = get_supabase_client()

        # Initialize agents
        self.agents = {}
        self._init_agents()

        logger.info("Pipeline orchestrator initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration"""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def _init_agents(self):
        """Initialize all agents"""
        agent_config = self.config.get("agents", {})

        if agent_config.get("data_agent", {}).get("enabled", True):
            self.agents["data_agent"] = DataAgent(agent_config.get("data_agent"))

        if agent_config.get("classify_agent", {}).get("enabled", True):
            self.agents["classify_agent"] = ClassifyAgent(agent_config.get("classify_agent"))

        if agent_config.get("signal_agent", {}).get("enabled", True):
            self.agents["signal_agent"] = SignalAgent(agent_config.get("signal_agent"))

        if agent_config.get("insight_agent", {}).get("enabled", True):
            self.agents["insight_agent"] = InsightAgent(agent_config.get("insight_agent"))

        if agent_config.get("venture_agent", {}).get("enabled", True):
            self.agents["venture_agent"] = VentureAgent(agent_config.get("venture_agent"))

        logger.info(f"Initialized {len(self.agents)} agents")

    async def run_pipeline(self, mode: str = "full") -> Dict[str, Any]:
        """
        Run the pipeline

        Args:
            mode: Pipeline mode (full, ingestion_only, analysis_only)

        Returns:
            Pipeline execution statistics
        """
        logger.info(f"Starting pipeline run (mode: {mode})...")

        start_time = datetime.now(timezone.utc)
        results = {}

        try:
            if mode in ["full", "ingestion_only"]:
                # Step 1: Data ingestion
                if "data_agent" in self.agents:
                    logger.info("Running data agent...")
                    results["data_agent"] = await self.agents["data_agent"].run()

                # Step 2: Classification
                if "classify_agent" in self.agents:
                    logger.info("Running classify agent...")
                    results["classify_agent"] = self.agents["classify_agent"].run()

            if mode in ["full", "analysis_only"]:
                # Step 3: Signal generation, insight, and venture analysis (parallel)
                tasks = []

                if "signal_agent" in self.agents:
                    tasks.append(self._run_signal_agent())

                if "insight_agent" in self.agents:
                    tasks.append(self._run_insight_agent())

                if "venture_agent" in self.agents:
                    tasks.append(self._run_venture_agent())

                if tasks:
                    parallel_results = await asyncio.gather(*tasks, return_exceptions=True)

                    for i, result in enumerate(parallel_results):
                        agent_name = ["signal_agent", "insight_agent", "venture_agent"][i]
                        if not isinstance(result, Exception):
                            results[agent_name] = result

            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            pipeline_stats = {
                "mode": mode,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "results": results,
                "success": True
            }

            logger.info(f"Pipeline completed in {duration:.2f}s")
            return pipeline_stats

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return {
                "mode": mode,
                "success": False,
                "error": str(e)
            }

    async def _run_signal_agent(self) -> Dict[str, Any]:
        """Run signal agent"""
        return await self.agents["signal_agent"].run()

    async def _run_insight_agent(self) -> Dict[str, Any]:
        """Run insight agent"""
        return self.agents["insight_agent"].run()

    async def _run_venture_agent(self) -> Dict[str, Any]:
        """Run venture agent"""
        return self.agents["venture_agent"].run()

    async def run_continuous(self, interval_seconds: int = 300):
        """
        Run pipeline continuously

        Args:
            interval_seconds: Interval between runs
        """
        logger.info(f"Starting continuous pipeline (interval: {interval_seconds}s)...")

        while True:
            try:
                await self.run_pipeline(mode="full")
                logger.info(f"Waiting {interval_seconds}s until next run...")
                await asyncio.sleep(interval_seconds)

            except KeyboardInterrupt:
                logger.info("Pipeline stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous pipeline: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error


# Main execution
async def main():
    """Main execution function"""
    orchestrator = PipelineOrchestrator()

    # Check if continuous mode
    pipeline_config = orchestrator.config.get("pipeline", {})
    mode = pipeline_config.get("mode", "continuous")

    if mode == "continuous":
        interval = pipeline_config.get("interval_seconds", 300)
        await orchestrator.run_continuous(interval)
    else:
        # Single run
        stats = await orchestrator.run_pipeline(mode="full")
        print(f"Pipeline execution completed:")
        print(f"Duration: {stats.get('duration_seconds', 0):.2f}s")
        print(f"Results: {stats.get('results', {})}")


if __name__ == "__main__":
    asyncio.run(main())
