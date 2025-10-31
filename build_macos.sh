#!/bin/bash

###############################################################################
# Sitzplatz-Manager macOS Build Script
#
# This script automates the build process for creating a macOS app bundle
# using py2app. It handles cleaning, building, and testing the application.
#
# Usage: ./build_macos.sh [clean|build|test|all]
#        ./build_macos.sh              # Builds the app
#        ./build_macos.sh clean        # Removes build artifacts
#        ./build_macos.sh all          # Clean + build + test
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

# Project settings
PROJECT_NAME="Sitzplatz-Manager"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_DIR="${SCRIPT_DIR}/build"
DIST_DIR="${SCRIPT_DIR}/dist"
APP_BUNDLE="${DIST_DIR}/${PROJECT_NAME}.app"
PYTHON_VERSION="3.13"

# Use Python 3.13 from Homebrew (which has tkinter)
PYTHON_BIN="/opt/homebrew/opt/python@3.13/bin/python3.13"

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
    log_info "Checking system requirements..."

    # Check Python version
    if ! command -v "$PYTHON_BIN" &> /dev/null; then
        log_error "Python 3.13 is not installed at $PYTHON_BIN"
        exit 1
    fi

    PYTHON_VERSION_INSTALLED=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_info "Python version: $PYTHON_VERSION_INSTALLED"

    # Check for required packages
    "$PYTHON_BIN" -c "import py2app" 2>/dev/null || {
        log_warn "py2app not installed. Installing dependencies..."
        "$PYTHON_BIN" -m pip install -r requirements.txt
    }

    log_info "All requirements met ✓"
}

clean_build() {
    log_info "Cleaning build artifacts..."

    rm -rf "${BUILD_DIR}"
    rm -rf "${DIST_DIR}"
    rm -rf "${SCRIPT_DIR}/build"
    rm -rf "${SCRIPT_DIR}/.python-eggs"
    rm -rf "${SCRIPT_DIR}/__pycache__"

    # Clean pycache in subdirectories
    find "${SCRIPT_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "${SCRIPT_DIR}" -type f -name "*.pyc" -delete

    log_info "Build artifacts cleaned ✓"
}

build_app() {
    log_info "Building ${PROJECT_NAME} macOS app..."

    if [ ! -f "${SCRIPT_DIR}/setup.py" ]; then
        log_error "setup.py not found in project root"
        exit 1
    fi

    if [ ! -f "${SCRIPT_DIR}/main.py" ]; then
        log_error "main.py not found in project root"
        exit 1
    fi

    cd "${SCRIPT_DIR}"

    log_info "Running py2app build..."
    "$PYTHON_BIN" setup.py py2app

    if [ ! -d "${APP_BUNDLE}" ]; then
        log_error "App bundle creation failed"
        exit 1
    fi

    log_info "App bundle created successfully ✓"
    log_info "App location: ${APP_BUNDLE}"
}

verify_bundle() {
    log_info "Verifying app bundle integrity..."

    if [ ! -d "${APP_BUNDLE}" ]; then
        log_error "App bundle not found: ${APP_BUNDLE}"
        return 1
    fi

    # Check for main executable
    if [ ! -x "${APP_BUNDLE}/Contents/MacOS/${PROJECT_NAME}" ]; then
        log_error "Main executable not found"
        return 1
    fi

    # Check for assets
    if [ ! -d "${APP_BUNDLE}/Contents/Resources/assets" ]; then
        log_warn "Assets directory not found in app bundle"
        # Not fatal, but worth noting
    fi

    log_info "App bundle verification passed ✓"
}

test_app() {
    log_info "Testing app bundle..."

    verify_bundle || {
        log_error "Bundle verification failed"
        return 1
    }

    log_info "Attempting to launch app (you may need to grant permissions)..."

    # Try to launch the app with a timeout
    # Note: This may fail if Security & Privacy settings require approval
    if timeout 5 open "${APP_BUNDLE}" 2>/dev/null; then
        sleep 2
        log_info "App launched successfully ✓"
        # Optional: kill the app if you don't want it to stay open
        # killall "${PROJECT_NAME}" 2>/dev/null || true
    else
        log_warn "App launch test timed out or failed"
        log_warn "You can manually test with: open '${APP_BUNDLE}'"
    fi
}

show_help() {
    cat << EOF
${GREEN}Sitzplatz-Manager macOS Build Script${NC}

Usage: ./build_macos.sh [command]

Commands:
    clean       Remove all build artifacts
    build       Build the macOS app bundle
    test        Test the built app
    all         Clean, build, and test (full workflow)
    help        Show this help message

Examples:
    ./build_macos.sh              # Build only
    ./build_macos.sh all          # Clean + build + test
    ./build_macos.sh clean        # Clean only

Environment:
    Python version: ${PYTHON_VERSION_INSTALLED:-unknown}
    Project name:   ${PROJECT_NAME}
    Build dir:      ${BUILD_DIR}
    Dist dir:       ${DIST_DIR}
EOF
}

# Main script
main() {
    log_info "Starting ${PROJECT_NAME} build process..."

    # Default command is 'build'
    COMMAND="${1:-build}"

    case "${COMMAND}" in
        clean)
            clean_build
            ;;
        build)
            check_requirements
            build_app
            verify_bundle
            ;;
        test)
            test_app
            ;;
        all)
            check_requirements
            clean_build
            build_app
            verify_bundle
            test_app
            log_info "Build process completed successfully! ✓"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: ${COMMAND}"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
