#!/bin/bash

# Setup alias for jmAgent development script
# Add to shell profile for easy access

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="$PROJECT_ROOT/shell/local-start.sh"

# Determine shell profile
if [ -f "$HOME/.zshrc" ]; then
    PROFILE_FILE="$HOME/.zshrc"
    SHELL_TYPE="zsh"
elif [ -f "$HOME/.bashrc" ]; then
    PROFILE_FILE="$HOME/.bashrc"
    SHELL_TYPE="bash"
elif [ -f "$HOME/.bash_profile" ]; then
    PROFILE_FILE="$HOME/.bash_profile"
    SHELL_TYPE="bash"
else
    echo "❌ Could not find shell profile (~/.zshrc or ~/.bashrc)"
    exit 1
fi

# Alias to add
ALIAS_LINE="alias jm-dev='$SCRIPT_PATH'"

# Check if alias already exists
if grep -q "alias jm-dev=" "$PROFILE_FILE"; then
    echo "✅ Alias 'jm-dev' already exists in $PROFILE_FILE"
    exit 0
fi

# Add alias
echo "" >> "$PROFILE_FILE"
echo "# jmAgent development shortcut (added $(date))" >> "$PROFILE_FILE"
echo "$ALIAS_LINE" >> "$PROFILE_FILE"

echo "✅ Alias 'jm-dev' added to $PROFILE_FILE"
echo ""
echo "To use immediately, run:"
echo "  source $PROFILE_FILE"
echo ""
echo "Then you can use:"
echo "  jm-dev start"
echo "  jm-dev stop"
echo "  jm-dev status"
echo "  jm-dev restart"
