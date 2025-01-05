#!/usr/bin/env python3

# Copyright 2025 Elijah Gordon (NitrixXero) <nitrixxero@gmail.com>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Vte, GLib, Gdk
import os
import socket

open_windows = 0

class TerminalWindow(Gtk.Window):
    def __init__(self):
        global open_windows
        super().__init__()
        self.set_icon_from_file("/usr/share/icons/hicolor/24x24/apps/about.png")

        open_windows += 1

        self.tab_labels = {}

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)

        self.accel_group = Gtk.AccelGroup()
        self.add_accel_group(self.accel_group)

        self.create_menu_bar(vbox)

        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        vbox.pack_start(self.notebook, True, True, 0)

        self.notebook.connect("switch-page", self.on_switch_page)

        self.add_terminal_tab()

        self.set_default_size(650, 500)

        self.connect("delete-event", self.on_delete_event)

    def create_menu_bar(self, vbox):
        menubar = Gtk.MenuBar()

        def create_menu_item(label_text, icon_path, shortcut_text, accelerator, callback):
            menu_item = Gtk.MenuItem()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

            icon = Gtk.Image.new_from_file(icon_path)
            label = Gtk.Label(label=label_text)
            shortcut_label = Gtk.Label(label=shortcut_text)
            shortcut_label.get_style_context().add_class("dim-label")
            shortcut_label.set_xalign(1)

            box.pack_start(icon, False, False, 0)
            box.pack_start(label, False, False, 0)
            box.pack_end(shortcut_label, False, False, 0)

            menu_item.add(box)

            if accelerator:
                key, mod = Gtk.accelerator_parse(accelerator)
                if key != 0:
                    menu_item.add_accelerator("activate", self.accel_group, key, mod, Gtk.AccelFlags.VISIBLE)

            menu_item.connect("activate", callback)
            menu_item.show_all()

            return menu_item

        file_menu_item = Gtk.MenuItem(label="File")
        menubar.append(file_menu_item)

        file_menu = Gtk.Menu()
        file_menu_item.set_submenu(file_menu)

        file_menu.append(create_menu_item("New Window", "/usr/share/icons/hicolor/24x24/apps/window-new.svg", "Shift+Ctrl+N", "<Shift><Control>N", self.on_new_window))
        file_menu.append(create_menu_item("New Tab", "/usr/share/icons/hicolor/24x24/apps/tab-new.svg", "Shift+Ctrl+T", "<Shift><Control>T", self.on_new_tab))

        file_menu.append(Gtk.SeparatorMenuItem())

        file_menu.append(create_menu_item("Close Tab", "/usr/share/icons/hicolor/24x24/apps/tab-close.svg", "Shift+Ctrl+W", "<Shift><Control>W", self.on_close_tab))
        file_menu.append(create_menu_item("Close Window", "/usr/share/icons/hicolor/24x24/apps/window-close.svg", "Shift+Ctrl+Q", "<Shift><Control>Q", self.on_close_window))

        edit_menu = Gtk.Menu()
        edit_item = Gtk.MenuItem(label="Edit")
        edit_item.set_submenu(edit_menu)
        menubar.append(edit_item)

        edit_menu.append(create_menu_item("Copy", "/usr/share/icons/hicolor/24x24/apps/edit-copy.svg", "Shift+Ctrl+C", "<Shift><Control>C", self.on_copy))
        edit_menu.append(create_menu_item("Paste", "/usr/share/icons/hicolor/24x24/apps/edit-paste.svg", "Shift+Ctrl+V", "<Shift><Control>V", self.on_paste))

        edit_menu.append(Gtk.SeparatorMenuItem())

        edit_menu.append(create_menu_item("Clear Scrollback", "/usr/share/icons/hicolor/24x24/apps/edit-clear.svg", "", "", self.on_clear_scrollback))

        edit_menu.append(Gtk.SeparatorMenuItem())

        edit_menu.append(create_menu_item("Zoom In", "/usr/share/icons/hicolor/24x24/apps/zoom-in.svg", "Shift+Ctrl++", "<Shift><Control>plus", self.on_zoom_in))
        edit_menu.append(create_menu_item("Zoom Out", "/usr/share/icons/hicolor/24x24/apps/zoom-out.svg", "Shift+Ctrl+_", "<Shift><Control>underscore", self.on_zoom_out))
        edit_menu.append(create_menu_item("Zoom Reset", "/usr/share/icons/hicolor/24x24/apps/zoom-original.svg", "Shift+Ctrl+)", "<Shift><Control>parenright", self.on_zoom_reset))

        edit_menu.append(Gtk.SeparatorMenuItem())

        tabs_menu = Gtk.Menu()
        tabs_item = Gtk.MenuItem(label="Tabs")
        tabs_item.set_submenu(tabs_menu)

        tabs_menu.append(create_menu_item("Name Tab", "/usr/share/icons/hicolor/24x24/apps/edit.svg", "Shift+Ctrl+I", "<Shift><Control>I", self.on_name_tab))

        tabs_menu.append(Gtk.SeparatorMenuItem())

        tabs_menu.append(create_menu_item("Previous Tab", "/usr/share/icons/hicolor/24x24/apps/go-previous.svg", "Shift+Ctrl+Left", "<Control><Shift>Left", self.on_previous_tab))
        tabs_menu.append(create_menu_item("Next Tab", "/usr/share/icons/hicolor/24x24/apps/go-next.svg", "Shift+Ctrl+Right", "<Shift><Control>Right", self.on_next_tab))

        tabs_menu.append(Gtk.SeparatorMenuItem())

        tabs_menu.append(create_menu_item("Move Tab Left", "/usr/share/icons/hicolor/24x24/apps/go-up.svg", "Shift+Ctrl+Page Up", "<Shift><Control>Page_Up", self.on_move_tab_left))
        tabs_menu.append(create_menu_item("Move Tab Right", "/usr/share/icons/hicolor/24x24/apps/go-down.svg", "Shift+Ctrl+Page Down", "<Shift><Control>Page_Down", self.on_move_tab_right))

        menubar.append(tabs_item)

        position_menu = Gtk.Menu()
        position_item = Gtk.MenuItem(label="Position")
        position_item.set_submenu(position_menu)

        position_menu.append(create_menu_item("Move Window Left", "/usr/share/icons/hicolor/24x24/apps/go-previous.svg", "Ctrl+Left", "<Control>Left", self.on_move_left))
        position_menu.append(create_menu_item("Move Window Right", "/usr/share/icons/hicolor/24x24/apps/go-next.svg", "Ctrl+Right", "<Control>Right", self.on_move_right))

        position_menu.append(Gtk.SeparatorMenuItem())

        position_menu.append(create_menu_item("Enter Fullscreen", "/usr/share/icons/hicolor/24x24/apps/go-up.svg", "Shift+Ctrl+F", "<Shift><Control>F", self.on_fullscreen))
        position_menu.append(create_menu_item("Exit Fullscreen", "/usr/share/icons/hicolor/24x24/apps/go-down.svg", "Shift+Ctrl+Esc", "<Shift><Control>Escape", self.on_exit_fullscreen))

        position_menu.append(Gtk.SeparatorMenuItem())

        position_menu.append(create_menu_item("Increase Window Size", "/usr/share/icons/hicolor/24x24/apps/zoom-in.svg", "Ctrl+Alt+9", "<Control><Alt>9", self.on_increase_size))
        position_menu.append(create_menu_item("Decrease Window Size", "/usr/share/icons/hicolor/24x24/apps/zoom-out.svg", "Ctrl+Alt+8", "<Control><Alt>8", self.on_decrease_size))
        position_menu.append(create_menu_item("Reset Window Size", "/usr/share/icons/hicolor/24x24/apps/zoom-original.svg", "Ctrl+Alt+)", "<Control><Alt>0", self.on_reset_size))
        menubar.append(position_item)

        helpmenu = Gtk.Menu()
        help_item = Gtk.MenuItem(label="Help")
        help_item.set_submenu(helpmenu)

        about_item = Gtk.MenuItem()
        about_icon = Gtk.Image.new_from_file("/usr/share/icons/hicolor/24x24/apps/help-about.svg")
        about_label = Gtk.Label(label="About")
        about_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        about_box.pack_start(about_icon, False, False, 0)
        about_box.pack_start(about_label, True, True, 0)
        about_item.add(about_box)
        about_item.connect("activate", self.on_about)
        helpmenu.append(about_item)
        menubar.append(help_item)

        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        self.set_titlebar(header_bar)

        preferences_button = Gtk.Button()
        preferences_button.set_relief(Gtk.ReliefStyle.NONE)
        preferences_icon = Gtk.Image.new_from_file("/usr/share/icons/hicolor/24x24/apps/configure.svg")
        preferences_button.set_image(preferences_icon)
        preferences_button.connect("clicked", self.on_preferences)
        header_bar.pack_end(preferences_button)
        preferences_button.show()

        search_button = Gtk.Button()
        search_icon = Gtk.Image.new_from_file("/usr/share/icons/hicolor/24x24/apps/preferences-system-search-symbolic.svg")
        search_button.set_image(search_icon)
        search_button.set_relief(Gtk.ReliefStyle.NONE)
        search_button.connect("clicked", self.on_search)
        header_bar.pack_end(search_button)

        self.accel_group = Gtk.AccelGroup()
        self.add_accel_group(self.accel_group)
        key, mod = Gdk.keyval_from_name("S"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK
        search_button.add_accelerator("clicked", self.accel_group, key, mod, Gtk.AccelFlags.VISIBLE)

        self.connect("button-press-event", self.on_right_click)
        self.add_context_menu()

        vbox.pack_start(menubar, False, False, 0)
        vbox.pack_start(header_bar, False, False, 0)

    def add_context_menu(self):
        self.context_menu = Gtk.Menu()

        def add_menu_item(label_text, icon_path, callback):
            menu_item = Gtk.MenuItem()

            icon_image = Gtk.Image.new_from_file(icon_path)

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.set_halign(Gtk.Align.START)
            box.set_spacing(10)

            icon_image.set_size_request(24, 24)
            box.pack_start(icon_image, False, False, 0)

            label = Gtk.Label(label=label_text)
            label.set_halign(Gtk.Align.START)
            label.set_xalign(0.0)
            box.pack_start(label, True, True, 0)

            menu_item.add(box)
            menu_item.connect("activate", callback)
            self.context_menu.append(menu_item)

        add_menu_item("New Window", "/usr/share/icons/hicolor/24x24/apps/window-new.svg", self.on_new_window)
        add_menu_item("New Tab", "/usr/share/icons/hicolor/24x24/apps/tab-new.svg", self.on_new_tab)
        self.context_menu.append(Gtk.SeparatorMenuItem())
        add_menu_item("Copy", "/usr/share/icons/hicolor/24x24/apps/edit-copy.svg", self.on_copy)
        add_menu_item("Paste", "/usr/share/icons/hicolor/24x24/apps/edit-paste.svg", self.on_paste)
        self.context_menu.append(Gtk.SeparatorMenuItem())
        add_menu_item("Clear Scrollback", "/usr/share/icons/hicolor/24x24/apps/edit-clear.svg", self.on_clear_scrollback)
        self.context_menu.append(Gtk.SeparatorMenuItem())
        add_menu_item("Name Tab", "/usr/share/icons/hicolor/24x24/apps/edit.svg", self.on_name_tab)
        self.context_menu.append(Gtk.SeparatorMenuItem())
        add_menu_item("Previous Tab", "/usr/share/icons/hicolor/24x24/apps/go-previous.svg", self.on_previous_tab)
        add_menu_item("Next Tab", "/usr/share/icons/hicolor/24x24/apps/go-next.svg", self.on_next_tab)
        self.context_menu.append(Gtk.SeparatorMenuItem())
        add_menu_item("Move Tab Left", "/usr/share/icons/hicolor/24x24/apps/go-up.svg", self.on_move_tab_left)
        add_menu_item("Move Tab Right", "/usr/share/icons/hicolor/24x24/apps/go-down.svg", self.on_move_tab_right)
        self.context_menu.append(Gtk.SeparatorMenuItem())
        add_menu_item("Close Tab", "/usr/share/icons/hicolor/24x24/apps/window-close.svg", self.on_close_tab)

        self.context_menu.show_all()

    def on_right_click(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            self.context_menu.popup_at_pointer(event)
            return True

    def add_terminal_tab(self):
        terminal = Vte.Terminal()
        terminal.set_scroll_on_output(True)
        terminal.set_scroll_on_keystroke(True)

        self.spawn_shell(terminal)

        terminal.connect("key-press-event", self.on_key_press)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(terminal)

        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        hostname = socket.gethostname()
        initial_directory = os.getcwd()
        initial_tab_label = f"{hostname}: {initial_directory}"

        tab_label = Gtk.Label(label=initial_tab_label)

        new_tab_index = self.notebook.get_n_pages()
        self.tab_labels[new_tab_index] = {
            'label': tab_label,
            'tab_box': tab_box,
            'dynamic': True,
            'custom_title': None
        }

        close_button = Gtk.Button.new_from_icon_name("window-close", Gtk.IconSize.MENU)
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.set_focus_on_click(False)

        tab_box.pack_start(tab_label, True, True, 0)
        tab_box.pack_start(close_button, False, False, 0)
        tab_box.show_all()

        terminal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        terminal_box.pack_start(scrolled_window, True, True, 0)

        self.notebook.append_page(terminal_box, tab_box)
        self.notebook.show_all()
        self.notebook.set_tab_reorderable(terminal_box, True)

        close_button.connect("clicked", self.on_close_tab, terminal_box)

        terminal.connect("child-exited", lambda term, _: self.on_child_exited(terminal_box))
        terminal.connect("window-title-changed", lambda term: self.on_title_changed(term, new_tab_index))
        terminal.connect("eof", self.on_eof)

        self.update_tab_label(new_tab_index, initial_tab_label)
        self.notebook.set_current_page(new_tab_index)

        self.set_title(initial_tab_label)

    def update_tab_label(self, tab_index, new_title):
        tab_data = self.tab_labels.get(tab_index)
        if tab_data:
            title = tab_data['custom_title'] if tab_data['custom_title'] else new_title
            tab_data['label'].set_text(title[:14] + "..." if len(title) > 14 else title)
            tab_data['label'].set_tooltip_text(title)

            if self.notebook.get_current_page() == tab_index:
                self.set_title(title)

    def on_title_changed(self, terminal, tab_index):
        current_title = terminal.get_window_title()
        tab_data = self.tab_labels.get(tab_index)

        if tab_data and tab_data['dynamic'] and not tab_data['custom_title']:
            self.update_tab_label(tab_index, current_title)

    def on_switch_page(self, notebook, page, page_num):
        terminal_box = self.notebook.get_nth_page(page_num)
        terminal = terminal_box.get_children()[0].get_child()
        tab_data = self.tab_labels.get(page_num)

        if tab_data:
            if tab_data['custom_title']:
                self.set_title(tab_data['custom_title'])
            else:
                hostname = socket.gethostname()
                current_directory = terminal.get_window_title() or os.getcwd()
                title = f"{current_directory}"
                self.set_title(title)
                self.update_tab_label(page_num, title)

    def on_name_tab(self, widget):
        current_page = self.notebook.get_current_page()
        if current_page == -1:
            return

        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Enter New Tab Name:"
        )

        dialog.set_icon_from_file("/usr/share/icons/hicolor/24x24/apps/edit.svg")

        entry = Gtk.Entry()
        dialog.vbox.pack_start(entry, True, True, 0)
        entry.show()

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            new_name = entry.get_text() or "Terminal"
            tab_data = self.tab_labels.get(current_page)
            if tab_data:
                tab_data['label'].set_text(new_name)
                tab_data['dynamic'] = False
                tab_data['custom_title'] = new_name
                self.set_title(new_name)

        dialog.destroy()

    def on_delete_event(self, widget, event):
        num_tabs = self.notebook.get_n_pages()
        if num_tabs > 1:
            self.show_warning_dialog(num_tabs)
            return True
        return False

    def show_warning_dialog(self, num_tabs):
        dialog = Gtk.MessageDialog(
            parent=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Warning: You have multiple tabs open!",
        )
        dialog.format_secondary_text(f"You currently have {num_tabs} tab(s) open. Are you sure you want to close the application?")
        warning_icon = Gtk.Image.new_from_file("/usr/share/icons/hicolor/48x48/status/dialog-warning.svg")
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            self.destroy()

    def spawn_shell(self, terminal):
        shell = os.environ.get('SHELL', '/bin/bash')

        terminal.spawn_async(
            Vte.PtyFlags.DEFAULT,
            os.environ['HOME'],
            [shell],
            [],
            GLib.SpawnFlags.DEFAULT,
            None,
            None,
            -1,
            None,
            None,
            None
        )

    def on_child_exited(self, terminal, status):
        current_page = self.notebook.get_current_page()

        if current_page != -1:
            terminal_box = self.notebook.get_nth_page(current_page)
            if terminal_box is not None:
                self.notebook.remove_page(current_page)

        if self.notebook.get_n_pages() == 0:
            self.destroy()

    def on_eof(self, terminal):
        current_page = self.notebook.get_current_page()
        self.notebook.remove_page(current_page)

        if self.notebook.get_n_pages() == 0:
            self.destroy()

    def on_key_press(self, terminal, key_event):
        keyval = key_event.keyval
        state = Gdk.ModifierType(key_event.state)

        if keyval == Gdk.KEY_d and state & Gdk.ModifierType.CONTROL_MASK:
            self.on_eof(terminal)
            return True

        return False

    def get_current_terminal(self):
        current_page = self.notebook.get_current_page()
        if current_page == -1:
            return None
        terminal_box = self.notebook.get_nth_page(current_page)
        if terminal_box is None:
            return None
        scrolled_window = terminal_box.get_children()[0]
        terminal = scrolled_window.get_child()
        return terminal

    def on_new_window(self, widget):
        new_window = TerminalWindow()
        new_window.show_all()

    def on_new_tab(self, widget):
        self.add_terminal_tab()

    def on_close_tab(self, button=None, terminal_box=None):
        if terminal_box is None:
            current_page = self.notebook.get_current_page()
            terminal_box = self.notebook.get_nth_page(current_page)

        page_num = self.notebook.page_num(terminal_box)
        if page_num != -1:
            self.notebook.remove_page(page_num)

        if self.notebook.get_n_pages() == 0:
            self.destroy()

    def on_close_window(self, widget):
        num_tabs = self.notebook.get_n_pages()
        if num_tabs > 1:
            self.show_warning_dialog(num_tabs)
        else:
            self.destroy()

    def on_copy(self, widget):
        terminal = self.get_current_terminal()
        if terminal:
            terminal.copy_clipboard_format(Vte.Format.TEXT)

    def on_paste(self, widget):
        terminal = self.get_current_terminal()
        if terminal:
            terminal.paste_clipboard()

    def on_clear_scrollback(self, widget):
        terminal = self.get_current_terminal()
        if terminal:
            terminal.reset(True, True)

    def on_zoom_in(self, widget):
        terminal = self.get_current_terminal()
        if terminal:
            current_scale = terminal.get_font_scale()
            terminal.set_font_scale(current_scale + 0.1)

    def on_zoom_out(self, widget):
        terminal = self.get_current_terminal()
        if terminal:
            terminal.set_font_scale(terminal.get_font_scale() - 0.1)

    def on_zoom_reset(self, widget):
        terminal = self.get_current_terminal()
        if terminal:
            terminal.set_font_scale(1.0)

    def on_preferences(self, widget):
        pref_window = Gtk.Window(title="Preferences")
        pref_window.set_default_size(600, 600)
        pref_window.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        pref_window.set_resizable(False)
        pref_window.set_icon_from_file("/usr/share/icons/hicolor/24x24/apps/configure.svg")

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        notebook = Gtk.Notebook()

        self.create_tab(notebook, "Style", self.create_style_content())
        self.create_tab(notebook, "Display", self.create_display_content())
        self.create_tab(notebook, "Advanced", self.create_advanced_content())

        shortcuts_content = self.create_shortcuts_content()
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(shortcuts_content)
        self.create_tab(notebook, "Shortcuts", scrolled_window)

        vbox.pack_start(notebook, True, True, 0)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", self.on_cancel_clicked)

        ok_button = Gtk.Button(label="OK")
        ok_button.connect("clicked", self.on_ok_clicked)

        button_box.pack_start(cancel_button, False, False, 0)
        button_box.pack_start(ok_button, False, False, 0)

        vbox.pack_start(button_box, False, False, 10)
        button_box.set_margin_end(20)

        pref_window.add(vbox)
        pref_window.show_all()

    def on_cancel_clicked(self, widget):
        widget.get_toplevel().destroy()

    def on_ok_clicked(self, widget):
        widget.get_toplevel().destroy()

    def create_tab(self, notebook, tab_label, content):
        tab = Gtk.Label(label=tab_label)
        notebook.append_page(content, tab)

    def create_style_content(self):
        style_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        font_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        font_label = Gtk.Label(label="Terminal Font:")
        font_label.set_halign(Gtk.Align.START)

        font_button = Gtk.FontButton()
        font_button.set_font("Monospace 10")
        font_button.connect("font-set", self.on_font_set)

        font_box.pack_start(font_label, True, True, 0)
        font_box.pack_start(font_button, False, False, 0)
        style_box.pack_start(font_box, False, False, 0)

        bg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bg_label = Gtk.Label(label="Background Color:")
        bg_label.set_halign(Gtk.Align.START)

        bg_color_button = Gtk.ColorButton()
        bg_color_button.set_rgba(Gdk.RGBA(0, 0, 0, 1))
        bg_color_button.connect("color-set", self.on_select_background_color)
        bg_color_button.set_size_request(190, 40)

        bg_box.pack_start(bg_label, True, True, 0)
        bg_box.pack_start(bg_color_button, False, False, 0)
        style_box.pack_start(bg_box, False, False, 0)

        fg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        fg_label = Gtk.Label(label="Foreground Color:")
        fg_label.set_halign(Gtk.Align.START)

        fg_color_button = Gtk.ColorButton()
        fg_color_button.set_rgba(Gdk.RGBA(1, 1, 1, 1))
        fg_color_button.connect("color-set", self.on_select_foreground_color)
        fg_color_button.set_size_request(190, 40)

        fg_box.pack_start(fg_label, True, True, 0)
        fg_box.pack_start(fg_color_button, False, False, 0)
        style_box.pack_start(fg_box, False, False, 0)

        palette_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        palette_label = Gtk.Label(label="Palette:")
        palette_label.set_halign(Gtk.Align.START)

        palette_combo = Gtk.ComboBoxText()
        palette_options = ["VGA", "xterm", "Tango", "Solarized Dark", "Solarized Light", "Custom"]

        for option in palette_options:
            palette_combo.append_text(option)

        palette_combo.set_active(0)
        palette_combo.set_size_request(190, 40)

        palette_box.pack_start(palette_label, True, True, 0)
        palette_box.pack_start(palette_combo, False, False, 0)
        style_box.pack_start(palette_box, False, False, 0)

        color_grid = Gtk.Grid()
        color_grid.set_column_spacing(10)
        color_grid.set_row_spacing(10)

        row1_colors = [
            ("black", 0, 0, 0),
            ("red", 1, 0, 0),
            ("green", 0, 1, 0),
            ("brown", 0.6, 0.4, 0.2),
            ("blue", 0, 0, 1),
            ("magenta", 1, 0, 1),
            ("cyan", 0, 1, 1),
            ("light-grey", 0.75, 0.75, 0.75)
        ]

        row2_colors = [
            ("grey", 0.5, 0.5, 0.5),
            ("faded red", 1, 0.5, 0.5),
            ("faded green", 0.5, 1, 0.5),
            ("faded brown", 0.65, 0.5, 0.4),
            ("faded blue", 0.5, 0.5, 1),
            ("faded magenta", 1, 0.6, 1),
            ("faded cyan", 0.5, 1, 1),
            ("white", 1, 1, 1)
        ]

        for i, (color_name, r, g, b) in enumerate(row1_colors):
            color_button = Gtk.ColorButton()
            color_button.set_rgba(Gdk.RGBA(r, g, b, 1))
            color_button.set_size_request(65, 40)
            color_button.connect("color-set", self.on_color_selected, color_name)
            color_grid.attach(color_button, i, 0, 1, 1)

        for i, (color_name, r, g, b) in enumerate(row2_colors):
            color_button = Gtk.ColorButton()
            color_button.set_rgba(Gdk.RGBA(r, g, b, 1))
            color_button.set_size_request(65, 40)
            color_button.connect("color-set", self.on_color_selected, color_name)
            color_grid.attach(color_button, i, 1, 1, 1)

        style_box.pack_start(color_grid, False, False, 0)

        bold_font_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        bold_font_checkbox = Gtk.CheckButton(label="")
        bold_font_checkbox.set_active(True)
        bold_font_checkbox.connect("toggled", self.on_bold_font_toggle)

        bold_font_label = Gtk.Label(label="Allow Bold Font")
        bold_font_label.set_halign(Gtk.Align.START)

        bold_font_box.pack_start(bold_font_checkbox, False, False, 0)
        bold_font_box.pack_start(bold_font_label, False, False, 0)

        style_box.pack_start(bold_font_box, False, False, 0)

        bold_bright_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        bold_bright_checkbox = Gtk.CheckButton(label="")
        bold_bright_checkbox.set_active(False)
        bold_bright_checkbox.connect("toggled", self.on_bold_bright_toggle)

        bold_bright_label = Gtk.Label(label="Bold is Bright")
        bold_bright_label.set_halign(Gtk.Align.START)

        bold_bright_box.pack_start(bold_bright_checkbox, False, False, 0)
        bold_bright_box.pack_start(bold_bright_label, False, False, 0)

        style_box.pack_start(bold_bright_box, False, False, 0)

        cursor_blink_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        cursor_blink_checkbox = Gtk.CheckButton(label="")
        cursor_blink_checkbox.set_active(False)
        cursor_blink_checkbox.connect("toggled", self.on_cursor_blink_toggle)

        cursor_blink_label = Gtk.Label(label="Cursor Blink")
        cursor_blink_label.set_halign(Gtk.Align.START)

        cursor_blink_box.pack_start(cursor_blink_checkbox, False, False, 0)
        cursor_blink_box.pack_start(cursor_blink_label, False, False, 0)

        style_box.pack_start(cursor_blink_box, False, False, 0)

        cursor_style_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        cursor_style_label = Gtk.Label(label="Cursor Style:")
        cursor_style_label.set_halign(Gtk.Align.START)

        bold_radio = Gtk.RadioButton.new_with_label_from_widget(None, "Bold")
        underline_radio = Gtk.RadioButton.new_with_label_from_widget(bold_radio, "Underline")

        cursor_style_box.pack_start(cursor_style_label, False, False, 0)
        cursor_style_box.pack_start(bold_radio, False, False, 0)
        cursor_style_box.pack_start(underline_radio, False, False, 0)

        bold_radio.set_size_request(30, 30)
        underline_radio.set_size_request(30, 30)

        spacer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        spacer_box.pack_start(cursor_style_box, False, False, 8)

        style_box.pack_start(spacer_box, False, False, 0)

        audible_bell_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        audible_bell_checkbox = Gtk.CheckButton(label="")
        audible_bell_checkbox.set_active(False)
        audible_bell_checkbox.connect("toggled", self.on_audible_bell_toggle)

        audible_bell_label = Gtk.Label(label="Audible Bell")
        audible_bell_label.set_halign(Gtk.Align.START)

        audible_bell_box.pack_start(audible_bell_checkbox, False, False, 0)
        audible_bell_box.pack_start(audible_bell_label, False, False, 0)

        style_box.pack_start(audible_bell_box, False, False, 0)

        visual_bell_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        visual_bell_checkbox = Gtk.CheckButton(label="")
        visual_bell_checkbox.set_active(False)
        visual_bell_checkbox.connect("toggled", self.on_visual_bell_toggle)

        visual_bell_label = Gtk.Label(label="Visual Bell")
        visual_bell_label.set_halign(Gtk.Align.START)

        visual_bell_box.pack_start(visual_bell_checkbox, False, False, 0)
        visual_bell_box.pack_start(visual_bell_label, False, False, 0)

        style_box.pack_start(visual_bell_box, False, False, 0)

        return style_box

    def on_select_background_color(self, widget):
        pass

    def on_select_foreground_color(self, widget):
        pass

    def on_font_set(self, font_button):
        pass

    def on_audible_bell_toggle(self, widget):
        pass

    def on_visual_bell_toggle(self, widget):
        pass

    def on_color_selected(self, widget, color_name):
        pass

    def on_edit_palette(self, widget):
        pass

    def on_bold_font_toggle(self, checkbox):
        pass

    def on_bold_bright_toggle(self, checkbox):
        pass

    def on_cursor_blink_toggle(self, checkbox):
        pass

    def create_display_content(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        hbox_position = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        position_label = Gtk.Label(label="Top panel position:")
        position_label.set_halign(Gtk.Align.START)
        position_label.set_valign(Gtk.Align.CENTER)
        position_label.set_margin_start(0)
        hbox_position.pack_start(position_label, False, True, 0)

        position_combo = Gtk.ComboBoxText()
        position_combo.append_text("Top")
        position_combo.append_text("Bottom")
        position_combo.append_text("Left")
        position_combo.append_text("Right")
        position_combo.set_active(0)
        position_combo.set_size_request(260, -1)
        hbox_position.pack_start(position_combo, False, False, 10)

        box.pack_start(hbox_position, False, False, 0)

        hbox_window_size = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        default_window_size_label = Gtk.Label(label="Default window size:")
        default_window_size_label.set_halign(Gtk.Align.START)
        default_window_size_label.set_valign(Gtk.Align.CENTER)
        default_window_size_label.set_margin_start(0)
        hbox_window_size.pack_start(default_window_size_label, False, True, 0)

        width_spinbutton = Gtk.SpinButton()
        width_spinbutton.set_adjustment(Gtk.Adjustment(
            value=80, lower=10, upper=500, step_increment=1, page_increment=10, page_size=0))
        width_spinbutton.set_numeric(True)
        width_spinbutton.set_value(80)
        width_spinbutton.set_size_request(60, -1)
        hbox_window_size.pack_start(width_spinbutton, False, False, 0)

        hbox_window_size.pack_start(Gtk.Label(label="x"), False, False, 0)

        height_spinbutton = Gtk.SpinButton()
        height_spinbutton.set_adjustment(Gtk.Adjustment(
            value=24, lower=10, upper=200, step_increment=1, page_increment=10, page_size=0))
        height_spinbutton.set_numeric(True)
        height_spinbutton.set_value(24)
        height_spinbutton.set_size_request(60, -1)
        hbox_window_size.pack_start(height_spinbutton, False, False, 0)

        box.pack_start(hbox_window_size, False, False, 0)

        hbox_scrollback = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        scrollback_label = Gtk.Label(label="Scrollback lines:")
        scrollback_label.set_halign(Gtk.Align.START)
        scrollback_label.set_valign(Gtk.Align.CENTER)
        scrollback_label.set_margin_start(0)
        hbox_scrollback.pack_start(scrollback_label, False, True, 0)

        scrollback_spinbutton = Gtk.SpinButton()
        scrollback_spinbutton.set_adjustment(Gtk.Adjustment(
            value=1000, lower=0, upper=10000, step_increment=1, page_increment=10, page_size=0))
        scrollback_spinbutton.set_numeric(True)
        scrollback_spinbutton.set_value(1000)
        scrollback_spinbutton.set_size_request(265, -1)
        hbox_scrollback.pack_start(scrollback_spinbutton, False, False, 30)

        box.pack_start(hbox_scrollback, False, False, 0)

        hbox_hide_scrollbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hide_scrollbar_toggle = Gtk.CheckButton(label="")
        hbox_hide_scrollbar.pack_start(hide_scrollbar_toggle, False, False, 0)

        hide_scrollbar_label = Gtk.Label(label="Hide scroll bar")
        hide_scrollbar_label.set_halign(Gtk.Align.START)
        hide_scrollbar_label.set_valign(Gtk.Align.CENTER)
        hide_scrollbar_label.set_margin_start(0)
        hbox_hide_scrollbar.pack_start(hide_scrollbar_label, False, True, 5)
        box.pack_start(hbox_hide_scrollbar, False, False, 0)

        hbox_hide_menubar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hide_menubar_toggle = Gtk.CheckButton(label="")
        hbox_hide_menubar.pack_start(hide_menubar_toggle, False, False, 0)

        hide_menubar_label = Gtk.Label(label="Hide menu bar")
        hide_menubar_label.set_halign(Gtk.Align.START)
        hide_menubar_label.set_valign(Gtk.Align.CENTER)
        hide_menubar_label.set_margin_start(0)
        hbox_hide_menubar.pack_start(hide_menubar_label, False, True, 5)
        box.pack_start(hbox_hide_menubar, False, False, 0)

        hbox_hide_close_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hide_close_buttons_toggle = Gtk.CheckButton(label="")
        hbox_hide_close_buttons.pack_start(hide_close_buttons_toggle, False, False, 0)

        hide_close_buttons_label = Gtk.Label(label="Hide close buttons")
        hide_close_buttons_label.set_halign(Gtk.Align.START)
        hide_close_buttons_label.set_valign(Gtk.Align.CENTER)
        hide_close_buttons_label.set_margin_start(0)
        hbox_hide_close_buttons.pack_start(hide_close_buttons_label, False, True, 5)
        box.pack_start(hbox_hide_close_buttons, False, False, 0)

        hbox_hide_mouse_pointer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hide_mouse_pointer_toggle = Gtk.CheckButton(label="")
        hbox_hide_mouse_pointer.pack_start(hide_mouse_pointer_toggle, False, False, 0)

        hide_mouse_pointer_label = Gtk.Label(label="Hide mouse pointer")
        hide_mouse_pointer_label.set_halign(Gtk.Align.START)
        hide_mouse_pointer_label.set_valign(Gtk.Align.CENTER)
        hide_mouse_pointer_label.set_margin_start(0)
        hbox_hide_mouse_pointer.pack_start(hide_mouse_pointer_label, False, True, 5)
        box.pack_start(hbox_hide_mouse_pointer, False, False, 0)

        return box

    def on_width_minus_clicked(self, button, width_entry):
        current_width = int(width_entry.get_text())
        if current_width > 1:
            new_width = current_width - 1
            width_entry.set_text(str(new_width))

    def on_width_plus_clicked(self, button, width_entry):
        current_width = int(width_entry.get_text())
        new_width = current_width + 1
        width_entry.set_text(str(new_width))

    def on_height_minus_clicked(self, button, height_entry):
        current_height = int(height_entry.get_text())
        if current_height > 1:
            new_height = current_height - 1
            height_entry.set_text(str(new_height))

    def on_height_plus_clicked(self, button, height_entry):
        current_height = int(height_entry.get_text())
        new_height = current_height + 1
        height_entry.set_text(str(new_height))

    def on_minus_clicked(self, button, entry):
        current_value = int(entry.get_text())
        if current_value > 0:
            entry.set_text(str(current_value - 1))

    def on_plus_clicked(self, button, entry):
        current_value = int(entry.get_text())
        entry.set_text(str(current_value + 1))

    def create_advanced_content(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        select_by_word_label = Gtk.Label(label="Select-by-word characters:")
        select_by_word_label.set_halign(Gtk.Align.START)
        hbox.pack_start(select_by_word_label, False, False, 0)

        character_entry = Gtk.Entry()
        character_entry.set_text("-A-Za-z0-9,./?%&#:_")
        hbox.pack_start(character_entry, False, False, 0)

        box.pack_start(hbox, False, False, 0)

        hbox_menu_shortcut = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        menu_shortcut_checkbox = Gtk.CheckButton()
        hbox_menu_shortcut.pack_start(menu_shortcut_checkbox, False, False, 0)

        menu_shortcut_label = Gtk.Label(label="Disable menu shortcut key (F10 by default)")
        menu_shortcut_label.set_halign(Gtk.Align.START)
        hbox_menu_shortcut.pack_start(menu_shortcut_label, False, False, 0)

        box.pack_start(hbox_menu_shortcut, False, False, 0)

        hbox_alt_n = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        alt_n_checkbox = Gtk.CheckButton()
        hbox_alt_n.pack_start(alt_n_checkbox, False, False, 0)

        alt_n_label = Gtk.Label(label="Disable using Alt-n for tabs and menu")
        alt_n_label.set_halign(Gtk.Align.START)
        hbox_alt_n.pack_start(alt_n_label, False, False, 0)

        box.pack_start(hbox_alt_n, False, False, 0)

        hbox_confirmation = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        confirmation_checkbox = Gtk.CheckButton()
        hbox_confirmation.pack_start(confirmation_checkbox, False, False, 0)

        confirmation_label = Gtk.Label(label="Disable confirmation before closing a window with multiple tabs")
        confirmation_label.set_halign(Gtk.Align.START)
        hbox_confirmation.pack_start(confirmation_label, False, False, 0)

        box.pack_start(hbox_confirmation, False, False, 0)

        return box

    def create_shortcuts_content(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        grid = Gtk.Grid(row_spacing=6, column_spacing=10)

        shortcuts = [
            ("New Window:", "Shift+Ctrl+N"),
            ("New Tab:", "Shift+Ctrl+T"),
            ("Close Tab:", "Shift+Ctrl+W"),
            ("Close Window:", "Shift+Ctrl+Q"),
            ("Copy:", "Shift+Ctrl+C"),
            ("Paste:", "Shift+Ctrl+V"),
            ("Zoom In:", "Shift+Ctrl++"),
            ("Zoom Out:", "Shift+Ctrl+_"),
            ("Zoom Reset:", "Shift+Ctrl+)"),
            ("Name Tab:", "Shift+Ctrl+I"),
            ("Previous Tab:", "Shift+Ctrl+Left"),
            ("Next Tab:", "Shift+Ctrl+Right"),
            ("Move Tab Left:", "Shift+Ctrl+Page Up"),
            ("Move Tab Right:", "Shift+Ctrl+Page Down"),
            ("Move Window Left:", "Ctrl+Left"),
            ("Move Window Right:", "Ctrl+Right"),
            ("Enter Fullsreen:", "Shift+Ctrl+F"),
            ("Exit Fullscreen:", "Shift+Ctrl+Esc"),
            ("Increase Window Size:", "Ctrl+Alt+9"),
            ("Decrease Window Size:", "Ctrl+Alt+8"),
            ("Reset Window Size:", "Shift+Ctrl+)")

        ]

        for row, (label_text, shortcut) in enumerate(shortcuts):
            label = Gtk.Label(label=label_text)
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)
            grid.attach(label, 0, row, 1, 1)

            shortcut_entry = Gtk.Entry()
            shortcut_entry.set_text(shortcut)
            grid.attach(shortcut_entry, 1, row, 1, 1)

        grid.set_column_homogeneous(True)
        grid.set_column_spacing(10)

        box.pack_start(grid, True, True, 0)

        return box

    def on_previous_tab(self, widget):
        current_page = self.notebook.get_current_page()
        if current_page > 0:
            self.notebook.set_current_page(current_page - 1)

    def on_next_tab(self, widget):
        current_page = self.notebook.get_current_page()
        if current_page < self.notebook.get_n_pages() - 1:
            self.notebook.set_current_page(current_page + 1)

    def on_move_tab_left(self, widget):
        current_page = self.notebook.get_current_page()
        if current_page > 0:
            child = self.notebook.get_nth_page(current_page)
            tab_label = self.notebook.get_tab_label(child)
            self.notebook.remove_page(current_page)
            self.notebook.insert_page(child, tab_label, current_page - 1)
            self.notebook.set_current_page(current_page - 1)

    def on_move_tab_right(self, widget):
        current_page = self.notebook.get_current_page()
        if current_page < self.notebook.get_n_pages() - 1:
            child = self.notebook.get_nth_page(current_page)
            tab_label = self.notebook.get_tab_label(child)
            self.notebook.remove_page(current_page)
            self.notebook.insert_page(child, tab_label, current_page + 1)
            self.notebook.set_current_page(current_page + 1)

    def on_move_left(self, widget):
        print("Window moved left.")

    def on_move_right(self, widget):
        print("Window moved right.")

    def on_fullscreen(self, widget):
        self.fullscreen()

    def on_exit_fullscreen(self, widget):
        self.unfullscreen()

    def on_increase_size(self, widget):
        current_width, current_height = self.get_size()
        new_width = int(current_width * 1.1)
        new_height = int(current_height * 1.1)
        self.resize(new_width, new_height)

    def on_decrease_size(self, widget):
        current_width, current_height = self.get_size()
        new_width = int(current_width * 0.9)
        new_height = int(current_height * 0.9)
        self.resize(new_width, new_height)

    def on_reset_size(self, widget):
        default_width = 650
        default_height = 500
        self.resize(default_width, default_height)

    def on_search(self, widget):
        search_window = Gtk.Window(title="Search")
        search_window.set_border_width(10)
        search_window.set_default_size(300, 150)
        search_window.set_resizable(False)

        search_window.set_icon_from_file("/usr/share/icons/hicolor/24x24/apps/preferences-system-search-symbolic.svg")

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        search_window.add(vbox)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        vbox.pack_start(hbox, False, False, 0)

        search_entry = Gtk.Entry()
        search_entry.set_placeholder_text("Enter search term...")
        hbox.pack_start(search_entry, True, True, 0)

        up_button = Gtk.Button(label="↑")
        hbox.pack_start(up_button, False, False, 0)

        down_button = Gtk.Button(label="↓")
        hbox.pack_start(down_button, False, False, 0)

        case_checkbox = Gtk.CheckButton(label="Match Case")
        word_checkbox = Gtk.CheckButton(label="Match Entire Word Only")
        regex_checkbox = Gtk.CheckButton(label="Use as Regular Expression")
        wrap_checkbox = Gtk.CheckButton(label="Wrap Around")

        vbox.pack_start(case_checkbox, False, False, 0)
        vbox.pack_start(word_checkbox, False, False, 0)
        vbox.pack_start(regex_checkbox, False, False, 0)
        vbox.pack_start(wrap_checkbox, False, False, 0)

        search_button = Gtk.Button(label="Search")
        vbox.pack_start(search_button, False, False, 0)

        search_button.connect("clicked", lambda btn: self.perform_search(search_entry.get_text(), case_checkbox.get_active(), word_checkbox.get_active(), regex_checkbox.get_active(), wrap_checkbox.get_active(), search_window))
        up_button.connect("clicked", lambda btn: print("Up arrow clicked"))
        down_button.connect("clicked", lambda btn: print("Down arrow clicked"))

        search_window.show_all()

    def on_about(self, widget):
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_program_name("IllumiTerm")
        about_dialog.set_version("1.0.0")
        about_dialog.set_comments("Terminal Emulator in GTK-3.0")

        about_dialog.set_license_type(Gtk.License.GPL_2_0)

        about_dialog.set_icon_from_file("/usr/share/icons/hicolor/24x24/apps/about.png")
        about_dialog.set_website("https://www.illumiterm.blogspot.com")
        about_dialog.set_website_label("Website")
        about_dialog.set_authors(["Elijah Gordon <NitrixXero@gmail.com>"])
        about_dialog.set_copyright("Copyright (C) 2024-2025 Elijah Gordon")

        logo_icon = Gtk.Image.new_from_file("/usr/share/icons/hicolor/24x24/apps/about.png")
        about_dialog.set_logo(logo_icon.get_pixbuf())

        about_dialog.run()
        about_dialog.destroy()

    def destroy(self):
        global open_windows
        open_windows -= 1
        if open_windows == 0:
            Gtk.main_quit()
        else:
            super().destroy()

if __name__ == "__main__":
    try:
        win = TerminalWindow()
        win.show_all()
        Gtk.main()
    except KeyboardInterrupt:
        pass
