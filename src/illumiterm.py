#!/usr/bin/env python3

# Copyright 2022 Elijah Gordon (NitrixXero) <nitrixxero@gmail.com>

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

import os
import socket
import signal
import subprocess

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')

from gi.repository import Gtk, Vte, Gdk  # noqa: E402

print("[+] VTE version loaded:", Vte.MAJOR_VERSION, Vte.MINOR_VERSION, Vte.MICRO_VERSION)
print("[+] GTK version loaded:", Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())

open_windows = 0


class TerminalWindow(Gtk.Window):
    def __init__(self, cwd=None):
        super().__init__()
        global open_windows
        open_windows += 1

        self.tab_labels = {}
        self.child_pid = None

        self.set_icon_from_file("/usr/share/icons/hicolor/24x24/apps/about.png")
        self.set_default_size(650, 500)

        self.accel_group = Gtk.AccelGroup()
        self.add_accel_group(self.accel_group)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)

        self.create_menu_bar(vbox)

        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.connect("switch-page", self.on_switch_page)
        vbox.pack_start(self.notebook, True, True, 0)

        self.terminal = Vte.Terminal()
        self.add_terminal_tab(cwd=cwd)

        self.connect("delete-event", self.on_delete_event)
        self.connect("destroy", self.on_destroy)

        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        self.set_titlebar(header_bar)

        self.connect("button-press-event", self.on_right_click)
        self.add_context_menu()

    def create_menu_bar(self, container):
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
                if key:
                    menu_item.add_accelerator("activate", self.accel_group, key, mod, Gtk.AccelFlags.VISIBLE)

            menu_item.connect("activate", callback)
            menu_item.show_all()

            return menu_item

        file_menu = Gtk.Menu()
        file_item = Gtk.MenuItem(label="File")
        file_item.set_tooltip_text("File menu")
        file_item.set_submenu(file_menu)
        menubar.append(file_item)

        file_menu.append(create_menu_item("New Window", "/usr/share/icons/hicolor/24x24/apps/window-new.svg",
                                          "Shift+Ctrl+N", "<Shift><Control>N", self.on_new_window))
        file_menu.append(create_menu_item("New Tab", "/usr/share/icons/hicolor/24x24/apps/tab-new.svg",
                                          "Shift+Ctrl+T", "<Shift><Control>T", self.on_new_tab))
        file_menu.append(Gtk.SeparatorMenuItem())
        file_menu.append(create_menu_item("Close Tab", "/usr/share/icons/hicolor/24x24/apps/tab-close.svg",
                                          "Shift+Ctrl+W", "<Shift><Control>W", self.on_close_tab))
        file_menu.append(create_menu_item("Close Window", "/usr/share/icons/hicolor/24x24/apps/window-close.svg",
                                          "Shift+Ctrl+Q", "<Shift><Control>Q", self.on_close_window))

        edit_menu = Gtk.Menu()
        edit_item = Gtk.MenuItem(label="Edit")
        edit_item.set_tooltip_text("Edit menu")
        edit_item.set_submenu(edit_menu)
        menubar.append(edit_item)

        edit_menu.append(create_menu_item("Copy", "/usr/share/icons/hicolor/24x24/apps/edit-copy.svg",
                                          "Shift+Ctrl+C", "<Shift><Control>C", self.on_copy))
        edit_menu.append(create_menu_item("Paste", "/usr/share/icons/hicolor/24x24/apps/edit-paste.svg",
                                          "Shift+Ctrl+V", "<Shift><Control>V", self.on_paste))
        edit_menu.append(Gtk.SeparatorMenuItem())
        edit_menu.append(create_menu_item("Clear Scrollback", "/usr/share/icons/hicolor/24x24/apps/edit-clear.svg",
                                          "", "", self.on_clear_scrollback))
        edit_menu.append(Gtk.SeparatorMenuItem())
        edit_menu.append(create_menu_item("Zoom In", "/usr/share/icons/hicolor/24x24/apps/zoom-in.svg",
                                          "Shift+Ctrl++", "<Shift><Control>plus", self.on_zoom_in))
        edit_menu.append(create_menu_item("Zoom Out", "/usr/share/icons/hicolor/24x24/apps/zoom-out.svg",
                                          "Shift+Ctrl+_", "<Shift><Control>underscore", self.on_zoom_out))
        edit_menu.append(create_menu_item("Zoom Reset", "/usr/share/icons/hicolor/24x24/apps/zoom-original.svg",
                                          "Shift+Ctrl+)", "<Shift><Control>parenright", self.on_zoom_reset))
        edit_menu.append(Gtk.SeparatorMenuItem())

        tabs_menu = Gtk.Menu()
        tabs_item = Gtk.MenuItem(label="Tabs")
        tabs_item.set_tooltip_text("Tabs menu")
        tabs_item.set_submenu(tabs_menu)
        menubar.append(tabs_item)

        tabs_menu.append(create_menu_item("Name Tab", "/usr/share/icons/hicolor/24x24/apps/edit.svg",
                                          "Shift+Ctrl+I", "<Shift><Control>I", self.on_name_tab))
        tabs_menu.append(Gtk.SeparatorMenuItem())
        tabs_menu.append(create_menu_item("Previous Tab", "/usr/share/icons/hicolor/24x24/apps/go-previous.svg",
                                          "Shift+Ctrl+L", "<Control><Shift>L", self.on_previous_tab))
        tabs_menu.append(create_menu_item("Next Tab", "/usr/share/icons/hicolor/24x24/apps/go-next.svg",
                                          "Shift+Ctrl+R", "<Shift><Control>R", self.on_next_tab))
        tabs_menu.append(Gtk.SeparatorMenuItem())
        tabs_menu.append(create_menu_item("Move Tab Left", "/usr/share/icons/hicolor/24x24/apps/go-up.svg",
                                          "Shift+Ctrl+Page Up", "<Shift><Control>Page_Up", self.on_move_tab_left))
        tabs_menu.append(create_menu_item("Move Tab Right", "/usr/share/icons/hicolor/24x24/apps/go-down.svg",
                                          "Shift+Ctrl+Page Down", "<Shift><Control>Page_Down", self.on_move_tab_right))

        misc_menu = Gtk.Menu()
        misc_item = Gtk.MenuItem(label="Misc")
        misc_item.set_tooltip_text("Misc menu")
        misc_item.set_submenu(misc_menu)
        menubar.append(misc_item)

        misc_menu.append(create_menu_item("Move Window Left", "/usr/share/icons/hicolor/24x24/apps/go-previous.svg",
                                          "Ctrl+Left", "<Control>Left", self.on_move_left))
        misc_menu.append(create_menu_item("Move Window Right", "/usr/share/icons/hicolor/24x24/apps/go-next.svg",
                                          "Ctrl+Right", "<Control>Right", self.on_move_right))
        misc_menu.append(Gtk.SeparatorMenuItem())
        misc_menu.append(create_menu_item("Enter Fullscreen", "/usr/share/icons/hicolor/24x24/apps/go-up.svg",
                                          "Shift+Ctrl+F", "<Shift><Control>F", self.on_fullscreen))
        misc_menu.append(create_menu_item("Exit Fullscreen", "/usr/share/icons/hicolor/24x24/apps/go-down.svg",
                                          "Shift+Ctrl+Esc", "<Shift><Control>Escape", self.on_exit_fullscreen))
        misc_menu.append(Gtk.SeparatorMenuItem())
        misc_menu.append(create_menu_item("Increase Window Size", "/usr/share/icons/hicolor/24x24/apps/zoom-in.svg",
                                          "Ctrl+Alt+8", "<Control><Alt>8", self.on_increase_size))
        misc_menu.append(create_menu_item("Decrease Window Size", "/usr/share/icons/hicolor/24x24/apps/zoom-out.svg",
                                          "Ctrl+Alt+9", "<Control><Alt>9", self.on_decrease_size))
        misc_menu.append(create_menu_item("Reset Window Size", "/usr/share/icons/hicolor/24x24/apps/zoom-original.svg",
                                          "Ctrl+Alt+0", "<Control><Alt>0", self.on_reset_size))

        help_menu = Gtk.Menu()
        help_item = Gtk.MenuItem(label="Help")
        help_item.set_tooltip_text("Help menu")
        help_item.set_submenu(help_menu)
        menubar.append(help_item)

        about_item = Gtk.MenuItem()
        about_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        about_icon = Gtk.Image.new_from_file("/usr/share/icons/hicolor/24x24/apps/help-about.svg")
        about_label = Gtk.Label(label="About")

        about_box.pack_start(about_icon, False, False, 0)
        about_box.pack_start(about_label, True, True, 0)
        about_item.add(about_box)
        about_item.connect("activate", self.on_about)
        help_menu.append(about_item)

        container.pack_start(menubar, False, False, 0)

    def add_context_menu(self):
        self.context_menu = Gtk.Menu()

        def add_menu_item(label_text, icon_path, callback):
            menu_item = Gtk.MenuItem()
            icon = Gtk.Image.new_from_file(icon_path)

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.set_halign(Gtk.Align.START)

            icon.set_size_request(24, 24)
            box.pack_start(icon, False, False, 0)

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

    def update_tab_label(self, tab_widget, new_title):
        tab_data = self.tab_labels.get(tab_widget)

        if tab_data:
            label_text = tab_data.get('custom_title') or new_title
            display_title = label_text[:14] + "..." if len(label_text) > 14 else label_text
            tab_data['label'].set_text(display_title)

            tooltip_text = tab_data.get('original_title') or new_title
            tab_data['label'].set_tooltip_text(tooltip_text)
            tab_data['tab_box'].set_tooltip_text(tooltip_text)

            current_page = self.notebook.get_current_page()

            if current_page != -1:
                current_tab = self.notebook.get_nth_page(current_page)

                if current_tab == tab_widget:
                    self.set_title(label_text)

    def add_terminal_tab(self, cwd=None):
        terminal = Vte.Terminal()
        terminal.set_scroll_on_output(True)
        terminal.set_scroll_on_keystroke(True)

        if cwd is None:
            cwd = os.getcwd()
            current_terminal = self.get_current_terminal()
            if current_terminal and hasattr(current_terminal, "pid"):
                cwd = os.readlink(f"/proc/{current_terminal.pid}/cwd")

        self.spawn_shell(terminal, cwd=cwd)

        terminal.connect("key-press-event", self.on_key_press)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        scrolled_window.set_overlay_scrolling(False)
        scrolled_window.add(terminal)

        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        hostname = socket.gethostname()
        tab_label = Gtk.Label(label=f"{hostname}: {cwd}")

        close_button = Gtk.Button.new_from_icon_name("window-close", Gtk.IconSize.MENU)
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.set_focus_on_click(False)

        tab_box.pack_start(tab_label, True, True, 0)
        tab_box.pack_start(close_button, False, False, 0)
        tab_box.show_all()

        terminal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        terminal_box.pack_start(scrolled_window, True, True, 0)

        self.notebook.append_page(terminal_box, tab_box)
        self.notebook.set_tab_reorderable(terminal_box, True)
        self.notebook.show_all()

        self.tab_labels[terminal_box] = {
            'label': tab_label,
            'tab_box': tab_box,
            'dynamic': True,
            'custom_title': None
        }

        terminal.connect("window-title-changed", lambda term: self.on_title_changed(term, terminal_box))
        close_button.connect("clicked", self.on_close_tab, terminal_box)
        terminal.connect("child-exited", lambda term, status: self.on_child_exited(terminal_box, status))
        terminal.connect("eof", self.on_eof)

        self.update_tab_label(terminal_box, f"{hostname}: {cwd}")
        self.notebook.set_current_page(self.notebook.page_num(terminal_box))
        self.set_title(f"{hostname}: {cwd}")

    def focus_current_terminal(self):
        terminal = self.get_current_terminal()

        if terminal:
            terminal.grab_focus()
            terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)

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

    def spawn_shell(self, terminal, cwd=None):
        shell = os.environ.get('SHELL', '/bin/bash')
        cwd = cwd or os.environ.get("HOME")

        def on_spawned(terminal, pid, error, user_data):
            if pid > 0:
                terminal.pid = pid
                self.child_pid = pid

            terminal.grab_focus()
            terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)

        banner_cmd = (
            'echo \'To run a command as administrator (user "root"), use "sudo <command>".\'; '
            'echo \'See "man sudo_root" for details.\'; '
            'echo; '
            'exec bash'
        )

        terminal.spawn_async(
            Vte.PtyFlags.DEFAULT,
            cwd,
            [shell, "-c", banner_cmd],
            [],
            0,
            None,
            None,
            -1,
            None,
            on_spawned,
            None
        )

        self.connect("delete-event", self.on_window_delete)

    def shell_has_running_child(self):
        try:
            output = subprocess.check_output(
                ['ps', '--no-headers', '--ppid', str(self.child_pid), '-o', 'pid'],
                text=True
            ).strip()

            return bool(output)

        except subprocess.CalledProcessError:
            return False

    def on_child_exited(self, terminal_box, status):
        page_num = self.notebook.page_num(terminal_box)

        if page_num != -1:
            self.notebook.remove_page(page_num)

            if page_num in self.tab_labels:
                del self.tab_labels[page_num]

            current_page = self.notebook.get_current_page()

            if current_page != -1:
                tab_label_data = self.tab_labels.get(current_page)

                if tab_label_data and tab_label_data['custom_title']:
                    self.set_title(tab_label_data['custom_title'])
                else:
                    self.set_title("Terminal")
            else:
                self.set_title("No tabs")

    def on_eof(self, terminal):
        current_page = self.notebook.get_current_page()
        self.notebook.remove_page(current_page)

        if self.notebook.get_n_pages() == 0:
            self.destroy()

    def on_title_changed(self, terminal, tab_widget):
        current_title = terminal.get_window_title()
        tab_data = self.tab_labels.get(tab_widget)

        if tab_data:
            tab_data['original_title'] = current_title

            if tab_data['dynamic'] and not tab_data['custom_title']:
                self.update_tab_label(tab_widget, current_title)
            else:
                self.update_tab_label(tab_widget, tab_data.get('custom_title'))

    def on_switch_page(self, notebook, page, page_num):
        terminal_box = self.notebook.get_nth_page(page_num)
        terminal = terminal_box.get_children()[0].get_child()
        tab_data = self.tab_labels.get(terminal_box)

        if tab_data:
            if tab_data.get('custom_title'):
                title = tab_data.get('title', 'Terminal')
            else:
                current_directory = terminal.get_window_title() or os.getcwd()
                title = current_directory

            self.set_title(title)
            self.update_tab_label(terminal_box, title)

    def on_right_click(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            self.context_menu.popup_at_pointer(event)
            return True

    def on_key_press(self, terminal, key_event):
        keyval = key_event.keyval
        state = Gdk.ModifierType(key_event.state)

        if keyval == Gdk.KEY_d and state & Gdk.ModifierType.CONTROL_MASK:
            self.on_eof(terminal)
            return True

        return False

    def on_name_tab(self, widget):
        page_num = self.notebook.get_current_page()
        if page_num == -1:
            return

        tab_widget = self.notebook.get_nth_page(page_num)
        tab_data = self.tab_labels.get(tab_widget)

        if not tab_data:
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

        def on_entry_activate(entry):
            dialog.response(Gtk.ResponseType.OK)

        entry.connect("activate", on_entry_activate)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            new_name = entry.get_text().strip() or "Terminal"
            tab_data["custom_title"] = new_name
            tab_data["dynamic"] = False
            tab_data["title"] = new_name

            self.set_title(new_name)
            self.update_tab_label(tab_widget, new_name)

        dialog.destroy()

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
        self.unmaximize()

        while Gtk.events_pending():
            Gtk.main_iteration()

        _, y = self.get_position()
        self.move(0, y)

    def on_move_right(self, widget):
        self.unmaximize()

        while Gtk.events_pending():
            Gtk.main_iteration()

        display = Gdk.Display.get_default()

        total_width = 0
        n_monitors = display.get_n_monitors()
        for i in range(n_monitors):
            monitor = display.get_monitor(i)
            geometry = monitor.get_geometry()
            total_width += geometry.width

        width, _ = self.get_size()
        _, y = self.get_position()

        self.move(total_width - width, y)

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
            terminal.reset(clear_tabstops=False, clear_history=True)

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

    def on_new_window(self, widget):
        cwd = os.path.expanduser("~")

        current_terminal = self.get_current_terminal()
        if current_terminal and hasattr(current_terminal, "pid"):
            cwd = os.readlink(f"/proc/{current_terminal.pid}/cwd")

        new_window = TerminalWindow(cwd=cwd)
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

        if self.child_pid and self.shell_has_running_child():
            self.show_close_warning()
        elif num_tabs > 1:
            self.show_warning_dialog(num_tabs)
        else:
            self.destroy()

    def on_window_delete(self, widget, event):
        if self.child_pid and self.shell_has_running_child():
            self.show_close_warning()
            return True

        return False

    def on_delete_event(self, widget, event):
        num_tabs = self.notebook.get_n_pages()

        if num_tabs > 1:
            self.show_warning_dialog(num_tabs)
            return True

        return False

    def show_close_warning(self):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Close this terminal?"
        )

        dialog.format_secondary_text(
            "There is still a process running in this terminal. "
            "Closing the terminal will terminate it."
        )

        dialog.add_buttons(
            "Cancel", Gtk.ResponseType.CANCEL,
            "Close Terminal", Gtk.ResponseType.ACCEPT
        )

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.ACCEPT:
            self.destroy()

    def show_warning_dialog(self, num_tabs):
        dialog = Gtk.MessageDialog(
            parent=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Warning: You have multiple tabs open!",
        )
        dialog.format_secondary_text(
            f"You currently have {num_tabs} tab(s) open. Are you sure you want to close the application?"
        )

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            self.destroy()

    def on_destroy(self, widget):
        global open_windows

        open_windows -= 1

        if open_windows == 0:
            Gtk.main_quit()

    def on_fullscreen(self, widget):
        self.fullscreen()

    def on_exit_fullscreen(self, widget):
        self.unfullscreen()

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
        about_dialog.set_copyright("Copyright (C) 2022-2026 Elijah Gordon")

        logo_icon = Gtk.Image.new_from_file("/usr/share/icons/hicolor/24x24/apps/about.png")
        about_dialog.set_logo(logo_icon.get_pixbuf())

        about_dialog.run()
        about_dialog.destroy()


def handle_sigint(sig, frame):
    Gtk.main_quit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_sigint)

    win = TerminalWindow()
    win.show_all()
    Gtk.main()
