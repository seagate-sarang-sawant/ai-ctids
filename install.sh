#!/bin/bash
# ============================================================================
# AI-CTIDS Installation Script
# ============================================================================
# Quick installation script for setting up the AI-CTIDS environment
# Usage: ./install.sh [full|minimal|dev]
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Print banner
echo "============================================================================"
echo "  AI-CTIDS Installation"
echo "  AI-Driven Cyber Threat Detection and Intrusion Detection System"
echo "============================================================================"
echo ""

# Check Python version
print_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
print_success "Python $PYTHON_VERSION found"

# Check pip
print_info "Checking pip..."
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    print_error "pip is not installed. Please install pip."
    exit 1
fi
print_success "pip found"

# Determine installation type
INSTALL_TYPE=${1:-full}

print_info "Installation type: $INSTALL_TYPE"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip --quiet
print_success "pip upgraded"

# Install dependencies based on type
case $INSTALL_TYPE in
    full)
        print_info "Installing full dependencies (requirements.txt)..."
        pip install -r requirements.txt
        print_success "Full dependencies installed"
        ;;
    minimal)
        print_info "Installing minimal dependencies (requirements-minimal.txt)..."
        pip install -r requirements-minimal.txt
        print_success "Minimal dependencies installed"
        ;;
    dev)
        print_info "Installing development dependencies (requirements-dev.txt)..."
        pip install -r requirements-dev.txt
        print_success "Development dependencies installed"
        ;;
    *)
        print_error "Invalid installation type: $INSTALL_TYPE"
        print_info "Usage: ./install.sh [full|minimal|dev]"
        exit 1
        ;;
esac

# Create necessary directories
print_info "Creating project directories..."
mkdir -p data models logs
print_success "Directories created"

# Copy .env.example if .env doesn't exist
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    print_info "Creating .env file from template..."
    cp .env.example .env
    print_success ".env file created"
fi

echo ""
echo "============================================================================"
print_success "Installation complete!"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment:"
echo "     ${GREEN}source venv/bin/activate${NC}"
echo ""
echo "  2. Configure your environment (edit .env file)"
echo ""
echo "  3. Download the CICIDS2017 dataset to data/ directory"
echo ""
echo "  4. Train models:"
echo "     ${GREEN}make train${NC}"
echo ""
echo "  5. Start the API:"
echo "     ${GREEN}make api-dev${NC}"
echo ""
echo "  6. Or start all services with Docker:"
echo "     ${GREEN}make docker-up${NC}"
echo ""
echo "For more commands, run: ${GREEN}make help${NC}"
echo "============================================================================"
