# -*- coding: utf-8 -*-

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository.Gtk import Box, ListBox, ListBoxRow, Separator, Template

from .entity import Entity
from .page import Page
from .sidebarentity import SidebarEntity

@Template.from_resource("/org/prevete/Daty/gtk/sidebarlist.ui")
class SidebarList(ListBox):
    __gtype_name__ = "SidebarList"

    def __init__(self, 
                 stack, 
                 entity_label,
                 entity_description, 
                 autoselect=True, *args, **kwargs):
        """Sidebar ListBox
        
        Args:
            stack (Gtk.Stack): entities stack;
            entity_label (Gtk.Label): title of the visible entity;
            description_label (Gtk.Label): description of the visible entity;
            autoselect (bool): whether to select the first element
                by default.
           
        """
        ListBox.__init__(self, *args, **kwargs)

        self.autoselect = autoselect

        # Set separator as row header
        self.set_header_func(self.update_header)

        self.connect("row-selected", self.sidebar_row_selected_cb,
                                     stack,
                                     entity_label,
                                     entity_description)

    def update_header(self, row, before, *args):
        """See GTK+ Documentation"""
        if before:
            row.set_header(Separator())

    def set_selection_mode(self, value):
        """Set selection mode on or off

            Args:
                value (bool): whether to activate selection mode
        """
        self.selected = []
        self.foreach(self.set_checkbutton, value)

    def set_checkbutton(self, row, value):
        """Add checkbutton to row

            Args:
                row (Gtk.ListBoxRow): selected row;
                value (bool): whether to add or remove checkbutton.
        """
        if row.get_children():
            child = row.box.child
            entity = child.entity
            if value:
                row.box.remove(child)
                row.check = Entity(entity, widget=False, selected=self.selected)
                row.box.add(row.check)
                row.box.add(child)
            else:
                row.box.remove(row.check)
                row.check.destroy()
                del row.check
                #row.add(SidebarEntity(entity))
 
    def add(self, widget):
        """Add widget to a new row

            Overrides Gtk.Container.add

            Args:
                widget (Gtk.Widget): the widget to add to the new row.
        """
        # If the list has rows
        if self.get_children():

            # Pick the last one
            last_row = self.get_children()[-1]

            # If it has no children, it is the ending separator, so remove it
            if not last_row.get_children():
                self.remove(last_row)

        # Create new row and add to self
        row = ListBoxRow()
        row.box = Box()
        row.add(row.box)
        row.box.child = widget
        row.box.add(row.box.child)
        
        super(SidebarList, self).add(row)

        # Select if 'autoselect'
        if len(self.get_children()) == 1 and self.autoselect:
            self.select_row(row)

        # The final empty row that acts as separator
        row = ListBoxRow()
        row.props.activatable = False
        row.props.selectable = False
        super(SidebarList, self).add(row)
      
    def sidebar_row_selected_cb(self,
                                listbox, 
                                row, 
                                stack, 
                                entity_label,
                                entity_description):
        """Sidebar row selected callback

            If not existing, creates entity page and then
            switch to it in content_stack.

            Args:
                listbox (Gtk.ListBox): the listbox class, so self;
                row (Gtk.ListBoxRow): the selected row, which has 
                for only child a SidebarEntity object;
                stack (Gtk.Stack): the stack which has to switch
                visible child.
                entity_label (Gtk.Label): widget of entity title
                entity_description(Gtk.Label)
        """
        # Get entity from SidebarEntity child
        sidebar_entity = row.box.child
        entity = sidebar_entity.entity

        # Set titlebar
        entity_label.set_text(entity["Label"])
        entity_description.set_text(entity["Description"])

        # If there is no corresponding child in stack, create one
        if not stack.get_child_by_name(entity['URI']):
            stack.add_titled(Page(entity['Data']), entity['URI'], entity['Label'])

        # Set corresponding child in stack
        stack.set_visible_child_name(entity['URI'])
        stack.show_all() 
