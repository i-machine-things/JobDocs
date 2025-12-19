#!/bin/bash
# Quick version bump script for JobDocs

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to show usage
show_usage() {
    echo "JobDocs Version Bump Utility"
    echo ""
    echo "Usage:"
    echo "  ./bump_version.sh [command] [version]"
    echo ""
    echo "Commands:"
    echo "  show               Show current version information (default)"
    echo "  patch              Bump patch version (0.2.0 -> 0.2.1)"
    echo "  minor              Bump minor version (0.2.0 -> 0.3.0)"
    echo "  major              Bump major version (0.2.0 -> 1.0.0)"
    echo "  set <version>      Set specific version (e.g., 1.0.0 or 1.0.0-beta)"
    echo ""
    echo "Examples:"
    echo "  ./bump_version.sh                # Show current version"
    echo "  ./bump_version.sh patch          # Bump patch number"
    echo "  ./bump_version.sh set 1.0.0      # Set to version 1.0.0"
    echo "  ./bump_version.sh set 1.0.0-rc1  # Set to 1.0.0-rc1"
}

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found"
    exit 1
fi

# Handle commands
case "${1:-show}" in
    -h|--help|help)
        show_usage
        ;;
    show|info|current)
        python3 "$SCRIPT_DIR/update_version.py"
        ;;
    patch)
        python3 "$SCRIPT_DIR/update_version.py" patch
        ;;
    minor)
        python3 "$SCRIPT_DIR/update_version.py" minor
        ;;
    major)
        python3 "$SCRIPT_DIR/update_version.py" major
        ;;
    set)
        if [ -z "$2" ]; then
            echo "Error: 'set' command requires a version argument"
            echo "Example: ./bump_version.sh set 1.0.0"
            exit 1
        fi
        python3 "$SCRIPT_DIR/update_version.py" set "$2"
        ;;
    *)
        echo "Error: Unknown command '$1'"
        echo ""
        show_usage
        exit 1
        ;;
esac
