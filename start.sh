#!/bin/sh

#!/bin/sh

echo "Running in $APP_ENV mode..."
echo "print PWD: $PWD"

# Autogenerate migration and remove if empty
alembic -c app/alembic.ini revision --autogenerate -m "Auto migration"
LATEST_MIGRATION=$(ls -t app/migrations/versions/*.py | head -1)
if grep -q "pass" "$LATEST_MIGRATION"; then
  echo "No changes detected, removing empty migration: $LATEST_MIGRATION"
  rm "$LATEST_MIGRATION"
fi

# Always apply all available migrations
alembic -c app/alembic.ini upgrade head

# Start app...

if [ "$APP_ENV" = "dev" ]; then
    echo "Starting in development mode..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
else
    echo "Starting in production mode..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000
fi