#!/usr/bin/env python
"""
Quick script to check PostgreSQL connection
"""
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed, using defaults")

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed!")
    print("Install it with: pip install psycopg2-binary")
    sys.exit(1)

# Get database credentials
db_name = os.getenv('DATABASE_NAME', 'inspection_db')
db_user = os.getenv('DATABASE_USER', 'postgres')
db_password = os.getenv('DATABASE_PASSWORD', 'postgres')
db_host = os.getenv('DATABASE_HOST', 'localhost')
db_port = os.getenv('DATABASE_PORT', '5432')

print("="*60)
print("PostgreSQL Connection Test")
print("="*60)
print(f"Database: {db_name}")
print(f"User: {db_user}")
print(f"Host: {db_host}:{db_port}")
print("="*60)

try:
    print("\n🔄 Attempting to connect...")
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )

    print("✅ PostgreSQL connection successful!")

    # Test query
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"\n📊 PostgreSQL Version:")
    print(f"   {version}")

    cursor.close()
    conn.close()

    print("\n✅ All checks passed! You're ready to run migrations.")
    print("\nNext steps:")
    print("  1. python manage.py migrate")
    print("  2. python manage.py createsuperuser")
    print("  3. python manage.py import_a92_templates")
    print("  4. python manage.py runserver")

except psycopg2.OperationalError as e:
    print(f"\n❌ Connection failed!")
    print(f"\nError: {e}")
    print("\n🔧 Troubleshooting:")
    print("  1. Is PostgreSQL installed?")
    print("  2. Is PostgreSQL service running?")
    print("     Windows: net start postgresql-x64-18")
    print("     Linux: sudo systemctl start postgresql")
    print("     macOS: brew services start postgresql")
    print("  3. Is the database created?")
    print(f"     createdb {db_name}")
    print("  4. Are the credentials in .env correct?")
    print("\n📖 See INSTALL_POSTGRES.md for detailed instructions")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
