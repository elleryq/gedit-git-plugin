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
    (NONE,
     ADDED,
     MODIFIED,
     REMOVED) = range(4)


class DiffRenderer(GtkSource.GutterRenderer):

    backgrounds = {}
    backgrounds[DiffType.ADDED] = Gdk.RGBA()
    backgrounds[DiffType.MODIFIED] = Gdk.RGBA()
    backgrounds[DiffType.REMOVED] = Gdk.RGBA()
    backgrounds[DiffType.ADDED].parse("#8ae234")
    backgrounds[DiffType.MODIFIED].parse("#fcaf3e")
    backgrounds[DiffType.REMOVED].parse("#ef2929")

    def __init__(self):
        GtkSource.GutterRenderer.__init__(self)

        self.set_size(8)
        self.set_padding(3, 0)

        self.file_context = {}
        self.tooltip = None
        self.tooltip_line = 0

    def do_draw(self, cr, bg_area, cell_area, start, end, state):
        GtkSource.GutterRenderer.do_draw(self, cr, bg_area, cell_area,
                                         start, end, state)

        line_context = self.file_context.get(start.get_line() + 1, None)
        if line_context is None or line_context.line_type == DiffType.NONE:
            return

        background = self.backgrounds[line_context.line_type]

        Gdk.cairo_set_source_rgba(cr, background)
        cr.rectangle(cell_area.x, cell_area.y,
                     cell_area.width, cell_area.height)
        cr.fill()

    def do_query_tooltip(self, it, area, x, y, tooltip):
        line = it.get_line() + 1

        line_context = self.file_context.get(line, None)
        if line_context is None:
            return False

        # Check that the context is the same not the line this
        # way contexts that span multiple times are handled correctly
        if self.file_context.get(self.tooltip_line, None) is line_context:
            tooltip.set_custom(None)
            tooltip.set_custom(self.tooltip)
            return True

        if line_context.line_type not in (DiffType.REMOVED, DiffType.MODIFIED):
            return False

        tooltip_buffer = GtkSource.Buffer()
        tooltip_view = GtkSource.View.new_with_buffer(tooltip_buffer)

        # Propagate the view's settings
        content_view = self.get_view()
        tooltip_view.set_indent_width(content_view.get_indent_width())
        tooltip_view.set_tab_width(content_view.get_tab_width())

        # Propagate the buffer's settings
        content_buffer = content_view.get_buffer()
        tooltip_buffer.set_highlight_syntax(content_buffer.get_highlight_syntax())
        tooltip_buffer.set_language(content_buffer.get_language())
        tooltip_buffer.set_style_scheme(content_buffer.get_style_scheme())

        # Fix some styling issues
        tooltip_buffer.set_highlight_matching_brackets(False)
        tooltip_view.set_border_width(4)
        tooltip_view.set_cursor_visible(False)

        # Set the font
        content_style_context = content_view.get_style_context()
        content_font = content_style_context.get_font(Gtk.StateFlags.NORMAL)
        tooltip_view.override_font(content_font)

        # Only add what can be shown, we
        # don't want to add hundreds of lines
        allocation = content_view.get_allocation()
        lines = allocation.height // area.height
        removed = '\n'.join(map(str, line_context.removed_lines[:lines]))
        tooltip_buffer.set_text(removed)

        # Avoid having to create the tooltip multiple times
        self.tooltip = tooltip_view
        self.tooltip_line = line

        tooltip.set_custom(tooltip_view)
        return True

    def set_file_context(self, file_context):
        self.file_context = file_context
        self.tooltip = None
        self.tooltip_line = 0

        self.queue_draw()

# ex:ts=4:et:
