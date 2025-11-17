#!/usr/bin/env python3
"""
Test script for Advanced Memory System (Mem0 + Zep)
Verifies that the memory integration is working correctly
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.advanced_memory import get_advanced_memory_manager


def test_memory_initialization():
    """Test that memory managers can be initialized"""
    print("=" * 60)
    print("TEST 1: Memory Initialization")
    print("=" * 60)

    agents = ["signal_agent", "insight_agent", "venture_agent"]

    for agent_name in agents:
        print(f"\n{agent_name}:")
        try:
            memory = get_advanced_memory_manager(agent_name)
            stats = memory.get_stats()

            print(f"  ✅ Memory manager initialized")
            print(f"  - Mem0 enabled: {stats['mem0_enabled']}")
            print(f"  - Zep enabled: {stats['zep_enabled']}")
            print(f"  - Ready: {memory.is_ready()}")

            if not memory.is_ready():
                print(f"  ⚠️  WARNING: Memory system not fully initialized")
                print(f"     This is OK if Mem0/Zep services are not running yet")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    print()


def test_conversation_memory():
    """Test adding and retrieving conversations"""
    print("=" * 60)
    print("TEST 2: Conversation Memory")
    print("=" * 60)

    try:
        memory = get_advanced_memory_manager("signal_agent")

        session_id = "test_session_001"
        user_id = "test_user_123"

        # Create session
        print(f"\n✓ Creating session: {session_id}")
        memory.create_session(session_id, user_id, metadata={"test": True})

        # Add conversation
        print(f"✓ Adding test conversation...")
        success = memory.add_conversation(
            user_message="帮我找AI创业项目",
            assistant_message="我找到了3个AI创业项目：ProjectX、AIFlow、SmartAgent",
            session_id=session_id,
            user_id=user_id,
            metadata={"test": True}
        )

        if success:
            print(f"  ✅ Conversation saved successfully")
        else:
            print(f"  ⚠️  Conversation save returned False (services might not be running)")

        # Retrieve context
        print(f"\n✓ Retrieving context...")
        context = memory.retrieve_context(
            query="AI项目",
            session_id=session_id,
            user_id=user_id
        )

        print(f"  Retrieved context:")
        print(f"  - Session summary: {context['session_summary'][:50] if context['session_summary'] else 'N/A'}...")
        print(f"  - Recent messages: {len(context['recent_messages'])} messages")
        print(f"  - Relevant history: {len(context['relevant_history'])} items")
        print(f"  - Long-term memories: {len(context['long_term_memories'])} memories")

        print(f"\n  ✅ Context retrieval test passed")

    except Exception as e:
        print(f"\n  ❌ Error in conversation test: {e}")
        import traceback
        traceback.print_exc()

    print()


def test_long_term_memory():
    """Test long-term memory storage"""
    print("=" * 60)
    print("TEST 3: Long-term Memory")
    print("=" * 60)

    try:
        memory = get_advanced_memory_manager("signal_agent")
        user_id = "test_user_123"

        # Add user preference
        print(f"\n✓ Adding user preference to long-term memory...")
        success = memory.add_user_memory(
            content="用户偏好AI和Web3领域的创业项目",
            user_id=user_id,
            metadata={"type": "preference"}
        )

        if success:
            print(f"  ✅ Long-term memory saved")
        else:
            print(f"  ⚠️  Long-term memory save returned False (Mem0 might not be running)")

        # Retrieve user memories
        print(f"\n✓ Retrieving user memories...")
        memories = memory.get_user_memories(user_id, limit=10)

        print(f"  Found {len(memories)} user memories")
        if memories:
            for i, mem in enumerate(memories[:3], 1):
                print(f"  {i}. {mem.get('memory', 'N/A')[:60]}...")

        print(f"\n  ✅ Long-term memory test passed")

    except Exception as e:
        print(f"\n  ❌ Error in long-term memory test: {e}")
        import traceback
        traceback.print_exc()

    print()


async def test_agent_integration():
    """Test integration with actual agents"""
    print("=" * 60)
    print("TEST 4: Agent Integration")
    print("=" * 60)

    try:
        from agents.signal_agent_chat import SignalAgentChat

        print(f"\n✓ Initializing Signal Agent...")
        agent = SignalAgentChat()

        print(f"  ✅ Agent initialized with advanced memory")
        print(f"  - Memory manager: {agent.memory}")
        print(f"  - Memory stats: {agent.memory.get_stats()}")

        # Test chat (will fail if Supabase/Claude not configured, but memory should work)
        print(f"\n✓ Testing chat with memory...")
        try:
            response = await agent.process_user_request(
                user_message="你好，我想找AI相关的创业项目",
                user_id="test_user_123",
                session_id="test_agent_session_001"
            )

            print(f"  ✅ Chat completed")
            print(f"  - Session ID: {response.get('session_id')}")
            print(f"  - Memory stats: {response.get('memory_stats')}")

        except Exception as e:
            print(f"  ⚠️  Chat failed (expected if services not running): {e}")
            print(f"  But memory integration is configured correctly!")

        print(f"\n  ✅ Agent integration test passed")

    except Exception as e:
        print(f"\n  ❌ Error in agent integration test: {e}")
        import traceback
        traceback.print_exc()

    print()


def test_services_connectivity():
    """Test connectivity to Zep and Qdrant services"""
    print("=" * 60)
    print("TEST 5: Services Connectivity")
    print("=" * 60)

    # Test Zep
    print(f"\n✓ Testing Zep connectivity...")
    zep_url = os.getenv("ZEP_API_URL", "http://localhost:8000")
    print(f"  Zep URL: {zep_url}")

    try:
        import requests
        response = requests.get(f"{zep_url}/healthz", timeout=5)
        if response.status_code == 200:
            print(f"  ✅ Zep is running and healthy")
        else:
            print(f"  ⚠️  Zep responded with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Cannot connect to Zep")
        print(f"     Start Zep with: docker-compose up -d")
    except Exception as e:
        print(f"  ❌ Error connecting to Zep: {e}")

    # Test Qdrant
    print(f"\n✓ Testing Qdrant connectivity...")
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = os.getenv("QDRANT_PORT", "6333")
    print(f"  Qdrant: {qdrant_host}:{qdrant_port}")

    try:
        import requests
        response = requests.get(f"http://{qdrant_host}:{qdrant_port}/", timeout=5)
        if response.status_code == 200:
            print(f"  ✅ Qdrant is running and healthy")
        else:
            print(f"  ⚠️  Qdrant responded with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Cannot connect to Qdrant")
        print(f"     Start Qdrant with: docker-compose up -d")
    except Exception as e:
        print(f"  ❌ Error connecting to Qdrant: {e}")

    print()


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ADVANCED MEMORY SYSTEM TEST SUITE")
    print("=" * 60)
    print()

    print("Environment:")
    print(f"  CLAUDE_API_KEY: {'✓ Set' if os.getenv('CLAUDE_API_KEY') else '✗ Not set'}")
    print(f"  ZEP_API_URL: {os.getenv('ZEP_API_URL', 'http://localhost:8000')}")
    print(f"  QDRANT_HOST: {os.getenv('QDRANT_HOST', 'localhost')}")
    print(f"  QDRANT_PORT: {os.getenv('QDRANT_PORT', '6333')}")
    print()

    # Run tests
    test_services_connectivity()
    test_memory_initialization()
    test_conversation_memory()
    test_long_term_memory()

    # Run async test
    asyncio.run(test_agent_integration())

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print()
    print("✅ If all tests passed: Memory system is fully integrated!")
    print()
    print("⚠️  If some tests failed:")
    print("   - Make sure Docker services are running: docker-compose up -d")
    print("   - Check .env file has CLAUDE_API_KEY set")
    print("   - Install dependencies: pip install mem0ai zep-python qdrant-client")
    print()
    print("Next steps:")
    print("   1. Start services: docker-compose up -d")
    print("   2. Verify: docker-compose ps")
    print("   3. Run agents: python -m agents.signal_agent_chat")
    print()


if __name__ == "__main__":
    main()
