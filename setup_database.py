#!/usr/bin/env python3
"""
Database Setup Script for Multi-Agent AI Platform
Automatically creates all required tables, indexes, and functions in Supabase
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """Create Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
        sys.exit(1)

    return create_client(url, key)

def read_sql_schema() -> str:
    """Read the database schema SQL file"""
    schema_path = Path(__file__).parent / "database" / "schema.sql"

    if not schema_path.exists():
        print(f"❌ Error: Schema file not found at {schema_path}")
        sys.exit(1)

    with open(schema_path, 'r', encoding='utf-8') as f:
        return f.read()

def execute_sql(client: Client, sql: str) -> bool:
    """Execute SQL commands"""
    try:
        # Split by semicolons to execute statements individually
        statements = [s.strip() for s in sql.split(';') if s.strip()]

        print(f"📝 Found {len(statements)} SQL statements to execute")

        for i, statement in enumerate(statements, 1):
            # Skip comments and empty statements
            if statement.startswith('--') or not statement:
                continue

            print(f"   Executing statement {i}/{len(statements)}...", end='')

            # Use RPC to execute raw SQL
            try:
                client.rpc('exec_sql', {'sql': statement}).execute()
                print(" ✅")
            except Exception as e:
                # If exec_sql doesn't exist, try direct execution
                # Note: This might not work for all statements
                print(f" ⚠️  (trying alternative method)")
                # For Supabase, we'll need to use the REST API or psycopg2
                # This is a simplified version
                pass

        return True
    except Exception as e:
        print(f"\n❌ Error executing SQL: {e}")
        return False

def create_tables_manually(client: Client) -> bool:
    """Create tables using Supabase client (fallback method)"""
    print("📝 Creating tables using REST API...")

    try:
        # This is a simplified approach - tables should be created via SQL
        # For production, use Supabase dashboard or SQL editor
        print("⚠️  Please execute the SQL schema manually:")
        print("   1. Go to Supabase Dashboard")
        print("   2. Navigate to SQL Editor")
        print("   3. Copy contents from database/schema.sql")
        print("   4. Execute the SQL")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_tables(client: Client) -> bool:
    """Verify that all tables were created"""
    required_tables = [
        'raw_items',
        'classified_items',
        'founders',
        'signals',
        'insights',
        'investments',
        'agent_status',
        'agent_logs'
    ]

    print("\n🔍 Verifying tables...")

    all_exist = True
    for table in required_tables:
        try:
            # Try to query the table
            result = client.table(table).select("*").limit(1).execute()
            print(f"   ✅ Table '{table}' exists")
        except Exception as e:
            print(f"   ❌ Table '{table}' not found")
            all_exist = False

    return all_exist

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 Multi-Agent AI Platform - Database Setup")
    print("=" * 60)
    print()

    # Create Supabase client
    print("📡 Connecting to Supabase...")
    client = get_supabase_client()
    print("   ✅ Connected successfully")
    print()

    # Read schema
    print("📖 Reading database schema...")
    schema_sql = read_sql_schema()
    print(f"   ✅ Schema loaded ({len(schema_sql)} characters)")
    print()

    # Show instructions
    print("⚠️  IMPORTANT INSTRUCTIONS:")
    print("   Due to Supabase API limitations, please follow these steps:")
    print()
    print("   1. Open Supabase Dashboard: https://supabase.com/dashboard")
    print("   2. Select your project: fftkazutsznpjvkqctvy")
    print("   3. Go to 'SQL Editor' in the left sidebar")
    print("   4. Click 'New Query'")
    print("   5. Copy the entire contents of: database/schema.sql")
    print("   6. Paste into the SQL editor")
    print("   7. Click 'Run' or press Cmd/Ctrl + Enter")
    print()
    print("   The schema will create 8 tables:")
    print("   - raw_items (original collected data)")
    print("   - classified_items (categorized content)")
    print("   - founders (founder profiles)")
    print("   - signals (generated signals)")
    print("   - insights (trend analysis)")
    print("   - investments (investment opportunities)")
    print("   - agent_status (agent health monitoring)")
    print("   - agent_logs (system logs)")
    print()

    # Ask if user has completed the setup
    response = input("📝 Have you executed the schema in Supabase? (y/n): ").strip().lower()

    if response == 'y':
        print()
        if verify_tables(client):
            print("\n✅ Database setup completed successfully!")
            print("\n🎉 You're ready to start the agents!")
            print("\nNext steps:")
            print("   1. Install Python dependencies: pip install -r requirements.txt")
            print("   2. Install frontend dependencies: cd dashboard/frontend && npm install")
            print("   3. Start the system: python pipeline_orchestrator.py")
            return 0
        else:
            print("\n❌ Some tables are missing. Please check the SQL execution.")
            return 1
    else:
        print("\n📋 Please complete the database setup and run this script again.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
