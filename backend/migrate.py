"""
NarrAI Database Migration Script.
Upgrades existing SQLite/PostgreSQL schema to include new auth columns/tables.
Safe to run multiple times (idempotent).

Usage:
    python migrate.py
"""
import sys
import os

# Ensure backend/ is importable
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

from sqlalchemy import inspect, text
from db.models import engine, Base


def run_migration():
    print("=== NarrAI Database Migration ===")
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"Existing tables: {existing_tables}")
    
    # 1. Create any missing tables (auth_accounts, token_blacklist, etc.)
    Base.metadata.create_all(engine)
    new_tables = inspect(engine).get_table_names()
    created = set(new_tables) - set(existing_tables)
    if created:
        print(f"Created new tables: {created}")
    
    # 2. Add missing columns to existing 'users' table
    if "users" in existing_tables:
        existing_columns = {col["name"] for col in inspector.get_columns("users")}
        print(f"Existing user columns: {existing_columns}")
        
        new_columns = {
            "email": "VARCHAR(255)",
            "name": "VARCHAR(100)",
            "avatar_url": "VARCHAR(500)",
            "updated_at": "DATETIME",
        }
        
        with engine.connect() as conn:
            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    try:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                        print(f"  Added column: users.{col_name} ({col_type})")
                    except Exception as e:
                        print(f"  Skip column users.{col_name}: {e}")
            
            # 3. Backfill email from username for existing users
            try:
                result = conn.execute(text(
                    "UPDATE users SET email = username WHERE email IS NULL"
                ))
                conn.commit()
                if result.rowcount > 0:
                    print(f"  Backfilled email for {result.rowcount} existing users")
            except Exception as e:
                print(f"  Email backfill note: {e}")
    
    print("\n=== Migration Complete ===")
    
    # Show summary
    final_inspector = inspect(engine)
    for table in final_inspector.get_table_names():
        cols = [c["name"] for c in final_inspector.get_columns(table)]
        print(f"  {table}: {cols}")


if __name__ == "__main__":
    run_migration()
