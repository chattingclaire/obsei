#!/usr/bin/env python3
"""
Simplified Setup Verification Script
Tests API keys without heavy dependencies
"""

import os
import sys
from pathlib import Path
import requests

# Load .env file manually
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_status(service: str, status: bool, message: str = ""):
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
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Hi"}]
        }
        response = requests.post("https://api.anthropic.com/v1/messages",
                                headers=headers, json=data, timeout=10)

        if response.status_code == 200:
            print_status("Claude API", True, "Valid API key")
            return True
        elif response.status_code == 401:
            print_status("Claude API", False, "Invalid API key")
            return False
        else:
            print_status("Claude API", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_status("Claude API", False, f"Error: {str(e)[:40]}")
        return False

def verify_supabase() -> bool:
    """Verify Supabase connection"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print_status("Supabase", False, "Credentials not set")
        return False

    try:
        # Try to access the REST API
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}"
        }
        response = requests.get(f"{url}/rest/v1/", headers=headers, timeout=10)

        if response.status_code in [200, 404]:  # 404 is OK, means API is accessible
            project_id = url.split('//')[1].split('.')[0]
            print_status("Supabase", True, f"Connected to {project_id}")
            return True
        else:
            print_status("Supabase", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_status("Supabase", False, f"Error: {str(e)[:40]}")
        return False

def verify_github() -> bool:
    """Verify GitHub token"""
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print_status("GitHub", False, "Token not set (optional)")
        return False

    try:
        headers = {"Authorization": f"token {token}"}
        response = requests.get("https://api.github.com/user",
                               headers=headers, timeout=10)

        if response.status_code == 200:
            user = response.json()
            print_status("GitHub", True, f"Authenticated as {user.get('login', 'unknown')}")
            return True
        else:
            print_status("GitHub", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_status("GitHub", False, f"Error: {str(e)[:40]}")
        return False

def verify_twitter() -> bool:
    """Verify Twitter/X bearer token"""
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

    if not bearer_token:
        print_status("Twitter/X", False, "Bearer token not set (optional)")
        return False

    try:
        headers = {"Authorization": f"Bearer {bearer_token}"}
        # Simple API call to verify token
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/recent?query=hello&max_results=10",
            headers=headers, timeout=10
        )

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
        print_status("Twitter/X", False, f"Error: {str(e)[:40]}")
        return False

def verify_producthunt() -> bool:
    """Verify ProductHunt token"""
    token = os.getenv("PRODUCTHUNT_TOKEN")

    if not token:
        print_status("ProductHunt", False, "Token not set (optional)")
        return False

    try:
        headers = {"Authorization": f"Bearer {token}"}
        query = {"query": "{viewer{id}}"}
        response = requests.post(
            "https://api.producthunt.com/v2/api/graphql",
            json=query, headers=headers, timeout=10
        )

        if response.status_code == 200:
            print_status("ProductHunt", True, "Token valid")
            return True
        else:
            print_status("ProductHunt", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_status("ProductHunt", False, f"Error: {str(e)[:40]}")
        return False

def check_file_structure() -> bool:
    """Check if all required files exist"""
    required_paths = [
        ("agents", "dir"),
        ("tools", "dir"),
        ("core", "dir"),
        ("database", "dir"),
        ("config", "dir"),
        ("database/schema.sql", "file"),
        ("config/settings.yaml", "file"),
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
    print("🔍 Multi-Agent AI Platform - Setup Verification (Simplified)")
    print("=" * 70)
    print()

    results = {}

    # Check file structure
    print(f"{Colors.BLUE}📁 File Structure{Colors.END}")
    results['files'] = check_file_structure()
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

    if required_ok and results['files']:
        print(f"{Colors.GREEN}✅ All required services are configured correctly!{Colors.END}")
        print(f"{Colors.GREEN}✅ {optional_count}/3 optional data sources are configured{Colors.END}")
        print()
        print("🎉 Your API keys are working!")
        print()
        print("📋 Next Steps:")
        print("   1. Set up database: python setup_database.py")
        print("   2. Install all dependencies: pip install -r requirements.txt")
        print("   3. Read the quick start: cat QUICK_START.md")
        print()
        return 0
    else:
        print(f"{Colors.RED}❌ Some required services are not configured{Colors.END}")
        print()
        if not results['claude']:
            print("💡 Check your CLAUDE_API_KEY in .env file")
        if not results['supabase']:
            print("💡 Check your SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
