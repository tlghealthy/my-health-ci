import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import json
import os
import copy
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

print("Imported necessary modules.")

class DailyTrackingApp:
    def __init__(self, root):
        print("Initializing the Daily Tracking App.")
        self.root = root
        self.root.title("Daily Tracking App")
        print("Set the window title.")

        self.data_file = "tracking_data.json"
        self.load_data()
        print("Loaded data from file.")

        self.current_date = datetime.now().strftime("%Y-%m-%d")
        print("Set current date to today:", self.current_date)

        # Check if current date data exists, if not, copy previous day's items without data
        if self.current_date not in self.data:
            print("Current date data not found. Copying items from previous day.")
            self.copy_previous_items_only()

        self.ui_scale = 1.0
        self.ui_padding = 5

        self.create_widgets()
        print("Created the widgets.")

    def load_data(self):
        print("Loading data from file.")
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
                print("Data loaded:", self.data)
        else:
            self.data = {}
            print("No existing data file. Initialized empty data.")

    def save_data(self):
        print("Saving data to file.")
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f)
            print("Data saved:", self.data)

    def create_widgets(self):
        print("Creating widgets.")
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=1, fill='both', padx=self.ui_padding, pady=self.ui_padding)
        print("Created notebook.")

        # Create Tracking tab
        self.tracking_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tracking_frame, text='Tracking')
        print("Created tracking tab.")

        # Create Graphs tab
        self.graphs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.graphs_frame, text='Graphs')
        print("Created graphs tab.")

        # Create Settings tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text='Settings')
        print("Created settings tab.")

        self.create_tracking_tab()
        print("Initialized tracking tab content.")

        self.create_graphs_tab()
        print("Initialized graphs tab content.")

        self.create_settings_tab()
        print("Initialized settings tab content.")

    def create_tracking_tab(self):
        print("Creating tracking tab content.")
        # Date navigation frame
        self.date_nav_frame = ttk.Frame(self.tracking_frame)
        self.date_nav_frame.pack()
        print("Created date navigation frame.")

        # Previous Day Button
        self.prev_day_button = ttk.Button(self.date_nav_frame, text="< Previous Day", command=self.go_to_previous_day)
        self.prev_day_button.pack(side='left')
        print("Created 'Previous Day' button.")

        # Next Day Button
        self.next_day_button = ttk.Button(self.date_nav_frame, text="Next Day >", command=self.go_to_next_day)
        self.next_day_button.pack(side='left')
        print("Created 'Next Day' button.")

        # Display current date
        self.date_label = ttk.Label(self.tracking_frame, text="Date: " + self.current_date)
        self.date_label.pack()
        print("Displayed current date:", self.current_date)

        # Buttons
        self.button_frame = ttk.Frame(self.tracking_frame)
        self.button_frame.pack()
        print("Created button frame.")

        self.add_item_button = ttk.Button(self.button_frame, text="Add Item", command=self.add_item)
        self.add_item_button.pack(side='left', padx=self.ui_padding, pady=self.ui_padding)
        self.add_item_button.bind('<Return>', lambda event: self.add_item())
        print("Created 'Add Item' button.")

        self.copy_previous_button = ttk.Button(self.button_frame, text="Copy Previous", command=self.copy_previous)
        self.copy_previous_button.pack(side='left', padx=self.ui_padding, pady=self.ui_padding)
        self.copy_previous_button.bind('<Return>', lambda event: self.copy_previous())
        print("Created 'Copy Previous' button.")

        self.items_frame = ttk.Frame(self.tracking_frame)
        self.items_frame.pack()
        print("Created items frame.")

        # Load items for the current date
        self.load_items()
        print("Loaded items for the current date.")

    def add_item(self):
        print("Adding a new item.")
        new_item_window = tk.Toplevel(self.root)
        new_item_window.title("Add New Item")
        print("Created new item window.")

        label = ttk.Label(new_item_window, text="Item Name:")
        label.pack()
        print("Created label for item name.")

        entry = ttk.Entry(new_item_window)
        entry.pack()
        entry.focus_set()  # Automatically focus on the entry box
        print("Created entry for item name and set focus.")

        # Type selection
        type_label = ttk.Label(new_item_window, text="Item Type:")
        type_label.pack()
        print("Created label for item type.")

        type_var = tk.StringVar(value="complete/incomplete")
        type_options = ["complete/incomplete", "double", "float", "int", "string"]
        type_dropdown = ttk.Combobox(new_item_window, textvariable=type_var, values=type_options, state="readonly")
        type_dropdown.pack()
        type_dropdown.bind('<Key>', self.dropdown_key_navigation)
        print("Created type dropdown menu.")

        def save_item():
            item_name = entry.get()
            item_type = type_var.get()
            print("Saving item:", item_name, "with type:", item_type)
            if item_name:
                if self.current_date not in self.data:
                    self.data[self.current_date] = {}
                    print("Initialized data for current date.")
                # Initialize value based on type
                if item_type == "complete/incomplete":
                    value = False
                elif item_type in ["double", "float", "int"]:
                    value = 0
                elif item_type == "string":
                    value = ""
                self.data[self.current_date][item_name] = {'type': item_type, 'value': value}
                print("Added item to data:", item_name)
                self.save_data()
                self.refresh_items()
                new_item_window.destroy()
                print("New item window closed.")

        # Bind Enter key to save the item
        entry.bind('<Return>', lambda event: save_item())
        type_dropdown.bind('<Return>', lambda event: save_item())
        new_item_window.bind('<Escape>', lambda event: new_item_window.destroy())  # Close window on Escape key

        save_button = ttk.Button(new_item_window, text="Save", command=save_item)
        save_button.pack()
        save_button.bind('<Return>', lambda event: save_item())
        print("Created save button for new item.")

        # Set focus traversal order
        entry.focus_set()
        entry.bind('<Tab>', lambda event: type_dropdown.focus_set())
        type_dropdown.bind('<Tab>', lambda event: save_button.focus_set())

    def copy_previous(self):
        print("Copying previous day's data.")
        previous_date = self.get_previous_date(self.current_date)
        print("Previous date:", previous_date)
        if previous_date and previous_date in self.data:
            # Use deepcopy to avoid shared references
            self.data[self.current_date] = copy.deepcopy(self.data[previous_date])
            print("Copied data from previous date to current date using deepcopy.")
            self.save_data()
            self.refresh_items()
        else:
            print("No previous date to copy from.")

    def copy_previous_items_only(self):
        print("Copying previous day's items without data.")
        previous_date = self.get_previous_date(self.current_date)
        print("Previous date:", previous_date)
        if previous_date and previous_date in self.data:
            # Copy item names and types without values
            self.data[self.current_date] = {}
            for item_name, item_info in self.data[previous_date].items():
                self.data[self.current_date][item_name] = {'type': item_info['type'], 'value': self.get_default_value(item_info['type'])}
                print("Copied item:", item_name, "with type:", item_info['type'])
            self.save_data()
            self.refresh_items()
        else:
            print("No previous date to copy items from.")

    def get_default_value(self, item_type):
        print("Getting default value for type:", item_type)
        if item_type == "complete/incomplete":
            return False
        elif item_type in ["double", "float", "int"]:
            return 0
        elif item_type == "string":
            return ""
        else:
            return None

    def get_previous_date(self, date_str):
        print("Calculating previous date from:", date_str)
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        previous_date_obj = date_obj - timedelta(days=1)
        previous_date_str = previous_date_obj.strftime("%Y-%m-%d")
        print("Previous date is:", previous_date_str)
        return previous_date_str

    def get_next_date(self, date_str):
        print("Calculating next date from:", date_str)
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        next_date_obj = date_obj + timedelta(days=1)
        next_date_str = next_date_obj.strftime("%Y-%m-%d")
        print("Next date is:", next_date_str)
        return next_date_str

    def go_to_previous_day(self):
        print("Navigating to previous day.")
        self.current_date = self.get_previous_date(self.current_date)
        self.date_label.config(text="Date: " + self.current_date)
        print("Updated current date to:", self.current_date)
        if self.current_date not in self.data:
            print("Current date data not found. Copying items from previous day.")
            self.copy_previous_items_only()
        self.refresh_items()

    def go_to_next_day(self):
        print("Navigating to next day.")
        self.current_date = self.get_next_date(self.current_date)
        self.date_label.config(text="Date: " + self.current_date)
        print("Updated current date to:", self.current_date)
        if self.current_date not in self.data:
            print("Current date data not found. Copying items from previous day.")
            self.copy_previous_items_only()
        self.refresh_items()

    def refresh_items(self):
        print("Refreshing items.")
        for widget in self.items_frame.winfo_children():
            widget.destroy()
            print("Destroyed existing item widget.")

        self.load_items()
        print("Reloaded items.")

    def load_items(self):
        print("Loading items.")
        self.item_vars = {}
        if self.current_date in self.data:
            for item_name, item_info in self.data[self.current_date].items():
                item_type = item_info['type']
                value = item_info['value']
                print("Loaded item:", item_name, "Type:", item_type, "Value:", value)

                frame = ttk.Frame(self.items_frame)
                frame.pack(anchor='w', fill='x', padx=self.ui_padding, pady=self.ui_padding)
                print("Created frame for item:", item_name)

                label = ttk.Label(frame, text=item_name)
                label.pack(side='left')
                print("Created label for item:", item_name)

                if item_type == "complete/incomplete":
                    var = tk.BooleanVar(value=value)
                    cb = ttk.Checkbutton(frame, variable=var, command=lambda name=item_name, var=var: self.update_item(name, var.get()))
                    cb.pack(side='left')
                    cb.bind('<Return>', lambda event, name=item_name, var=var: self.toggle_checkbox(var))
                    cb.focus_set()
                    print("Created checkbox for item:", item_name)
                    self.item_vars[item_name] = var
                elif item_type in ["double", "float", "int", "string"]:
                    var = tk.StringVar(value=str(value))
                    entry = ttk.Entry(frame, textvariable=var)
                    entry.pack(side='left')
                    entry.bind('<FocusOut>', lambda event, name=item_name, var=var: self.update_item(name, var.get()))
                    entry.bind('<Return>', lambda event, name=item_name, var=var: self.update_item(name, var.get()))
                    entry.bind('<Tab>', self.focus_next_widget)
                    print("Created entry for item:", item_name)
                    self.item_vars[item_name] = var
                else:
                    print("Unknown type for item:", item_name)
        else:
            print("No items for current date.")

    def toggle_checkbox(self, var):
        # Toggle the BooleanVar associated with the checkbox
        var.set(not var.get())
        print("Toggled checkbox to:", var.get())

    def focus_next_widget(self, event):
        event.widget.tk_focusNext().focus()
        return "break"

    def update_item(self, item_name, value):
        print("Updating item:", item_name, "with value:", value)
        item_type = self.data[self.current_date][item_name]['type']
        if item_type == "complete/incomplete":
            self.data[self.current_date][item_name]['value'] = value
        elif item_type == "int":
            try:
                self.data[self.current_date][item_name]['value'] = int(value)
                print("Set item to int:", int(value))
            except ValueError:
                print("Invalid int value for item:", item_name)
        elif item_type == "float":
            try:
                self.data[self.current_date][item_name]['value'] = float(value)
                print("Set item to float:", float(value))
            except ValueError:
                print("Invalid float value for item:", item_name)
        elif item_type == "double":
            try:
                self.data[self.current_date][item_name]['value'] = float(value)
                print("Set item to double:", float(value))
            except ValueError:
                print("Invalid double value for item:", item_name)
        elif item_type == "string":
            self.data[self.current_date][item_name]['value'] = value
            print("Set item to string:", value)
        else:
            print("Unknown type for item:", item_name)
        self.save_data()

    def create_graphs_tab(self):
        print("Creating graphs tab content.")
        # Paned window dividing item selection and graph view
        self.graphs_pane = ttk.PanedWindow(self.graphs_frame, orient=tk.HORIZONTAL)
        self.graphs_pane.pack(fill=tk.BOTH, expand=1)
        print("Created graphs pane.")

        # Item selection pane
        self.item_selection_pane = ttk.Frame(self.graphs_pane, width=200)
        self.graphs_pane.add(self.item_selection_pane, weight=1)
        print("Created item selection pane.")

        # Graph view pane
        self.graph_view_pane = ttk.Frame(self.graphs_pane)
        self.graphs_pane.add(self.graph_view_pane, weight=4)
        print("Created graph view pane.")

        # Listbox for item selection
        self.item_listbox = tk.Listbox(self.item_selection_pane, exportselection=False)
        self.item_listbox.pack(fill=tk.BOTH, expand=1)
        self.item_listbox.bind('<<ListboxSelect>>', self.plot_item)
        self.item_listbox.bind('<Return>', self.plot_item)
        self.item_listbox.bind('<Double-Button-1>', self.plot_item)
        print("Created item listbox.")

        self.populate_item_listbox()
        print("Populated item listbox.")

    def populate_item_listbox(self):
        print("Populating item listbox.")
        items = set()
        for date in self.data:
            for item_name, item_info in self.data[date].items():
                if item_info['type'] in ["double", "float", "int", "complete/incomplete"]:
                    items.add(item_name)
        self.graphable_items = sorted(list(items))
        print("Graphable items:", self.graphable_items)
        self.item_listbox.delete(0, tk.END)
        for item in self.graphable_items:
            self.item_listbox.insert(tk.END, item)
            print("Inserted item into listbox:", item)

    def plot_item(self, event):
        print("Plotting selected item.")
        selected_indices = self.item_listbox.curselection()
        if not selected_indices:
            print("No item selected.")
            return
        selected_index = selected_indices[0]
        item_name = self.graphable_items[selected_index]
        print("Selected item:", item_name)

        dates = sorted(self.data.keys())
        values = []
        labels = []
        for date in dates:
            if item_name in self.data[date]:
                item_info = self.data[date][item_name]
                item_type = item_info['type']
                value = item_info['value']
                try:
                    if item_type == "complete/incomplete":
                        value = 1 if value else 0
                        print("Converted boolean value to:", value)
                    else:
                        value = float(value)
                    values.append(value)
                    labels.append(date)
                    print("Date:", date, "Value:", value)
                except ValueError:
                    print("Invalid value on date:", date)
                    continue

        # Clear previous plot
        for widget in self.graph_view_pane.winfo_children():
            widget.destroy()
            print("Cleared previous plot.")

        # Plot the data
        fig = Figure(figsize=(5 * self.ui_scale, 4 * self.ui_scale), dpi=100)
        ax = fig.add_subplot(111)
        ax.bar(labels, values)
        ax.set_title(f"Values of {item_name} over time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        fig.autofmt_xdate()

        canvas = FigureCanvasTkAgg(fig, master=self.graph_view_pane)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
        print("Plotted item on graph.")

    def create_settings_tab(self):
        print("Creating settings tab content.")
        padding_label = ttk.Label(self.settings_frame, text="UI Padding:")
        padding_label.pack()
        print("Created padding label.")

        padding_var = tk.DoubleVar(value=self.ui_padding)
        padding_spinbox = ttk.Spinbox(self.settings_frame, from_=0, to=50, increment=1, textvariable=padding_var)
        padding_spinbox.pack()
        print("Created padding spinbox.")

        scale_label = ttk.Label(self.settings_frame, text="UI Scale:")
        scale_label.pack()
        print("Created scale label.")

        scale_var = tk.DoubleVar(value=self.ui_scale)
        scale_spinbox = ttk.Spinbox(self.settings_frame, from_=0.5, to=3.0, increment=0.1, textvariable=scale_var)
        scale_spinbox.pack()
        print("Created scale spinbox.")

        def apply_settings():
            self.ui_padding = padding_var.get()
            self.ui_scale = scale_var.get()
            print("Applied settings: UI Padding =", self.ui_padding, ", UI Scale =", self.ui_scale)
            self.refresh_ui()

        apply_button = ttk.Button(self.settings_frame, text="Apply", command=apply_settings)
        apply_button.pack(pady=self.ui_padding)
        print("Created apply settings button.")

    def refresh_ui(self):
        print("Refreshing UI with new settings.")
        # Recreate widgets with new padding and scale
        for widget in self.root.winfo_children():
            widget.destroy()
            print("Destroyed widget:", widget)
        self.create_widgets()
        print("Recreated widgets with updated settings.")

    def run(self):
        # Set focus traversal order
        self.add_item_button.focus_set()
        self.root.bind('<Tab>', self.focus_next_widget)
        self.root.bind('<Shift-Tab>', self.focus_prev_widget)
        self.root.mainloop()
        print("Application closed.")

    def focus_prev_widget(self, event):
        event.widget.tk_focusPrev().focus()
        return "break"

if __name__ == "__main__":
    print("Starting the application.")
    root = tk.Tk()
    app = DailyTrackingApp(root)
    app.run()
