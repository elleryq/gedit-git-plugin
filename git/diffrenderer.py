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

from gi.repository import Gtk, GtkSource

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

    def do_draw(self, cr, bg_area, cell_area, start, end, state):
        GtkSource.GutterRenderer.do_draw(self, cr, bg_area, cell_area, start, end, state)

        if self.diff_type is not DiffType.NONE:
            if self.diff_type == DiffType.ADDED:
                cr.set_source_rgba(0.8, 0.9, 0.3, 1.0)
            elif self.diff_type == DiffType.MODIFIED:
                cr.set_source_rgba(0.8, 0.6, 0.2, 1.0)
            elif self.diff_type == DiffType.REMOVED:
                cr.set_source_rgba(1.0, 0.0, 0.0, 1.0)

            cr.rectangle(cell_area.x, cell_area.y, cell_area.width, cell_area.height)
            cr.fill()
            cr.paint()

    def do_query_data(self, start, end, state):
        line = start.get_line() + 1
        if line in self.file_context:
            line_context = self.file_context[line]
            self.diff_type = line_context.line_type
        else:
            self.diff_type = DiffType.NONE

    def set_data(self, file_context):
        self.file_context = file_context
        self.queue_draw()

# ex:ts=4:et:
