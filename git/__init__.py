# -*- coding: utf-8 -*-

#  Copyright (C) 2013 - Ignacio Casal Quinteiro
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330,
#  Boston, MA 02111-1307, USA.

from gi.repository import GLib, GObject, Gio, Gdk, Gtk, Gedit, Ggit
from .diffrenderer import DiffType, DiffRenderer

import os
import threading

class DiffThread(threading.Thread):
    def __init__(self, doc, finishcb):
        threading.Thread.__init__(self)

        self.location = doc.get_location()

        bounds = doc.get_bounds()
        self.source_contents = bounds[0].get_text(bounds[1])

        self.clock = threading.Lock()
        self.cancelled = False
        self.finishcb = finishcb
        self.diff_opts = Ggit.DiffOptions.new(Ggit.DiffFlags.FORCE_TEXT, 1, 0, None, None, None)

        self.idle_finish = 0

    def cancel(self):
        self.clock.acquire()
        self.cancelled = True

        if self.idle_finish != 0:
            GLib.source_remove(self.idle_finish)

        self.clock.release()

    def finish_in_idle(self):
        self.finishcb()

    def file_cb(self, delta, progress, user_data):
        print(progress)
        return 0

    def hunk_cb(self, delta, drange, header, user_data):
        return 0

    def line_cb(self, delta, drange, line_type, content, user_data):
        print(line_type)
        print(content)
        return 0

    def run(self):
        try:
            repo_file = Ggit.Repository.discover(self.location)
            repo = Ggit.Repository.open(repo_file)
            head = repo.get_head()
            commit = repo.lookup(head.get_target(), Ggit.Commit.__gtype__)
            tree = commit.get_tree()

            relative_path = repo.get_workdir().get_relative_path(self.location)

            entry = tree.get_by_path(relative_path)
            file_blob = repo.lookup(entry.get_id(), Ggit.Blob.__gtype__)
            Ggit.Diff.blob_to_buffer(self.diff_opts, file_blob, self.source_contents, self.file_cb, self.hunk_cb, self.line_cb, None)
        except Exception as e:
            print(e)
            return

        self.clock.acquire()

        if not self.cancelled:
            self.idle_finish = GLib.idle_add(self.finish_in_idle)

        self.clock.release()

class GitPlugin(GObject.Object, Gedit.ViewActivatable):
    view = GObject.property(type=Gedit.View)

    def __init__(self):
        GObject.Object.__init__(self)

        self.diff_timeout = 0
        self.diff_thread = None

    def do_activate(self):
        Ggit.init()

        self.diff_renderer = DiffRenderer()
        self.diff_renderer.set_type(DiffType.ADDED)
        gutter = self.view.get_gutter(Gtk.TextWindowType.LEFT)
        gutter.insert(self.diff_renderer, 40)

        self._buffer = self.view.get_buffer()

        self._view_signals = [
            self.view.connect('notify::buffer', self.on_notify_buffer),
        ]
        
        self._connect_buffer()

    def _connect_buffer(self):
        self._buffer_signals = [
            self._buffer.connect('loaded', self.on_loaded),
            self._buffer.connect('end-user-action', self.on_end_user_action)
        ]

    def _disconnect(self, obj, signals):
        if obj:
            for sid in signals:
                obj.disconnect(sid)

        return []

    def _disconnect_buffer(self):
        self._buffer_signals = self._disconnect(self._buffer, self._buffer_signals)
        self._buffer_signals = []

    def _disconnect_view(self):
        self._disconnect(self.view, self._view_signals)
        self._view_signals = []

    def do_deactivate(self):
        self._disconnect_buffer()
        self._disconnect_view()

        self._buffer = None

    def do_update_state(self):
        pass

    def on_notify_buffer(self, view, gspec):
        self._disconnect_buffer()

        self._buffer = view.get_buffer()
        self._connect_buffer()
        self.update()

    def on_loaded(self, doc, error):
        self.update()

    def on_end_user_action(self, doc):
        self.update()

    def update(self, args=None):
        # Need to parse ourselves again
        if self.diff_timeout != 0:
            GLib.source_remove(self.diff_timeout)

        if self.diff_thread != None:
            self.diff_thread.cancel()
            self.diff_thread = None

        self.diff_timeout = GLib.timeout_add(300, self.on_diff_timeout)

    def on_diff_timeout(self):
        self.diff_timeout = 0

        self.diff_thread = DiffThread(self._buffer, self.on_diff_finished)
        self.diff_thread.run()

        return False

    def on_diff_finished(self):
        print("on diff finished")

# ex:ts=4:et:
