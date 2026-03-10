#!/usr/bin/env python
"""
Setup script for A92.2 Inspection App
Automates database setup, migrations, and template import
"""
import os
import sys
import subprocess
import getpass


def run_command(command, description, check=True):
    """Run a shell command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")

    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        else:
            result = subprocess.run(command, check=check, capture_output=True, text=True)

        if result.stdout:
            print(result.stdout)
        if result.stderr and not check:
            print(result.stderr)

        print(f"✅ {description} - COMPLETED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def check_postgres():
    """Check if PostgreSQL is accessible"""
    print("\n🔍 Checking PostgreSQL availability...")

    try:
        result = subprocess.run(
            ['psql', '--version'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print(f"✅ PostgreSQL found: {result.stdout.strip()}")
            return True
        else:
            print("⚠️  PostgreSQL command line tools not found in PATH")
            return False
    except FileNotFoundError:
        print("⚠️  PostgreSQL command line tools not found")
        return False


def create_database():
    """Create the PostgreSQL database"""
    print("\n📊 Database Setup")
    print("-" * 60)

    db_name = os.getenv('DB_NAME', os.getenv('DATABASE_NAME', 'inspectionapp'))
    db_user = os.getenv('DB_USER', os.getenv('DATABASE_USER', 'inspectionapp'))
    db_password = os.getenv('DB_PASSWORD', os.getenv('DATABASE_PASSWORD', 'postgres'))
    db_host = os.getenv('DB_HOST', os.getenv('DATABASE_HOST', 'localhost'))
    db_port = os.getenv('DB_PORT', os.getenv('DATABASE_PORT', '5432'))

    print(f"Database: {db_name}")
    print(f"User: {db_user}")
    print(f"Host: {db_host}:{db_port}")

    # Check if database already exists
    check_cmd = f'psql -h {db_host} -p {db_port} -U {db_user} -lqt'

    # Try to create database
    print(f"\n🔧 Attempting to create database '{db_name}'...")

    # Set password environment variable for psql
    env = os.environ.copy()
    env['PGPASSWORD'] = db_password

    # Create database command
    create_cmd = [
        'psql',
        '-h', db_host,
        '-p', db_port,
        '-U', db_user,
        '-c', f'CREATE DATABASE {db_name};'
    ]

    try:
        result = subprocess.run(
            create_cmd,
            env=env,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            print(f"✅ Database '{db_name}' created successfully")
            return True
        elif 'already exists' in result.stderr:
            print(f"ℹ️  Database '{db_name}' already exists")
            return True
        else:
            print(f"⚠️  Could not create database automatically")
            print(f"Error: {result.stderr}")
            print(f"\nPlease create the database manually:")
            print(f"  1. Open PostgreSQL command line or pgAdmin")
            print(f"  2. Run: CREATE DATABASE {db_name};")

            response = input("\nHave you created the database manually? (y/n): ")
            return response.lower() == 'y'

    except FileNotFoundError:
        print("⚠️  PostgreSQL tools not found. Please create database manually.")
        print(f"\nPlease create the database manually:")
        print(f"  1. Open PostgreSQL command line or pgAdmin")
        print(f"  2. Run: CREATE DATABASE {db_name};")

        response = input("\nHave you created the database manually? (y/n): ")
        return response.lower() == 'y'


def main():
    """Main setup function"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         A92.2 Inspection App - Setup Script              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Error: manage.py not found!")
        print("Please run this script from the project root directory.")
        sys.exit(1)

    # Check if .env exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found")
        if os.path.exists('.env.example'):
            print("📝 Copying .env.example to .env")
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file")
            print("⚠️  Please edit .env with your database credentials before continuing")

            response = input("\nContinue with setup? (y/n): ")
            if response.lower() != 'y':
                print("Setup cancelled.")
                sys.exit(0)
        else:
            print("❌ No .env.example found either!")
            sys.exit(1)

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
    except ImportError:
        print("⚠️  python-dotenv not installed, using defaults")

    # Step 1: Check Python version
    print(f"\n🐍 Python Version: {sys.version}")

    # Step 2: Install dependencies
    print("\n" + "="*60)
    response = input("📦 Install/upgrade dependencies from requirements.txt? (y/n): ")
    if response.lower() == 'y':
        if not run_command(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            "Installing dependencies"
        ):
            print("⚠️  Dependency installation had issues, but continuing...")

    # Step 3: PostgreSQL check
    postgres_available = check_postgres()

    # Step 4: Create database
    print("\n" + "="*60)
    response = input("📊 Create/check PostgreSQL database? (y/n): ")
    if response.lower() == 'y':
        if not create_database():
            print("\n❌ Database setup failed. Please create it manually and re-run this script.")
            sys.exit(1)

    # Step 5: Run makemigrations
    if not run_command(
        [sys.executable, 'manage.py', 'makemigrations'],
        "Creating migrations"
    ):
        print("❌ Failed to create migrations")
        sys.exit(1)

    # Step 6: Run migrate
    if not run_command(
        [sys.executable, 'manage.py', 'migrate'],
        "Running migrations"
    ):
        print("❌ Failed to run migrations")
        sys.exit(1)

    # Step 7: Create superuser
    print("\n" + "="*60)
    response = input("👤 Create superuser account? (y/n): ")
    if response.lower() == 'y':
        print("\n📝 Please enter superuser credentials:")
        run_command(
            [sys.executable, 'manage.py', 'createsuperuser'],
            "Creating superuser",
            check=False
        )

    # Step 8: Import templates
    print("\n" + "="*60)
    response = input("📋 Import A92.2 inspection templates? (y/n): ")
    if response.lower() == 'y':
        templates = [
            'periodic_a922.json',
            'cat_ab.json',
            'cat_cde.json',
            'uppercontrools.json',
            'liners.json',
            'ladders.json',
            'chassis.json',
            'load_test_structural.json'
        ]

        for template_file in templates:
            if os.path.exists(template_file):
                run_command(
                    [sys.executable, 'manage.py', 'import_new_template', template_file],
                    f"Importing {template_file}",
                    check=False
                )
            else:
                print(f"⚠️  {template_file} not found, skipping...")

    # Step 9: Create media directories
    print("\n" + "="*60)
    print("📁 Creating media directories...")
    os.makedirs('media/defect_photos', exist_ok=True)
    os.makedirs('media/generated_docs', exist_ok=True)
    print("✅ Media directories created")

    # Final summary
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║                    ✅ SETUP COMPLETE!                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

🚀 To start the development server, run:

    python manage.py runserver

📱 Then open your browser to:

    http://localhost:8000

🔑 Login with the superuser credentials you created.

📚 Additional commands:

    python manage.py createsuperuser    # Create additional users
    python manage.py collectstatic      # Collect static files (production)
    python manage.py import_a92_templates  # Re-import templates

💡 Tip: Check README.md for detailed usage instructions.
    """)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
