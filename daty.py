#!/usr/bin/env python3

#    Daty
#
#    ----------------------------------------------------------------------
#    Copyright © 2018  Pellegrino Prevete
#
#    All rights reserved
#    ----------------------------------------------------------------------
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#


from gi import require_version
require_version('Gtk', '3.0')
require_version('Gdk', '3.0')
from wikidata import Wikidata
from gi.repository.Gdk import Color, Event, EventMask, Screen
from gi.repository.Gio import ThemedIcon
from gi.repository.Gtk import main, main_quit, Align, Box, Button, CheckButton, CssProvider, Entry, EventBox, HBox, IconSize, Image, HeaderBar, Label, ListBox, ListBoxRow, ModelButton, Orientation, Overlay, PolicyType, PopoverMenu, Revealer, RevealerTransitionType, ScrolledWindow, SearchBar, SearchEntry, SelectionMode, Stack, StackSwitcher, StackTransitionType, StyleContext, TextView, VBox, Window, WindowPosition, WrapMode, STYLE_CLASS_DESTRUCTIVE_ACTION, STYLE_CLASS_SUGGESTED_ACTION, STYLE_PROVIDER_PRIORITY_APPLICATION
from gi.repository.GLib import unix_signal_add, PRIORITY_DEFAULT
from pprint import pprint
from signal import SIGINT
from widgets import ExtendedModelButton, NameDescriptionLabel, ResultsBox, WelcomePage

def gtk_style():
    with open('style.css', 'rb') as f:
        css = f.read()
        f.close()
    style_provider = CssProvider()
    style_provider.load_from_data(css)
    StyleContext.add_provider_for_screen(Screen.get_default(),
                                         style_provider,
                                         STYLE_PROVIDER_PRIORITY_APPLICATION)

