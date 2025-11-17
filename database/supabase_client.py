"""
Supabase Client for Multi-Agent Intelligence System
Provides database operations and real-time subscriptions
"""

import os
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
import json

from supabase import create_client, Client
from postgrest import APIResponse
from realtime import Channel

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Wrapper for Supabase client with convenience methods for the multi-agent system
    """

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        service_role_key: Optional[str] = None
    ):
        """
        Initialize Supabase client

        Args:
            url: Supabase project URL
            key: Supabase anon key
            service_role_key: Supabase service role key (for admin operations)
        """
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_KEY")
        self.service_role_key = service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

        # Create clients
        self.client: Client = create_client(self.url, self.key)
        self.admin_client: Client = create_client(self.url, self.service_role_key) if self.service_role_key else None

        # Realtime channels
        self.channels: Dict[str, Channel] = {}

        logger.info(f"Supabase client initialized for {self.url}")

    # ========================================================================
    # RAW ITEMS
    # ========================================================================

    def insert_raw_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a raw item from data ingestion"""
        try:
            response = self.client.table("raw_items").insert(item).execute()
            logger.debug(f"Inserted raw item from {item.get('source')}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error inserting raw item: {e}")
            raise

    def bulk_insert_raw_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk insert raw items"""
        try:
            response = self.client.table("raw_items").insert(items).execute()
            logger.info(f"Bulk inserted {len(items)} raw items")
            return response.data
        except Exception as e:
            logger.error(f"Error bulk inserting raw items: {e}")
            raise

    def get_unprocessed_raw_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get unprocessed raw items for classification"""
        try:
            response = (
                self.client.table("raw_items")
                .select("*")
                .eq("processed", False)
                .order("created_at", desc=False)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching unprocessed raw items: {e}")
            raise

    def mark_raw_item_processed(self, item_id: str) -> None:
        """Mark a raw item as processed"""
        try:
            self.client.table("raw_items").update({"processed": True}).eq("id", item_id).execute()
        except Exception as e:
            logger.error(f"Error marking item {item_id} as processed: {e}")
            raise

    # ========================================================================
    # CLASSIFIED ITEMS
    # ========================================================================

    def insert_classified_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a classified item"""
        try:
            response = self.client.table("classified_items").insert(item).execute()
            logger.debug(f"Inserted classified item: {item.get('category_l1')}/{item.get('category_l2')}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error inserting classified item: {e}")
            raise

    def get_classified_items(
        self,
        category_l1: Optional[str] = None,
        category_l2: Optional[str] = None,
        min_confidence: float = 0.6,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get classified items with optional filtering"""
        try:
            query = self.client.table("classified_items").select("*")

            if category_l1:
                query = query.eq("category_l1", category_l1)
            if category_l2:
                query = query.eq("category_l2", category_l2)

            query = query.gte("confidence", min_confidence)
            query = query.order("classified_at", desc=True).limit(limit)

            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching classified items: {e}")
            raise

    def get_recent_classified_items(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recently classified items for signal generation"""
        try:
            response = (
                self.client.table("classified_items")
                .select("*")
                .gte("classified_at", f"now() - interval '{hours} hours'")
                .order("classified_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching recent classified items: {e}")
            raise

    # ========================================================================
    # FOUNDERS
    # ========================================================================

    def upsert_founder(self, founder: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert founder information"""
        try:
            response = self.client.table("founders").upsert(founder).execute()
            logger.debug(f"Upserted founder: {founder.get('name')}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error upserting founder: {e}")
            raise

    def get_founder_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get founder by email"""
        try:
            response = self.client.table("founders").select("*").eq("email", email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching founder by email: {e}")
            raise

    def search_founders(self, ethnicity: Optional[str] = None, min_github_stars: int = 0) -> List[Dict[str, Any]]:
        """Search founders with filters"""
        try:
            query = self.client.table("founders").select("*")

            if ethnicity:
                query = query.eq("ethnicity", ethnicity)

            if min_github_stars > 0:
                query = query.gte("github_stars", min_github_stars)

            response = query.order("github_stars", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error searching founders: {e}")
            raise

    # ========================================================================
    # SIGNALS
    # ========================================================================

    def insert_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a generated signal"""
        try:
            response = self.client.table("signals").insert(signal).execute()
            logger.debug(f"Inserted signal: {signal.get('title')}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error inserting signal: {e}")
            raise

    def get_unpublished_signals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get unpublished signals"""
        try:
            response = (
                self.client.table("signals")
                .select("*")
                .eq("published", False)
                .order("signal_score", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching unpublished signals: {e}")
            raise

    def publish_signal(self, signal_id: str) -> None:
        """Mark a signal as published"""
        try:
            self.client.table("signals").update({
                "published": True,
                "published_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", signal_id).execute()
            logger.info(f"Published signal: {signal_id}")
        except Exception as e:
            logger.error(f"Error publishing signal: {e}")
            raise

    def get_published_signals_for_rss(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get published signals for RSS feed generation"""
        try:
            response = (
                self.client.table("signals")
                .select("*")
                .eq("published", True)
                .order("published_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching signals for RSS: {e}")
            raise

    # ========================================================================
    # INSIGHTS
    # ========================================================================

    def insert_insight(self, insight: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a generated insight"""
        try:
            response = self.client.table("insights").insert(insight).execute()
            logger.info(f"Inserted insight: {insight.get('title')}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error inserting insight: {e}")
            raise

    def get_recent_insights(self, insight_type: str = "weekly", limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent insights"""
        try:
            response = (
                self.client.table("insights")
                .select("*")
                .eq("insight_type", insight_type)
                .order("generated_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching recent insights: {e}")
            raise

    # ========================================================================
    # INVESTMENTS
    # ========================================================================

    def insert_investment(self, investment: Dict[str, Any]) -> Dict[str, Any]:
        """Insert investment intelligence"""
        try:
            response = self.client.table("investments").insert(investment).execute()
            logger.debug(f"Inserted investment: {investment.get('company_name')}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error inserting investment: {e}")
            raise

    def get_high_score_investments(self, min_score: float = 0.7, limit: int = 50) -> List[Dict[str, Any]]:
        """Get high-scoring investment opportunities"""
        try:
            response = (
                self.client.table("investments")
                .select("*")
                .gte("investability_score", min_score)
                .order("investability_score", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching high-score investments: {e}")
            raise

    def get_investments_by_founder_background(
        self,
        ethnicity: str,
        funding_stage: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get investments filtered by founder background"""
        try:
            # This requires JSONB querying
            query = self.client.table("investments").select("*")

            # Note: Supabase Python client JSONB querying syntax
            # May need adjustment based on actual JSONB structure
            query = query.filter("founder_backgrounds", "cs", json.dumps([{"ethnicity": ethnicity}]))

            if funding_stage:
                query = query.eq("funding_stage", funding_stage)

            response = query.order("investability_score", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching investments by founder background: {e}")
            raise

    # ========================================================================
    # AGENT STATUS & MONITORING
    # ========================================================================

    def update_agent_status(
        self,
        agent_name: str,
        status: str,
        processed_count: Optional[int] = None,
        error_message: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update agent status and heartbeat"""
        try:
            update_data = {
                "agent_name": agent_name,
                "status": status,
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                "last_run_timestamp": datetime.now(timezone.utc).isoformat()
            }

            if processed_count is not None:
                update_data["processed_count"] = processed_count

            if error_message:
                update_data["error_message"] = error_message
                update_data["error_count"] = self.client.table("agent_status").select("error_count").eq("agent_name", agent_name).execute().data[0].get("error_count", 0) + 1

            if payload:
                update_data["payload"] = payload

            self.client.table("agent_status").upsert(update_data).execute()
            logger.debug(f"Updated status for {agent_name}: {status}")
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")
            raise

    def get_agent_status(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get agent status (all or specific agent)"""
        try:
            query = self.client.table("agent_status").select("*")

            if agent_name:
                query = query.eq("agent_name", agent_name)

            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching agent status: {e}")
            raise

    def log_agent_activity(
        self,
        agent_name: str,
        log_level: str,
        message: str,
        operation: Optional[str] = None,
        item_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log agent activity"""
        try:
            log_entry = {
                "agent_name": agent_name,
                "log_level": log_level,
                "message": message,
                "operation": operation,
                "item_id": item_id,
                "metadata": metadata
            }
            self.client.table("agent_logs").insert(log_entry).execute()
        except Exception as e:
            logger.error(f"Error logging agent activity: {e}")

    # ========================================================================
    # ANALYTICS & REPORTING
    # ========================================================================

    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get overall pipeline metrics"""
        try:
            # Count items in each stage
            raw_count = self.client.table("raw_items").select("id", count="exact").execute().count
            classified_count = self.client.table("classified_items").select("id", count="exact").execute().count
            signals_count = self.client.table("signals").select("id", count="exact").execute().count
            insights_count = self.client.table("insights").select("id", count="exact").execute().count
            investments_count = self.client.table("investments").select("id", count="exact").execute().count

            return {
                "raw_items": raw_count,
                "classified_items": classified_count,
                "signals": signals_count,
                "insights": insights_count,
                "investments": investments_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching pipeline metrics: {e}")
            return {}

    def get_category_distribution(self) -> Dict[str, int]:
        """Get distribution of items across categories"""
        try:
            response = self.client.table("classified_items").select("category_l1, category_l2, category_l3").execute()
            distribution = {}
            for item in response.data:
                key = f"{item['category_l1']}/{item['category_l2']}/{item['category_l3']}"
                distribution[key] = distribution.get(key, 0) + 1
            return distribution
        except Exception as e:
            logger.error(f"Error fetching category distribution: {e}")
            return {}

    # ========================================================================
    # REALTIME SUBSCRIPTIONS
    # ========================================================================

    def subscribe_to_classified_items(self, callback: Callable) -> Channel:
        """Subscribe to new classified items via Realtime"""
        try:
            channel = self.client.channel("classified_items_channel")
            channel.on_postgres_changes(
                event="INSERT",
                schema="public",
                table="classified_items",
                callback=callback
            ).subscribe()

            self.channels["classified_items"] = channel
            logger.info("Subscribed to classified_items realtime updates")
            return channel
        except Exception as e:
            logger.error(f"Error subscribing to classified items: {e}")
            raise

    def subscribe_to_agent_status(self, callback: Callable) -> Channel:
        """Subscribe to agent status updates via Realtime"""
        try:
            channel = self.client.channel("agent_status_channel")
            channel.on_postgres_changes(
                event="UPDATE",
                schema="public",
                table="agent_status",
                callback=callback
            ).subscribe()

            self.channels["agent_status"] = channel
            logger.info("Subscribed to agent_status realtime updates")
            return channel
        except Exception as e:
            logger.error(f"Error subscribing to agent status: {e}")
            raise

    def unsubscribe_all(self) -> None:
        """Unsubscribe from all realtime channels"""
        for channel_name, channel in self.channels.items():
            try:
                channel.unsubscribe()
                logger.info(f"Unsubscribed from {channel_name}")
            except Exception as e:
                logger.error(f"Error unsubscribing from {channel_name}: {e}")

        self.channels.clear()

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def health_check(self) -> bool:
        """Check if Supabase connection is healthy"""
        try:
            response = self.client.table("agent_status").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Singleton instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get or create singleton Supabase client"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
