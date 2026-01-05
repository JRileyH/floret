#!/bin/bash
# ==============================================================================
# VPS Deployment Script for Floret
# ==============================================================================
# This script is executed on the VPS server by GitHub Actions during deployment.
# It handles:
# - Running database migrations
# - Starting services with docker-compose
# - Health checks and verification
#
# Prerequisites:
# - .env.prod must exist (created by GitHub Actions)
#
# Usage: ./deploy.sh
# ==============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

APP_NAME="floret"
DEPLOY_DIR="/home/riggy/web/${APP_NAME}"

echo "🚀 Starting deployment of ${APP_NAME}"
echo "📁 Deployment directory: ${DEPLOY_DIR}"

# Navigate to deployment directory
cd "${DEPLOY_DIR}"

# ==============================================================================
# Environment Configuration
# ==============================================================================
echo "⚙️  Environment file status:"
if [ -f .env.prod ]; then
    echo "✅ .env.prod exists"
else
    echo "❌ ERROR: .env.prod missing"
    echo "The environment file should be created by GitHub Actions"
    exit 1
fi

# ==============================================================================
# Database Migrations
# ==============================================================================
echo "🗄️  Running database migrations..."
if ! docker-compose -f docker-compose.prod.yml run --rm floret migrate 2>&1; then
    echo "❌ ERROR: Database migrations failed"
    echo "Recent migration logs:"
    docker-compose -f docker-compose.prod.yml logs --tail=50 floret || true
    exit 1
fi
echo "✅ Migrations completed successfully"

# ==============================================================================
# Deploy Services
# ==============================================================================
echo "🐳 Starting services with docker-compose..."
if ! docker-compose -f docker-compose.prod.yml up -d --force-recreate 2>&1; then
    echo "❌ ERROR: Failed to start services"
    echo "Container status:"
    docker-compose -f docker-compose.prod.yml ps || true
    echo "Recent logs:"
    docker-compose -f docker-compose.prod.yml logs --tail=100 || true
    exit 1
fi
echo "✅ Services started successfully"

# ==============================================================================
# Health Check
# ==============================================================================
echo "🏥 Waiting for services to be healthy..."
sleep 10

# Check if web container is running
echo "🔍 Checking web container..."
if docker ps --filter "name=^${APP_NAME}$" --format "{{.Names}}" | grep -q "^${APP_NAME}$"; then
    echo "✅ Web container is running"

    # Show container details
    echo "Container details:"
    docker ps --filter "name=^${APP_NAME}$" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "❌ ERROR: Web container failed to start"
    echo ""
    echo "📊 All containers status:"
    docker-compose -f docker-compose.prod.yml ps || true
    echo ""
    echo "📋 Recent application logs:"
    docker-compose -f docker-compose.prod.yml logs --tail=100 floret || true
    echo ""
    echo "📋 Database logs:"
    docker-compose -f docker-compose.prod.yml logs --tail=50 floret-db || true
    echo ""
    echo "📋 Redis logs:"
    docker-compose -f docker-compose.prod.yml logs --tail=50 floret-cache || true
    exit 1
fi

# Check if database is healthy
echo "🔍 Checking database..."
if docker ps | grep -q "${APP_NAME}-db"; then
    echo "✅ Database container is running"
    if docker ps | grep "${APP_NAME}-db" | grep -q "healthy"; then
        echo "✅ Database is healthy"
    else
        echo "⚠️  Database health check pending"
    fi
else
    echo "❌ WARNING: Database container not running"
    docker-compose -f docker-compose.prod.yml logs --tail=50 floret-db || true
fi

# Check Redis
echo "🔍 Checking Redis..."
if docker ps | grep -q "${APP_NAME}-cache"; then
    echo "✅ Redis container is running"
    if docker ps | grep "${APP_NAME}-cache" | grep -q "healthy"; then
        echo "✅ Redis is healthy"
    else
        echo "⚠️  Redis health check pending"
    fi
else
    echo "❌ WARNING: Redis container not running"
    docker-compose -f docker-compose.prod.yml logs --tail=50 floret-cache || true
fi

# ==============================================================================
# Cleanup
# ==============================================================================
echo ""
echo "🧹 Cleaning up old Docker images..."
if docker image prune -f 2>&1; then
    echo "✅ Cleanup completed"
else
    echo "⚠️  Cleanup encountered issues (non-critical)"
fi

echo ""
echo "✅ Deployment complete!"
echo "🌐 Application should be available at: https://${APP_NAME}.unlaunched.dev"
echo "📍 Deployment directory: ${DEPLOY_DIR}"

# Show running containers
echo ""
echo "📊 Running containers:"
docker-compose -f docker-compose.prod.yml ps

# Show recent logs
echo ""
echo "📋 Recent application logs (last 10 lines):"
docker-compose -f docker-compose.prod.yml logs --tail=10 floret 2>&1 || echo "Could not fetch logs"