class WelcomeWindow(Window):

    def __init__(self, wikidata):
        # Window properties
        Window.__init__(self, title="Daty")
        self.set_border_width(0)
        self.set_default_size(500, 400)
        self.set_position(WindowPosition(1))
        self.set_title ("Daty")
        #self.set_icon_from_file('icon.png')
        self.connect('destroy', main_quit)
        unix_signal_add(PRIORITY_DEFAULT, SIGINT, main_quit)

        # Title
        label = Label(label="<b>Daty</b>")
        label.set_use_markup(True)

        # Title revealer 
        title_revealer = Revealer()
        title_revealer.set_transition_type (RevealerTransitionType.CROSSFADE)
        title_revealer.set_transition_duration(500)
        title_revealer.add(label)
        title_revealer.set_reveal_child(True)

        # Headerbar        
        hb = HeaderBar()
        hb.set_show_close_button(True)
        hb.set_custom_title(title_revealer)
        self.set_titlebar(hb)

        # Headerbar: New items
        open_session = Button.new()
        open_session.set_label ("Apri sessione")
        open_session.connect ("clicked", self.on_constraint_search)
        hb.pack_start(open_session)

        # On demand stack
        stack = Stack()
        stack.set_transition_type (StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration (500)

        # Stack revealer 
        stack_revealer = Revealer()
        stack_revealer.set_transition_type (RevealerTransitionType.CROSSFADE)
        stack_revealer.set_transition_duration(500)
        stack_revealer.set_reveal_child(False)
        stack_revealer.add(stack)

        # Label search
        label_search_page = LabelSearchPage(wikidata, set_visible_search_entry=True)
        stack.add_titled(label_search_page, "Seleziona per etichetta", "Seleziona per etichetta")

        # Back button
        back = Button.new_from_icon_name("go-previous-symbolic", size=IconSize.BUTTON)

        # Add Button
        add = Button.new_with_label ("Apri")
        add.get_style_context().add_class(STYLE_CLASS_SUGGESTED_ACTION)
        add.set_sensitive(False)

        # Sparql Page
        sparql_page = SparqlPage(wikidata, add_button=add, parent=self)
        stack.add_titled(sparql_page, "Seleziona per vincolo", "Seleziona per vincolo")

        # Switcher
        switcher = StackSwitcher()
        switcher.set_stack(stack)

        # Switcher revealer 
        switcher_revealer = Revealer()
        switcher_revealer.set_transition_type (RevealerTransitionType.CROSSFADE)
        switcher_revealer.set_transition_duration(500)
        switcher_revealer.set_reveal_child(False)
        switcher_revealer.add(switcher)

        # Welcome revealer 
        welcome_revealer = Revealer()
        welcome_revealer.set_transition_type (RevealerTransitionType.CROSSFADE)
        welcome_revealer.set_transition_duration(500)
        welcome_revealer.set_reveal_child(True)
        self.add(welcome_revealer)

        # Things that will have to hide/be revealed
        hide_and_seek = [hb, open_session, back, add,
                         title_revealer, switcher_revealer,
                         stack_revealer, stack, welcome_revealer]

        # Welcome page
        self.search_visible = False
        daty_description = """Daty ti permette di consultare e modificare Wikidata in maniera facile e intuitiva. <br>
<b>Digita sulla tastiera quello che vorresti consultare</b> oppure clicca sul pulsante in basso per utilizzare il form di selezione avanzata!"""
        welcome_page = WelcomePage(icon_name="system-search-symbolic",
                                   description=daty_description,
                                   button_text="Aggiungi un vincolo",
                                   button_callback=self.on_constraint_search,
                                   button_callback_arguments=hide_and_seek,
                                   parent=self)
        welcome_revealer.add(welcome_page)

        # Write to search
        self.connect("key_press_event", self.on_key_press, hide_and_seek)
        back.connect("clicked", self.on_back_button, hide_and_seek)

    def on_key_press(self, widget, event, hide_and_seek):
        if self.search_visible:
            if event.keyval == 65307:
                self.deactivate_search(*hide_and_seek)
        if not self.search_visible:
            if not event.keyval == 65307:
                self.activate_search(*hide_and_seek)

    def on_back_button(self, button, hide_and_seek):
        self.deactivate_search(hb, *hide_and_seek)

    def activate_search(self, hb, open_session, back, add,
                              title_revealer, switcher_revealer,
                              stack_revealer, stack, welcome_revealer):
        # Hide welcome and title
        welcome_revealer.set_reveal_child(False)
        self.remove(welcome_revealer)
        title_revealer.set_reveal_child(False)
        hb.remove(open_session)
        hb.set_show_close_button(False)

        # Show switcher, stack and back
        hb.pack_start(back)
        hb.pack_end(add)
        hb.set_custom_title(switcher_revealer)
        switcher_revealer.set_reveal_child(True)
        hb.show_all()
        self.add(stack_revealer)
        stack_revealer.set_reveal_child(True)

        # Set search visible
        stack.set_visible_child_full("Seleziona per etichetta", StackTransitionType.NONE)
        self.search_visible = True 
        self.show_all()
        search_entry = stack.get_child_by_name("Seleziona per etichetta").search_entry
        search_entry.grab_focus_without_selecting()

    def deactivate_search(self, hb, open_session, back, add, 
                                title_revealer, switcher_revealer,
                                stack_revealer, stack, welcome_revealer):
        # Hide stack, switcher and back
        stack_revealer.set_reveal_child(False)
        self.remove(stack_revealer)
        switcher_revealer.set_reveal_child(False)
        hb.remove(back)
        hb.remove(add)
        hb.set_show_close_button(True)

        # Show title and welcome
        hb.set_custom_title(title_revealer)
        hb.pack_start(open_session)
        title_revealer.set_reveal_child(True)
        hb.show_all()
        self.add(welcome_revealer)
        welcome_revealer.set_reveal_child(True)

        # Set search not visible
        self.search_visible = False
        search_entry = stack.get_child_by_name("Seleziona per etichetta").search_entry
        search_entry.set_text("")
        self.show_all()

    def on_constraint_search(self, button, *hide_and_seek):
        self.activate_search(*hide_and_seek)
        stack = hide_and_seek[-2]
        stack.set_visible_child_full("Seleziona per vincolo", StackTransitionType.NONE)

class LabelSearchPage(VBox):

    def __init__(self, wikidata, set_visible_search_entry=True, results_border=0):
        VBox.__init__(self)

        # Search Box
        search_box = HBox()
        self.pack_start(search_box, False, False, 0)

        # Results Box
        results = ResultsBox()
        self.pack_start(results, True, True, results_border)

        # Search Entry
        self.search_entry = SearchEntry()
        self.search_entry.connect("search_changed", self.on_search_changed, results, wikidata)
        self.search_entry.show()

        # Search bar
        self.search_bar = SearchBar()
        self.search_bar.set_search_mode(True)
        self.search_bar.connect_entry(self.search_entry)
        self.search_bar.add(self.search_entry)
        search_box.pack_start(self.search_bar, expand=True, fill=True, padding=0)

    def on_search_changed(self, search_entry, results, wikidata):
        # Get query
        query = search_entry.get_text()

        # Clean results
        results.scrolled.remove(results.listbox)
        results.listbox = ListBox()

        # Obtain data
        if query != "":
            data = wikidata.search(query)
        else:
            data = []

        # Populate results
        for d in data:
            row = Result(results.listbox, d)
            results.listbox.add(row)
        results.scrolled.add(results.listbox)
        results.listbox.show_all()

class SparqlPage(VBox):
    def __init__(self, wikidata, add_button=None, parent=None, selection_vpadding=3):
        VBox.__init__(self)
        self.wikidata = wikidata
        self.parent = parent
        self.add_button = add_button
        self.query = {'vars':[], 'what':{}, 'triples':[]}
        self.triples = []
        self.what = {}

        # Selection Box
        selection_box = VBox()
        self.pack_start(selection_box, False, False, 0)

        # label + Button vertical Box
        label_button_vbox = VBox()

        # Label + Button horizontal Box
        label_button_hbox = HBox()
        label_button_vbox.pack_start(label_button_hbox, True, True, selection_vpadding)

        # Select label
        label = Label()
        label.set_label("Seleziona")
        label_button_hbox.pack_start(label, True, True, 2)

        # Selected variable
        self.variable = ButtonWithPopover(text="variabile", css="target", vpadding=2, data=self.query['what'])
        self.variable.set_popover_box(ItemSearchBox(self.variable, wikidata, type="var", item_changed_callback=self.check_query))
        label_button_hbox.pack_start(self.variable, True, True, 2)

        # Search bar
        self.selection_bar = SearchBar()
        self.selection_bar.set_search_mode(True)
        self.selection_bar.add(label_button_vbox)
        selection_box.pack_start(self.selection_bar, expand=True, fill=True, padding=0)

        # Constraints
        self.constraints = EditableListBox(new_row_callback=self.new_constraint, new_row_callback_arguments=[wikidata],
                                           delete_row_callback=self.delete_constraint, delete_row_callback_arguments=[],
                                           horizontal_padding=0)
        self.pack_start(self.constraints, True, True, 0)
        self.constraints.eventbox.emit("button_press_event", Event())

    def new_constraint(self, row, wikidata):
        # Add a triple box
        triple_box = TripleBox(wikidata, self.check_query)
        self.query['triples'].append(triple_box)
        row.add_widget(triple_box)
        self.check_query()

    def delete_constraint(self, row, widget, event):
        self.query['triples'].remove(row.child) 
        self.check_query()

    def check_query(self):
        update = [t.get_data() for t in self.query["triples"]]
        self.triples = [t.triple for t in self.query["triples"]]
        self.what = self.variable.data
        ready = all(not any(t[k] == {} for k in t.keys()) for t in self.triples) and self.what != {}
        if ready:
            self.add_button.set_sensitive(True)
            self.add_button.connect("clicked", self.on_add)
        else:
            self.add_button.set_sensitive(False)

    def on_add(self, button):
        results = self.wikidata.select(self.what, self.triples)
        self.parent.destroy()
        editor = Editor(self.wikidata, items=results) 
        editor.show_all() 
        del self.parent

class ItemResults(HBox):
    def __init__(self, wikidata, row_activated_callback=None, row_activated_callback_arguments=[]):
        HBox.__init__(self)

        # Scrolled Window
        self.scrolled = ScrolledWindow()
        self.scrolled.set_policy(PolicyType.NEVER, PolicyType.AUTOMATIC)
        self.pack_start(self.scrolled, True, True, padding=0)

        # ListBox             			# per dopo l'itwikicon. rendere eliminabili le variabili dichiarate
        self.listbox = ListBox()
        StyleContext.add_class(self.listbox.get_style_context(), "itemResultsListBox")
        self.scrolled.add(self.listbox)
        self.listbox.connect("row_activated", self.on_row_activated, row_activated_callback, row_activated_callback_arguments)
        self.listbox.show_all()

        # Populate listbox with sparql vars
        for var in wikidata.vars:
            row = Result(self.listbox, var)
            self.listbox.add(row)

    def on_row_activated(self, listbox, row, row_activated_callback, row_activated_callback_arguments):
        row_activated_callback(self, listbox, row, *row_activated_callback_arguments)

class ItemSearchBox(VBox):
    def __init__(self, parent, wikidata,
                       item_changed_callback=None, item_changed_callback_arguments=[],
                       type="var+search", vpadding=2, hpadding=4):
        VBox.__init__(self)
        self.type = type
        if type == "var":
            icon_name = "bookmark-new-symbolic"
            description = "Definisci una nuova variabile"
        if type == "var+search":
            icon_name = "system-search-symbolic"
            description = "Cerca un item o una variabile, oppure <b>definiscine una nuova</b>"

        # Horizontal box
        hbox = HBox()
        self.pack_start(hbox, True, True, 0)

        # Vertical box
        vbox = VBox()
        hbox.pack_start(vbox, True, True, hpadding)

        # Search entry
        self.search_entry = SearchEntry()
        vbox.pack_start(self.search_entry, False, False, vpadding)

        # Placeholder
        welcome_page = WelcomePage(icon_name=icon_name,
                                   icon_size=96,
                                   vpadding=15,
                                   description=description,
                                   description_max_length=25,
                                   parent=None)

        # Placeholder revealer
        welcome_revealer = Revealer()
        welcome_revealer.set_transition_type(RevealerTransitionType.NONE)
        welcome_revealer.set_reveal_child(True)
        welcome_revealer.add(welcome_page)
        vbox.pack_start(welcome_revealer, False, True, vpadding)

        # Results revealer
        results_revealer = Revealer()
        results_revealer.set_transition_type(RevealerTransitionType.NONE)
        results_revealer.set_reveal_child(False)
        results_revealer_box = VBox()
        results_revealer.add(results_revealer_box)
        vbox.pack_start(results_revealer, True, True, 0)

        # New variable button 
        new_variable_label = NameDescriptionLabel("<b>Seleziona un item o una variabile</b>", "oppure definiscine una nuova")
        new_variable = ExtendedModelButton(new_variable_label)
        new_variable.set_sensitive(False)
        results_revealer_box.pack_start(new_variable, False, False, vpadding)

        # Search results 
        results = ItemResults(wikidata,
                              row_activated_callback=self.on_result_clicked,
                              row_activated_callback_arguments=[parent, wikidata, 
                                                                item_changed_callback, item_changed_callback_arguments])
        results.set_visible(False)
        self.search_entry.connect("search_changed", self.on_search_changed, results_revealer,
                                                    welcome_revealer,
                                                    new_variable, results,
                                                    parent, wikidata,
                                                    item_changed_callback, item_changed_callback_arguments)
        results_revealer_box.pack_start(results, True, True, vpadding)

    def on_new_variable(self, widget, event, welcome_revealer, parent, query, wikidata, item_changed_callback, item_changed_callback_arguments):
        # Extract data
        var = self.search_entry.get_text()
        data = {"Label":var, "Description":"Sparql variable"}

        # Eventually add data
        labels = set([v["Label"] for v in wikidata.vars])
        if not var in labels and var != "":
            wikidata.vars.append(data)

        # Set data
        parent.set_data(data)
        parent.popover.trigger()

        item_changed_callback(*item_changed_callback_arguments)

        # Adjust button, search entry and addable status after selection
        parent.set_css("variable")
        self.search_entry.set_text("")
        welcome_revealer.set_reveal_child(False)

    def on_result_clicked(self, item_results, listbox, row, parent, wikidata,
                                item_changed_callback, item_changed_callback_arguments):
        parent.set_data(row.content)
        parent.popover.hide() 
        self.process_type(row.content, parent)
        item_changed_callback(*item_changed_callback_arguments)

    def process_type(self, dictionary, parent):
        if "URI" in dictionary.keys():
            if dictionary["URI"].startswith("Q"):
                parent.set_css("item")
            if dictionary["URI"].startswith("P"):
                parent.set_css("property")
            if dictionary["URI"] == "":
                parent.set_css("variable")
        else:
            parent.set_css("variable")

    def on_search_changed(self, widget, results_revealer, welcome_revealer,
                                new_variable, results, parent, wikidata,
                                item_changed_callback, item_changed_callback_arguments):

        # Obtain query from search widget
        query = widget.get_text()

        if query != "":
            # Hide welcome and show search revealer
            welcome_revealer.set_reveal_child(False)
            results_revealer.set_reveal_child(True)

            # Check variable existence
            labels = set([v["Label"] for v in wikidata.vars])
            if query in labels:
                description = "Seleziona variabile"
            else:
                description = "Registra variabile"

            # Set new variable label
            new_variable.child = NameDescriptionLabel("<b>" + query + "</b>", description)
            new_variable.set_sensitive(True)
            new_variable.update_child()
            new_variable.connect("button_press_event", self.on_new_variable, welcome_revealer, parent, query, wikidata,
                                                       item_changed_callback, item_changed_callback_arguments)

        if query == "":
            if wikidata.vars == []:
                # Hide revealer and show placeholder
                results_revealer.set_reveal_child(False)
                welcome_revealer.set_reveal_child(True)

            if wikidata.vars != []:
                # Show new variable not selectable and hide welcome revealer
                new_variable.child = NameDescriptionLabel("<b>Seleziona un item o una variabile</b>", "oppure definiscine una nuova")
                new_variable.set_sensitive(False)
                new_variable.update_child()
                new_variable.set_visible(True)
                welcome_revealer.set_reveal_child(False)

        if query != "" or wikidata.vars != []:
            # Destroy and re-create listbox
            results.scrolled.remove(results.listbox)
            results.listbox = ListBox()
            StyleContext.add_class(results.listbox.get_style_context(), "itemResultsListBox")
            results.listbox.connect("row_activated", results.on_row_activated, self.on_result_clicked, [parent, wikidata,
                                                                                                        item_changed_callback, item_changed_callback_arguments])
            results.scrolled.add(results.listbox)
         
            # Get data
            data = [v for v in wikidata.vars if query in v["Label"] and query != v["Label"]]
            if self.type != "var":
                data = data + wikidata.search(query)
         
            # Populate listbox
            for d in data:
                row = Result(results.listbox, d)
                results.listbox.add(row)
            results.listbox.show_all()
            results.set_visible(True)

class BetterPopover(PopoverMenu):
    def __init__(self, parent, child, width=300, height=275, vpadding=2):
        PopoverMenu.__init__(self)
        self.width = width
        self.height = height
        self.set_relative_to(parent)
        vbox = VBox()
        vbox.pack_start(child, True, True, vpadding)
        self.add(vbox)

    def trigger(self):
        if self.get_visible():
            self.hide()
        else:
            self.set_size_request(self.width, self.height)
            self.show_all()

class ButtonWithPopover(EventBox):
    def __init__(self, popover_box=None, text="var", css="unselected", vpadding=2, data=None):
        EventBox.__init__(self)
        self.data = data
        if popover_box == None:
            popover_box = HBox()
 
        # Popover
        self.popover = BetterPopover(self, popover_box, vpadding=vpadding)
        self.connect ("button_press_event", self.clicked)

        # Label and style
        self.label = Label()
        self.label.set_label(text)
        self.label.set_use_markup(True)
        self.label.set_line_wrap(True)
        self.label.set_max_width_chars(50)
        self.set_css(css)
        self.add(self.label)

    def set_css(self, css):
        self.label.set_tooltip_text("Seleziona la variabile o il valore da assumere come soggetto")
        StyleContext.add_class(self.label.get_style_context(), css)
        self.label.set_css_name(css)
        gtk_style()
        self.label.show_all()

    def set_popover_box(self, popover_box):
        self.popover = BetterPopover(self, popover_box)

    def clicked(self, widget, event):
        self.popover.trigger()

    def set_data(self, data):
        self.data = data
        self.label.set_label(data["Label"])

class EditableListBox(HBox):
    def __init__(self, new_row=True, new_row_callback=None, new_row_callback_arguments=[],
                       delete_row_callback=None, delete_row_callback_arguments=[],
                       row_activated_callback=None, row_activated_callback_arguments=[],
                       horizontal_padding=0, selectable=0, css="sidebar",
                       new_row_height=14):
        HBox.__init__(self)
        self.get_style_context().add_class("sidebar")
        self.new_row = new_row

        # Scrolled window
        self.scrolled = ScrolledWindow()
        self.scrolled.set_policy(PolicyType.AUTOMATIC, PolicyType.AUTOMATIC)
        self.pack_start(self.scrolled, True, True, padding=horizontal_padding)

        # Listbox
        self.listbox = ListBox()
        self.listbox.set_selection_mode(SelectionMode(selectable))
        self.listbox.connect("row_activated", self.on_row_activated, row_activated_callback, row_activated_callback_arguments)
        self.listbox.connect("motion-notify-event", self.motion)
        self.scrolled.add(self.listbox)

        if new_row:
            self.new_row = ListBoxRow()
            self.listbox.add(self.new_row)

            # New row icon
            icon = Image.new_from_icon_name('list-add-symbolic', IconSize.MENU)

            # New row VBox
            vbox = VBox()
            vbox.pack_start(icon, True, True, new_row_height)

            # New row Eventbox
            self.eventbox = EventBox()
            self.eventbox.add(vbox)
            self.eventbox.connect("button_press_event", self.on_new_row, self.new_row,
                                                   new_row_callback, new_row_callback_arguments,
                                                   delete_row_callback, delete_row_callback_arguments)
            self.new_row.add(self.eventbox)

    def motion(self, listbox, event):
        row = listbox.get_row_at_y(event.y)
        try:
            self.lastrow
        except:
            self.lastrow = row
        if row != self.lastrow:
            try:
                row.revealer.set_reveal_child(True)
            except:
                pass
            try:
                self.lastrow.revealer.set_reveal_child(False)
            except:
                pass
            self.lastrow = row

    def on_row_activated(self, listbox, row, row_activated_callback, row_activated_callback_arguments):
        row_activated_callback(self, listbox, row, *row_activated_callback_arguments)

    def on_new_row(self, widget, event, new_row,
                                        new_row_callback, new_row_callback_arguments,
                                        delete_row_callback, delete_row_callback_arguments):

        if self.new_row:
            # Remove "New row" from ListBox
            self.listbox.remove(new_row)

        # Create new row and give it to callback
        row = EditableListBoxRow(self.listbox, delete=True, delete_callback=delete_row_callback, delete_callback_arguments=delete_row_callback_arguments)
        new_row_callback(row, *new_row_callback_arguments)

        # Add the new row to the listbox with the "New row" button
        self.listbox.add(row)
        if self.new_row:
            self.listbox.add(new_row)
        self.listbox.show_all()

class EditableListBoxRow(ListBoxRow):
    def __init__(self, listbox, delete=False, delete_callback=None, delete_callback_arguments=[],
                                activatable=False, vertical_padding=10):
        ListBoxRow.__init__(self)
        self.set_activatable(activatable)
        #self.add_events(EventMask.ENTER_NOTIFY_MASK)

        # Overlay
        self.overlay = Overlay()
        self.add(self.overlay)

        if delete: 
            # Remove Icon
            self.remove_icon = Image.new_from_icon_name('window-close-symbolic', IconSize.BUTTON)

            # Remove Row EventBox
            remove_row_eventbox = EventBox()
            remove_row_eventbox.add(self.remove_icon)
            remove_row_eventbox.connect("button_press_event", self.on_delete_row, listbox, delete_callback, delete_callback_arguments)
       
            # Remove Row Revealer
            self.revealer = Revealer()
            self.revealer.set_transition_type (RevealerTransitionType.NONE)
            self.revealer.add(remove_row_eventbox)
            self.revealer.set_reveal_child(False)
            self.revealer.set_property("halign", Align.END)
            self.overlay.add_overlay(self.revealer)

    def add_widget(self, widget): #, same_size_widget):
        self.child = widget
        self.overlay.add(widget)
 
    def on_delete_row(self, widget, event, listbox, callback, callback_arguments):
        listbox.remove(self)
        if callback_arguments != []:
            callback(self, widget, event, *callback_arguments)
        else:
            callback(self, widget, event)

class Result(EditableListBoxRow):
    def __init__(self, listbox, result):
        EditableListBoxRow.__init__(self, listbox, activatable=True)
        self.content = result

        # Horizontal Box
        self.hbox = HBox()
        self.add_widget(self.hbox)

        # Contents Box
        self.update()
        self.hbox.pack_start(self.name_description, True, True, self.padding)

    def update(self):
        text = "<b>" + self.content["Label"] + "</b>"
        if "URI" in self.content.keys():
            text = text + " <span font_desc=\"8.0\">(" + self.content["URI"] + ")</span>"
            checkbox = CheckButton()
            self.hbox.pack_start(checkbox, False, False, 10)
            self.padding = 0
        else:
            self.padding = 20
        self.name_description = NameDescriptionLabel(text, self.content["Description"])
        self.show_all() 


class TripleBox(VBox):
    def __init__(self, wikidata, item_changed_callback=None, css="unselected", first="Soggetto", second="Proprietà", third="Oggetto", vertical_padding=8):
        VBox.__init__(self)

        # Data handling
        self.triple = {'s':{},'p':{},'o':{}}

        # Tuple Box
        hbox = HBox()
        self.pack_start(hbox, True, True, vertical_padding)

        # S/P/O
        self.subject = ButtonWithPopover(text=first, css=css, data=self.triple['s'])
        self.subject.set_popover_box(ItemSearchBox(self.subject, wikidata, item_changed_callback=item_changed_callback))
        self.prop = ButtonWithPopover(text=second, css=css, data=self.triple['p'])
        self.prop.set_popover_box(ItemSearchBox(self.prop, wikidata, item_changed_callback=item_changed_callback))
        self.obj = ButtonWithPopover(text=third, css=css, data=self.triple['o'])
        self.obj.set_popover_box(ItemSearchBox(self.obj, wikidata, item_changed_callback=item_changed_callback))

        # Tuple
        first = VBox()
        second = VBox()
        third = VBox()
        first.pack_start(self.subject, False, False, 0)
        second.pack_start(self.prop, False, False, 0)
        third.pack_start(self.obj, False, False, 0)

        # Tuple Box
        tuple_box = HBox(homogeneous=True)
        tuple_box.pack_start(first, True, False, 0)
        tuple_box.pack_start(second, True, False, 0)
        tuple_box.pack_start(third, True, False, 0)
        hbox.pack_start(tuple_box, True, True, vertical_padding)

    def get_data(self):
        self.triple = {'s':self.subject.data, 'p':self.prop.data, 'o':self.obj.data}

class Editor(Window):

    def __init__(self, wikidata, items=['Q156280', 'Q167981']):

        items = [wikidata.fetch(item) for item in items]

        # Window properties
        Window.__init__(self, title="Daty")
        self.set_border_width(0)
        self.set_default_size(800, 600)
        self.set_position(WindowPosition(1))
        self.set_title ("Daty")
        #self.set_icon_from_file('icon.png')
        self.connect('destroy', main_quit)
        unix_signal_add(PRIORITY_DEFAULT, SIGINT, main_quit)

        # Title
        label = Label(label="<b>Daty</b>")
        label.set_use_markup(True)

        # Headerbar        
        hb = HeaderBar()
        hb.set_show_close_button(True)
        hb.set_custom_title(label)
        self.set_titlebar(hb)

        # Headerbar: New items
        open = Button.new()
        open.set_label ("Apri")
        hb.pack_start(open)

        # Stack
        stack = Stack()

        # Data processing
        for item in items:
            result = self.name_description(item)
            editor_view = EditorPage(result)
            stack.add_titled(editor_view, result["Label"], result["Label"])

        # Sidebar
        sidebar = EditableListBox(new_row=False, new_row_callback=self.add_item, new_row_callback_arguments=[],
                                  delete_row_callback=None, delete_row_callback_arguments=[],
                                  horizontal_padding=0, new_row_height=14, selectable=1, css="sidebar")
        sidebar.set_size_request(200,100)

        for item in items:
            result = self.name_description(item)
            sidebar.on_new_row(sidebar.new_row, Event(), sidebar.new_row,
                                        new_row_callback=self.open_item, new_row_callback_arguments=[result, sidebar],
                                        delete_row_callback=None, delete_row_callback_arguments=[])

        # Hbox
        hbox = HBox()
        hbox.pack_start(sidebar, False, False, 0)
        #hbox.pack_start(stack, True, True, 0)
        self.add(hbox)

    def open_item(self, row, result, sidebar):
        #sidebar.listbox.
        row = Result(sidebar.listbox, result)
        sidebar.listbox.add(row)

    def add_item(self, row, *args):
        #triple_box = TripleBox(wikidata)
        #row.add_widget(triple_box)
        pass

    def on_sidebar_row_activated(self, sidebar, listbox, row, stack):
        stack.get_child_by_name(row.content).search_entry     

    def delete_constraint(self, row, widget, event):
        pass

    def name_description(self, item):
        result = {}
        if 'it' in item['labels']:
           result['Label'] = item['labels']['it']
        else:
           result['Label'] = item['labels']['en']
        if 'it' in item['descriptions']:
           result['Description'] = item['descriptions']['it']
        else:
           result['Description'] = item['descriptions']['en']
        return result

class EditorPage(HBox):
    def __init__(self, item):
        HBox.__init__(self)

class WikidataEditor():
    def __init__(self):
        wikidata = Wikidata(verbose=False)
        gtk_style()
        win = WelcomeWindow(wikidata)
        #win = Editor(wikidata)
        win.show_all()
        main()

if __name__ == "__main__":
    editor = WikidataEditor()