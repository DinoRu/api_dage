#!/bin/bash
set -e

echo "🚀 Starting application entrypoint..."

# Function to wait for database
wait_for_db() {
    echo "⏳ Waiting for database..."
    python << END
import sys
import time
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings

async def check_db():
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            engine = create_async_engine(settings.DATABASE_URL, echo=False)
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
            await engine.dispose()
            print("✅ Database is ready!")
            return True
        except Exception as e:
            print(f"⏳ Attempt {i+1}/{max_retries}: Database not ready yet... ({e})")
            time.sleep(retry_interval)
    
    print("❌ Database connection failed after all retries")
    sys.exit(1)

asyncio.run(check_db())
END
}

# Function to run migrations
run_migrations() {
    echo "🔄 Running database migrations..."
    alembic upgrade head
    echo "✅ Migrations completed"
}

# Function to create superuser
create_superuser() {
    if [ "$CREATE_SUPERUSER" = "true" ]; then
        echo "👤 Creating superuser..."
        python << END
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.auth import auth_service

async def create_admin():
    async with AsyncSessionLocal() as db:
        await auth_service.ensure_superuser_exists(db)

asyncio.run(create_admin())
END
        echo "✅ Superuser check completed"
    fi
}

# Main execution
main() {
    wait_for_db
    run_migrations
    create_superuser
    
    echo "🎉 Application ready to start!"
    echo "📝 Command: $@"
    
    # Execute the main command
    exec "$@"
}

main "$@"