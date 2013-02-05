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
import difflib

class LineContext:
    def __init__(self):
        self.line_num = 0
        self.removed_lines = []
        self.line_type = DiffType.NONE

class DiffThread(threading.Thread):
    def __init__(self, doc, finishcb):
        threading.Thread.__init__(self)

        self.location = doc.get_location()

        bounds = doc.get_bounds()
        self.source_contents = bounds[0].get_text(bounds[1])

        self.clock = threading.Lock()
        self.cancelled = False
        self.finishcb = finishcb
        self.file_context = {}

        self.idle_finish = 0

    def cancel(self):
        self.clock.acquire()
        self.cancelled = True

        if self.idle_finish != 0:
            GLib.source_remove(self.idle_finish)

        self.clock.release()

    def finish_in_idle(self):
        self.finishcb(self.file_context)

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

            # convert data to list of lines
            src_contents_list = self.source_contents.splitlines(True)
            file_blob_list = file_blob.get_raw_content().decode('utf-8').splitlines(True)

            # remove the last empty line added by gedit
            last_item = file_blob_list[len(file_blob_list) -1]
            if last_item[-1:] == '\n':
                file_blob_list[len(file_blob_list) -1] = last_item[:-1]

            diff = difflib.unified_diff(file_blob_list, src_contents_list, n=0)
            # skip first 2 lines: ---, +++
            next(diff)
            next(diff)

            hunk = 0
            hunk_point = 0
            for line_data in diff:
                if line_data[0] == '@':
                    t = [token for token in line_data.split() if token[0] == '+']
                    t = t[0]
                    hunk = int(t.split(',')[0])
                    hunk_point = hunk
                elif line_data[0] == '-':
                    # no hunk point increase
                    if hunk_point in self.file_context:
                        line_context = self.file_context[hunk_point]
                        line_context.removed_lines.append(line_data[1:])
                    else:
                        line_context = LineContext()
                        line_context.line_type = DiffType.REMOVED
                        line_context.removed_lines.append(line_data[1:])
                        self.file_context[hunk_point] = line_context
                elif line_data[0] == '+':
                    if hunk_point in self.file_context:
                        line_context = self.file_context[hunk_point]
                        if line_context.line_type == DiffType.REMOVED:
                            line_context.line_type = DiffType.MODIFIED
                    else:
                        line_context = LineContext()
                        line_context.line_type = DiffType.ADDED
                        self.file_context[hunk_point] = line_context

                    hunk_point += 1
        except StopIteration:
            pass
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
        self.gutter = self.view.get_gutter(Gtk.TextWindowType.LEFT)
        self.gutter.insert(self.diff_renderer, 40)

        self._buffer = self.view.get_buffer()

        self._view_signals = [
            self.view.connect('notify::buffer', self.on_notify_buffer),
        ]

        self._connect_buffer()

        self.update()

    def _connect_buffer(self):
        self._buffer_signals = [
            self._buffer.connect('loaded', self.on_loaded),
            self._buffer.connect('changed', self.on_changed)
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
        if self.diff_timeout != 0:
            GLib.source_remove(self.diff_timeout)

        self._disconnect_buffer()
        self._disconnect_view()
        self.gutter.remove(self.diff_renderer)

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

    def on_changed(self, doc):
        self.update()

    def update(self, args=None):
        # Need to parse ourselves again
        if self.diff_timeout != 0:
            GLib.source_remove(self.diff_timeout)

        if self.diff_thread != None:
            self.diff_thread.cancel()
            self.diff_thread = None

        # do nothing if it is an unsaved document
        if not self._buffer.get_location():
            return

        self.diff_timeout = GLib.timeout_add(300, self.on_diff_timeout)

    def on_diff_timeout(self):
        self.diff_timeout = 0

        self.diff_thread = DiffThread(self._buffer, self.on_diff_finished)
        self.diff_thread.run()

        return False

    def on_diff_finished(self, file_context):
        self.diff_renderer.set_data(file_context)

# ex:ts=4:et:
