INSTALL = install
INSTALL_PROGRAM = $(INSTALL) -D -m 755
INSTALL_DATA = $(INSTALL) -D -m 644
ICON_DIR = /usr/share/icons/hicolor/24x24/apps
APP_DIR = /usr/share/applications
BIN_DIR = /usr/local/bin

ICONS = \
    data/icons/about.png \
    data/icons/preferences-system-search-symbolic.svg \
    data/icons/window-new.svg \
    data/icons/tab-new.svg \
    data/icons/tab-close.svg \
    data/icons/window-close.svg \
    data/icons/edit-copy.svg \
    data/icons/edit-paste.svg \
    data/icons/edit-clear.svg \
    data/icons/zoom-in.svg \
    data/icons/zoom-out.svg \
    data/icons/zoom-original.svg \
    data/icons/configure.svg \
    data/icons/edit.svg \
    data/icons/go-previous.svg \
    data/icons/go-next.svg \
    data/icons/go-up.svg \
    data/icons/go-down.svg \
    data/icons/help-about.svg \
    data/icons/object-select-symbolic.svg \
    data/icons/drop-down.svg \
    data/icons/list-add-symbolic-red-cross.svg

DESKTOP_ENTRY = illumiterm.desktop
PROGRAM = src/illumiterm.py

.PHONY: install clean privacy-config

install: icons desktop-entry program privacy-config

icons: $(ICONS)
	mkdir -p $(ICON_DIR)
	$(INSTALL_DATA) data/icons/about.png $(ICON_DIR)/about.png
	$(INSTALL_DATA) data/icons/preferences-system-search-symbolic.svg $(ICON_DIR)/preferences-system-search-symbolic.svg
	$(INSTALL_DATA) data/icons/window-new.svg $(ICON_DIR)/window-new.svg
	$(INSTALL_DATA) data/icons/tab-new.svg $(ICON_DIR)/tab-new.svg
	$(INSTALL_DATA) data/icons/tab-close.svg $(ICON_DIR)/tab-close.svg
	$(INSTALL_DATA) data/icons/window-close.svg $(ICON_DIR)/window-close.svg
	$(INSTALL_DATA) data/icons/edit-copy.svg $(ICON_DIR)/edit-copy.svg
	$(INSTALL_DATA) data/icons/edit-paste.svg $(ICON_DIR)/edit-paste.svg
	$(INSTALL_DATA) data/icons/edit-clear.svg $(ICON_DIR)/edit-clear.svg
	$(INSTALL_DATA) data/icons/zoom-in.svg $(ICON_DIR)/zoom-in.svg
	$(INSTALL_DATA) data/icons/zoom-out.svg $(ICON_DIR)/zoom-out.svg
	$(INSTALL_DATA) data/icons/zoom-original.svg $(ICON_DIR)/zoom-original.svg
	$(INSTALL_DATA) data/icons/configure.svg $(ICON_DIR)/configure.svg
	$(INSTALL_DATA) data/icons/edit.svg $(ICON_DIR)/edit.svg
	$(INSTALL_DATA) data/icons/go-previous.svg $(ICON_DIR)/go-previous.svg
	$(INSTALL_DATA) data/icons/go-next.svg $(ICON_DIR)/go-next.svg
	$(INSTALL_DATA) data/icons/go-up.svg $(ICON_DIR)/go-up.svg
	$(INSTALL_DATA) data/icons/go-down.svg $(ICON_DIR)/go-down.svg
	$(INSTALL_DATA) data/icons/object-select-symbolic.svg $(ICON_DIR)/object-select-symbolic.svg
	$(INSTALL_DATA) data/icons/drop-down.svg $(ICON_DIR)/drop-down.svg
	$(INSTALL_DATA) data/icons/list-add-symbolic-red-cross.svg $(ICON_DIR)/list-add-symbolic-red-cross.svg
	$(INSTALL_DATA) data/icons/help-about.svg $(ICON_DIR)/help-about.svg

desktop-entry:
	mkdir -p $(APP_DIR)
	$(INSTALL_DATA) $(DESKTOP_ENTRY) $(APP_DIR)/$(DESKTOP_ENTRY)

program: $(PROGRAM)
	mkdir -p $(BIN_DIR)
	$(INSTALL_PROGRAM) $(PROGRAM) $(BIN_DIR)/illumiterm
	chmod +x $(BIN_DIR)/illumiterm

privacy-config:
	touch /etc/sudoers.d/privacy
	echo 'Defaults        lecture = always' | tee -a /etc/sudoers.d/privacy > /dev/null

clean:
	rm -f $(ICON_DIR)/about.png
	rm -f $(ICON_DIR)/preferences-system-search-symbolic.svg
	rm -f $(ICON_DIR)/window-new.svg
	rm -f $(ICON_DIR)/tab-new.svg
	rm -f $(ICON_DIR)/tab-close.svg
	rm -f $(ICON_DIR)/window-close.svg
	rm -f $(ICON_DIR)/edit-copy.svg
	rm -f $(ICON_DIR)/edit-paste.svg
	rm -f $(ICON_DIR)/edit-clear.svg
	rm -f $(ICON_DIR)/zoom-in.svg
	rm -f $(ICON_DIR)/zoom-out.svg
	rm -f $(ICON_DIR)/zoom-original.svg
	rm -f $(ICON_DIR)/configure.svg
	rm -f $(ICON_DIR)/edit.svg
	rm -f $(ICON_DIR)/go-previous.svg
	rm -f $(ICON_DIR)/go-next.svg
	rm -f $(ICON_DIR)/go-up.svg
	rm -f $(ICON_DIR)/go-down.svg
	rm -f $(ICON_DIR)/object-select-symbolic.svg
	rm -f $(ICON_DIR)/list-add-symbolic-red-cross.svg
	rm -f $(ICON_DIR)/help-about.svg
	rm -f $(ICON_DIR)/drop-down.svg
	rm -f $(APP_DIR)/$(DESKTOP_ENTRY)
	rm -f $(BIN_DIR)/illumiterm
