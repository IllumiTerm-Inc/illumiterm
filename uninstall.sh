#!/bin/bash
set -e

ICON_DIR="/usr/share/icons/hicolor/24x24/apps"
APP_DIR="/usr/share/applications"
BIN_DIR="/usr/local/bin"

# List of icons to remove
ICONS=(
    about.png
    preferences-system-search-symbolic.svg
    window-new.svg
    tab-new.svg
    tab-close.svg
    window-close.svg
    edit-copy.svg
    edit-paste.svg
    edit-clear.svg
    zoom-in.svg
    zoom-out.svg
    zoom-original.svg
    configure.svg
    edit.svg
    go-previous.svg
    go-next.svg
    go-up.svg
    go-down.svg
    help-about.svg
    object-select-symbolic.svg
    drop-down.svg
    list-add-symbolic-red-cross.svg
)

echo "Removing icons..."
for icon in "${ICONS[@]}"; do
    rm -f "$ICON_DIR/$icon"
done

echo "Removing desktop entry..."
rm -f "$APP_DIR/illumiterm.desktop"

echo "Removing program..."
rm -f "$BIN_DIR/illumiterm"

echo "Removing privacy config..."
rm -f /etc/sudoers.d/privacy

echo "Uninstallation complete."
