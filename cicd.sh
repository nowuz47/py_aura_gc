#!/bin/bash
# One-click CI/CD deployment script for AuraGC

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEELS_DIR="$PROJECT_ROOT/wheels"
COMPOSE_DIR="$PROJECT_ROOT/auragc-visualizer/infra"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    log_info "All requirements met"
}

cleanup() {
    if [ "$1" == "--clean" ]; then
        log_warn "Cleaning up previous builds..."
        cd "$COMPOSE_DIR"
        docker-compose down -v 2>/dev/null || docker compose down -v 2>/dev/null || true
        rm -rf "$WHEELS_DIR"/*.whl 2>/dev/null || true
        log_info "Cleanup complete"
    fi
}

build_wheel() {
    log_info "Building auragc-core wheel..."
    cd "$PROJECT_ROOT/auragc-core"
    
    # Install build dependencies if needed
    if ! python3 -c "import wheel" 2>/dev/null; then
        log_info "Installing wheel package..."
        pip install wheel > /dev/null 2>&1 || python3 -m pip install wheel > /dev/null 2>&1
    fi
    
    # Build wheel
    python3 setup.py bdist_wheel
    
    # Copy to wheels directory
    mkdir -p "$WHEELS_DIR"
    cp dist/auragc_core-*.whl "$WHEELS_DIR/"
    
    WHEEL_FILE=$(ls -1 "$WHEELS_DIR"/auragc_core-*.whl 2>/dev/null | head -1)
    if [ -n "$WHEEL_FILE" ]; then
        log_info "Wheel built: $(basename "$WHEEL_FILE")"
    else
        log_error "Failed to build wheel"
        exit 1
    fi
}

build_images() {
    log_info "Building Docker images..."
    cd "$COMPOSE_DIR"
    
    # Use docker compose if available, otherwise docker-compose
    if docker compose version &> /dev/null; then
        docker compose build --no-cache
    else
        docker-compose build --no-cache
    fi
    
    log_info "Images built successfully"
}

deploy() {
    log_info "Deploying services..."
    cd "$COMPOSE_DIR"
    
    # Use docker compose if available, otherwise docker-compose
    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi
    
    log_info "Services deployed"
}

health_check() {
    log_info "Waiting for services to be healthy..."
    sleep 5
    
    # Check baseline
    if curl -f http://localhost:8001/ > /dev/null 2>&1; then
        log_info "✓ Baseline service is up"
    else
        log_warn "Baseline service may not be ready yet"
    fi
    
    # Check AuraGC
    if curl -f http://localhost:8002/ > /dev/null 2>&1; then
        log_info "✓ AuraGC service is up"
    else
        log_warn "AuraGC service may not be ready yet"
    fi
    
    # Check dashboard
    if curl -f http://localhost:8501 > /dev/null 2>&1; then
        log_info "✓ Dashboard is up"
    else
        log_warn "Dashboard may not be ready yet"
    fi
}

show_status() {
    log_info "Service status:"
    cd "$COMPOSE_DIR"
    
    # Use docker compose if available, otherwise docker-compose
    if docker compose version &> /dev/null; then
        docker compose ps
    else
        docker-compose ps
    fi
    
    echo ""
    log_info "Access points:"
    echo "  - Baseline API:    http://localhost:8001"
    echo "  - AuraGC API:      http://localhost:8002"
    echo "  - Dashboard:       http://localhost:8501"
    echo "  - Locust UI:       http://localhost:8089"
}

# Main execution
main() {
    log_info "Starting AuraGC CI/CD deployment..."
    
    check_requirements
    cleanup "$@"
    build_wheel
    build_images
    deploy
    health_check
    show_status
    
    log_info "Deployment complete!"
}

# Run main function
main "$@"
