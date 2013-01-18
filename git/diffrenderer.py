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

from gi.repository import Gdk, Gtk, GtkSource

class DiffType:
    NONE     = 0
    ADDED    = 1
    MODIFIED = 2
    REMOVED  = 3

class DiffRenderer(GtkSource.GutterRenderer):

    def __init__(self):
        GtkSource.GutterRenderer.__init__(self)
        self.diff_type = DiffType.NONE
        self.file_context = {}

        self.set_size(4)
        self.bg_added = Gdk.RGBA()
        self.bg_added.parse("#8ae234")
        self.bg_modified = Gdk.RGBA()
        self.bg_modified.parse("#fcaf3e")
        self.bg_removed = Gdk.RGBA()
        self.bg_removed.parse("#ef2929")

    def do_draw(self, cr, bg_area, cell_area, start, end, state):
        GtkSource.GutterRenderer.do_draw(self, cr, bg_area, cell_area, start, end, state)

        if self.diff_type is not DiffType.NONE:
            bg = None

            if self.diff_type == DiffType.ADDED:
                bg = self.bg_added
            elif self.diff_type == DiffType.MODIFIED:
                bg = self.bg_modified
            elif self.diff_type == DiffType.REMOVED:
                bg = self.bg_removed

            # background
            Gdk.cairo_set_source_rgba(cr, bg)
            cr.rectangle(cell_area.x, cell_area.y, cell_area.width, cell_area.height)
            cr.fill()

    def do_query_data(self, start, end, state):
        line = start.get_line() + 1
        if line in self.file_context:
            line_context = self.file_context[line]
            self.diff_type = line_context.line_type
        else:
            self.diff_type = DiffType.NONE

    def do_query_tooltip(self, it, area, x, y, tooltip):
        line = it.get_line() + 1
        if line in self.file_context:
            line_context = self.file_context[line]
            if line_context.line_type == DiffType.REMOVED or line_context.line_type == DiffType.MODIFIED:
                removed = ''.join(map(str, line_context.removed_lines))
                added = ''.join(map(str, line_context.added_lines))
                tooltip.set_text(removed + added)
                return True
        return False

    def set_data(self, file_context):
        self.file_context = file_context
        self.queue_draw()

# ex:ts=4:et:
