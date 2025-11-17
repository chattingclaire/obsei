#!/usr/bin/env python3
"""
Setup Verification Script for Multi-Agent AI Platform
Tests all API keys and connections
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from supabase import create_client
import requests

# Load environment variables
load_dotenv()

class Colors:
    """Terminal colors"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_status(service: str, status: bool, message: str = ""):
    """Print formatted status"""
    icon = "✅" if status else "❌"
    color = Colors.GREEN if status else Colors.RED
    status_text = "OK" if status else "FAILED"
    print(f"   {icon} {service:<25} [{color}{status_text}{Colors.END}] {message}")

def verify_claude_api() -> bool:
    """Verify Claude API key"""
    api_key = os.getenv("CLAUDE_API_KEY")

    if not api_key:
        print_status("Claude API", False, "API key not set")
        return False

    try:
        client = anthropic.Anthropic(api_key=api_key)
        # Test with a simple message
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print_status("Claude API", True, f"Model: {message.model}")
        return True
    except anthropic.AuthenticationError:
        print_status("Claude API", False, "Invalid API key")
        return False
    except Exception as e:
        print_status("Claude API", False, f"Error: {str(e)[:50]}")
        return False

def verify_supabase() -> bool:
    """Verify Supabase connection"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print_status("Supabase", False, "Credentials not set")
        return False

    try:
        client = create_client(url, key)
        # Try to list tables
        result = client.table('agent_status').select("*").limit(1).execute()
        print_status("Supabase", True, f"Connected to {url.split('//')[1].split('.')[0]}")
        return True
    except Exception as e:
        error_msg = str(e)
        if "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
            print_status("Supabase", False, "Tables not created yet - run setup_database.py")
        else:
            print_status("Supabase", False, f"Error: {str(e)[:50]}")
        return False

def verify_github() -> bool:
    """Verify GitHub token"""
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print_status("GitHub", False, "Token not set (optional)")
        return False

    try:
        headers = {"Authorization": f"token {token}"}
        response = requests.get("https://api.github.com/user", headers=headers)

        if response.status_code == 200:
            user = response.json()
            print_status("GitHub", True, f"Authenticated as {user.get('login', 'unknown')}")
            return True
        else:
            print_status("GitHub", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_status("GitHub", False, f"Error: {str(e)[:50]}")
        return False

def verify_twitter() -> bool:
    """Verify Twitter/X bearer token"""
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

    if not bearer_token:
        print_status("Twitter/X", False, "Bearer token not set (optional)")
        return False

    try:
        headers = {"Authorization": f"Bearer {bearer_token}"}
        response = requests.get("https://api.twitter.com/2/tweets/search/recent?query=hello&max_results=10", headers=headers)

        if response.status_code == 200:
            print_status("Twitter/X", True, "Bearer token valid")
            return True
        elif response.status_code == 401:
            print_status("Twitter/X", False, "Invalid bearer token")
            return False
        else:
            print_status("Twitter/X", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_status("Twitter/X", False, f"Error: {str(e)[:50]}")
        return False

def verify_producthunt() -> bool:
    """Verify ProductHunt token"""
    token = os.getenv("PRODUCTHUNT_TOKEN")

    if not token:
        print_status("ProductHunt", False, "Token not set (optional)")
        return False

    try:
        headers = {"Authorization": f"Bearer {token}"}
        # Simple GraphQL query to verify token
        query = {"query": "{viewer{id}}"}
        response = requests.post("https://api.producthunt.com/v2/api/graphql", json=query, headers=headers)

        if response.status_code == 200:
            print_status("ProductHunt", True, "Token valid")
            return True
        else:
            print_status("ProductHunt", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_status("ProductHunt", False, f"Error: {str(e)[:50]}")
        return False

def verify_dependencies() -> bool:
    """Verify Python dependencies are installed"""
    required = [
        ('anthropic', 'Anthropic SDK'),
        ('supabase', 'Supabase client'),
        ('requests', 'Requests library'),
        ('yaml', 'PyYAML'),
        ('dotenv', 'python-dotenv'),
    ]

    all_installed = True
    for module, name in required:
        try:
            __import__(module)
            print_status(name, True, "Installed")
        except ImportError:
            print_status(name, False, "Not installed")
            all_installed = False

    return all_installed

def check_file_structure() -> bool:
    """Check if all required directories and files exist"""
    required_paths = [
        ("agents", "dir"),
        ("tools", "dir"),
        ("core", "dir"),
        ("database", "dir"),
        ("config", "dir"),
        ("database/schema.sql", "file"),
        ("config/settings.yaml", "file"),
        ("config/agent_tools.yaml", "file"),
    ]

    all_exist = True
    for path, path_type in required_paths:
        full_path = Path(__file__).parent / path
        exists = full_path.exists()

        if path_type == "dir":
            exists = exists and full_path.is_dir()
        else:
            exists = exists and full_path.is_file()

        print_status(f"Path: {path}", exists)
        if not exists:
            all_exist = False

    return all_exist

def main():
    """Main verification function"""
    print("=" * 70)
    print("🔍 Multi-Agent AI Platform - Setup Verification")
    print("=" * 70)
    print()

    results = {}

    # Check file structure
    print(f"{Colors.BLUE}📁 File Structure{Colors.END}")
    results['files'] = check_file_structure()
    print()

    # Check dependencies
    print(f"{Colors.BLUE}📦 Python Dependencies{Colors.END}")
    results['dependencies'] = verify_dependencies()
    print()

    # Check required services
    print(f"{Colors.BLUE}🔑 Required Services{Colors.END}")
    results['claude'] = verify_claude_api()
    results['supabase'] = verify_supabase()
    print()

    # Check optional services
    print(f"{Colors.BLUE}🔌 Optional Data Sources{Colors.END}")
    results['github'] = verify_github()
    results['twitter'] = verify_twitter()
    results['producthunt'] = verify_producthunt()
    print()

    # Summary
    print("=" * 70)
    print(f"{Colors.BLUE}📊 Summary{Colors.END}")
    print("=" * 70)

    required_ok = results['claude'] and results['supabase']
    optional_count = sum([results['github'], results['twitter'], results['producthunt']])

    if required_ok and results['files'] and results['dependencies']:
        print(f"{Colors.GREEN}✅ All required services are configured correctly!{Colors.END}")
        print(f"{Colors.GREEN}✅ {optional_count}/3 optional data sources are configured{Colors.END}")
        print()
        print("🎉 You're ready to run the system!")
        print()
        print("Next steps:")
        print("   1. Start the backend:  cd dashboard/backend && uvicorn main:app --reload")
        print("   2. Start the frontend: cd dashboard/frontend && npm run dev")
        print("   3. Start agents:       python pipeline_orchestrator.py")
        print()
        return 0
    else:
        print(f"{Colors.RED}❌ Some required services are not configured properly{Colors.END}")
        print()
        print("Please fix the issues above and run this script again.")
        print()

        if not results['supabase']:
            print("💡 Tip: Run 'python setup_database.py' to set up the database")

        if not results['dependencies']:
            print("💡 Tip: Run 'pip install -r requirements.txt' to install dependencies")

        return 1

if __name__ == "__main__":
    sys.exit(main())
