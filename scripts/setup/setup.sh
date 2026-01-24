#!/bin/bash
# LibraryDown Setup Script
# Full installation and startup

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Run master-manager.sh from the correct location
cd "$PROJECT_ROOT"
./scripts/utils/master-manager.sh setup