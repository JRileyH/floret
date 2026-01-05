# Default services to show logs for during development
attach := "floret"

# ================================================================ #
# = Development ================================================== #
# ================================================================ #

add PACKAGE:
    #!/usr/bin/env bash
    set -e

    echo "📦 Installing latest version of {{PACKAGE}}..."

    # Get the latest version from first line: "package (version)"
    # Filter out Docker status messages and get only the version line
    LATEST_VERSION=$(docker-compose run --rm floret \
        pip index versions "{{PACKAGE}}" 2>&1 | grep "^{{PACKAGE}}" | head -n 1 | sed 's/.*(\(.*\)).*/\1/' | tr -d '\r\n ')

    if [ -z "$LATEST_VERSION" ] || [[ "$LATEST_VERSION" == *"Container"* ]]; then
        echo "❌ Could not determine latest version of {{PACKAGE}}"
        exit 1
    fi

    echo "📝 Adding {{PACKAGE}}==$LATEST_VERSION to requirements.in..."

    # Add to requirements.in under Django Extensions section
    if ! grep -q "^{{PACKAGE}}==" requirements.in; then
        sed '/# Django Extensions/,/^$/s|^$|{{PACKAGE}}=='"$LATEST_VERSION"'\n|' requirements.in > requirements.in.tmp && mv requirements.in.tmp requirements.in
        echo "✅ Added {{PACKAGE}}==$LATEST_VERSION"
    else
        echo "⚠️  {{PACKAGE}} already exists in requirements.in, updating version..."
        sed 's|^{{PACKAGE}}==.*|{{PACKAGE}}=='"$LATEST_VERSION"'|' requirements.in > requirements.in.tmp && mv requirements.in.tmp requirements.in
    fi

    # Compile requirements.in to requirements.txt
    echo "🔨 Compiling requirements.in to requirements.txt..."
    docker-compose run --rm floret \
        uv pip compile requirements.in -o requirements.txt

    # Rebuild Docker image
    echo "🐳 Rebuilding Docker image..."
    docker-compose build floret

    # Refresh .venv if it exists
    if [ -d ".venv" ]; then
        echo "🔄 Refreshing .venv with updated requirements..."
        if command -v uv &> /dev/null; then
            uv pip sync requirements.txt
        elif [ -f ".venv/bin/pip" ]; then
            .venv/bin/pip install -r requirements.txt
        else
            echo "⚠️  Neither uv nor .venv/bin/pip found, skipping .venv refresh"
        fi
        echo "✅ .venv refreshed"
    else
        echo "ℹ️  No .venv directory found, skipping local environment refresh"
    fi

    echo "✨ Package {{PACKAGE}} added successfully!"

remove PACKAGE:
    #!/usr/bin/env bash
    set -e

    echo "🗑️  Removing {{PACKAGE}} from requirements.in..."

    # Check if package exists
    if ! grep -q "^{{PACKAGE}}==" requirements.in; then
        echo "⚠️  {{PACKAGE}} not found in requirements.in"
        exit 1
    fi

    # Remove the package line from requirements.in
    sed '/^{{PACKAGE}}==/d' requirements.in > requirements.in.tmp && mv requirements.in.tmp requirements.in
    echo "✅ Removed {{PACKAGE}} from requirements.in"

    # Compile requirements.in to requirements.txt
    echo "🔨 Compiling requirements.in to requirements.txt..."
    docker-compose run --rm floret \
        uv pip compile requirements.in -o requirements.txt

    # Rebuild Docker image
    echo "🐳 Rebuilding Docker image..."
    docker-compose build floret

    # Refresh .venv if it exists
    if [ -d ".venv" ]; then
        echo "🔄 Refreshing .venv with updated requirements..."
        if command -v uv &> /dev/null; then
            uv pip sync requirements.txt
        elif [ -f ".venv/bin/pip" ]; then
            .venv/bin/pip install -r requirements.txt
        else
            echo "⚠️  Neither uv nor .venv/bin/pip found, skipping .venv refresh"
        fi
        echo "✅ .venv refreshed"
    else
        echo "ℹ️  No .venv directory found, skipping local environment refresh"
    fi

    echo "✨ Package {{PACKAGE}} removed successfully!"
    

migrate:
    docker-compose run --rm floret python manage.py makemigrations

start *SERVICES:
    docker-compose -f docker-compose.yml up --attach {{ if SERVICES == "" { attach } else { SERVICES } }}

nuke:
    docker ps -a --filter "name=floret" -q | xargs -r docker stop > /dev/null 2>&1 || true
    docker ps -a --filter "name=floret" -q | xargs -r docker rm > /dev/null 2>&1 || true
    docker images --filter "reference=floret*" -q | xargs -r docker rmi > /dev/null 2>&1 || true
    docker volume ls --filter "name=floret_" -q | xargs -r docker volume rm > /dev/null 2>&1 || true
    rm -rf theme/node_modules theme/static/dist > /dev/null 2>&1 || true

# ================================================================ #
# = Linting & Formatting ========================================= #
# ================================================================ #
lint: lint-py lint-html lint-types

lint-py:
    docker exec floret python -m ruff check .

lint-html:
    docker exec floret sh -c "cd /code && djlint **/templates --check"

lint-types:
    docker exec floret basedpyright .

fix: fix-py fix-html

fix-py:
    docker exec floret python -m ruff check --fix .

fix-html:
    docker exec floret sh -c "cd /code && djlint **/templates --reformat"

format:
    docker exec floret python -m ruff format .

check:
    docker exec floret python -m ruff format --check .

# ================================================================ #
# = Tests & Debugging ============================================ #
# ================================================================ #

test:
    docker-compose -f docker-compose.test.yml run --rm floret-test-web test
    docker compose -f docker-compose.test.yml -p local_test_run down

shell:
    docker exec -it floret python manage.py shell_plus

fixtures:
    docker exec floret python manage.py load_fixtures

