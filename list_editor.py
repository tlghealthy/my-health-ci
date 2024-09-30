import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import sys

class DragDropListbox(ttk.Treeview):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.bind('<ButtonPress-1>', self.on_button_press)
        self.bind('<B1-Motion>', self.on_motion)
        self.bind('<ButtonRelease-1>', self.on_button_release)
        self._dragging = False
        self._dragged_item = None
        self._drag_label = None

    def on_button_press(self, event):
        # Identify the item under cursor
        item = self.identify_row(event.y)
        if item:
            self._dragged_item = item
            self._dragging = True
            # Create a floating label to represent the dragged item
            self._create_drag_label(event)

    def on_motion(self, event):
        if self._dragging and self._dragged_item:
            # Update the position of the drag label
            if self._drag_label:
                # Move the Toplevel window using geometry
                self._drag_label.geometry(f"+{event.x_root + 20}+{event.y_root + 20}")
            # Highlight potential drop target
            target = self.identify_row(event.y)
            if target:
                self._highlight_target(target)
            else:
                self._remove_highlight()

    def on_button_release(self, event):
        if self._dragging and self._dragged_item:
            # Identify drop target
            target = self.identify_row(event.y)
            if target and target != self._dragged_item:
                self.move(self._dragged_item, '', self.index(target))
                self.event_generate('<<TreeviewReordered>>')
            self._cleanup_drag()

    def _create_drag_label(self, event):
        # Get item text
        item_text = self.item(self._dragged_item, 'values')[1]
        # Create a Toplevel window as drag label
        self._drag_label = tk.Toplevel(self)
        self._drag_label.overrideredirect(True)
        self._drag_label.attributes('-topmost', True)
        label = tk.Label(self._drag_label, text=item_text, background='lightblue', relief='solid', borderwidth=1)
        label.pack()
        # Position the label near the cursor
        self._drag_label.geometry(f"+{event.x_root + 20}+{event.y_root + 20}")

    def _highlight_target(self, target):
        # Remove previous highlight
        self._remove_highlight()
        # Highlight the target row
        self.item(target, tags=('highlight',))
        self.tag_configure('highlight', background='lightyellow')

    def _remove_highlight(self):
        # Remove highlight from all items
        for item in self.get_children():
            self.item(item, tags=())

    def _cleanup_drag(self):
        # Reset dragging flags
        self._dragging = False
        self._dragged_item = None
        # Destroy the drag label
        if self._drag_label:
            self._drag_label.destroy()
            self._drag_label = None
        # Remove any highlights
        self._remove_highlight()

class ListApp:
    CONFIG_FILE = "config.json"  # Configuration file name

    def __init__(self, root):
        self.root = root
        self.root.title("List Manager")
        self.list_file = "list.json"  # Default file
        self.items = []
        self.config = {
            "last_opened_file": "",
            "recent_files": []
        }

        self.load_config()
        self.create_widgets()

        # Bind the Escape key to save and exit
        self.root.bind("<Escape>", self.on_escape)

        # If last_opened_file exists, load it
        if self.config.get("last_opened_file") and os.path.exists(self.config["last_opened_file"]):
            self.list_file = self.config["last_opened_file"]
            self.load_items()
        else:
            # If default list.json exists, load it
            if os.path.exists(self.list_file):
                self.load_items()
            else:
                self.items = []
                self.refresh_tree()

    def create_widgets(self):
        # Create the menu bar
        self.create_menu()

        # Frame for the list
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview with two columns: Index and Item
        self.tree = DragDropListbox(list_frame, columns=("Index", "Item"), show='headings', selectmode='extended')
        self.tree.heading("Index", text="Index")
        self.tree.heading("Item", text="Item")
        self.tree.column("Index", width=50, anchor='center')
        self.tree.column("Item", width=300, anchor='w')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for the Treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind the reorder event to update indices and save
        self.tree.bind('<<TreeviewReordered>>', self.on_reorder)

        # Frame for buttons and entry
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # Entry for new items
        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(control_frame, textvariable=self.entry_var)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        self.entry.bind("<Return>", lambda event: self.add_item())

        # Add button
        add_button = ttk.Button(control_frame, text="Add", command=self.add_item)
        add_button.pack(side=tk.LEFT, padx=(0,5))

        # Remove button
        remove_button = ttk.Button(control_frame, text="Remove", command=self.remove_items)
        remove_button.pack(side=tk.LEFT)

    def create_menu(self):
        # Create a menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Create the File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)

        # Add Load and New options to the File menu
        file_menu.add_command(label="Load", command=self.load_file)
        file_menu.add_command(label="New", command=self.new_file)

        # Add Recent Files submenu
        self.recent_files_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_files_menu)
        self.update_recent_files_menu()

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_escape)

    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # Ensure recent_files is a list
                if not isinstance(self.config.get("recent_files", []), list):
                    self.config["recent_files"] = []
                # Ensure last_opened_file is a string
                if not isinstance(self.config.get("last_opened_file", ""), str):
                    self.config["last_opened_file"] = ""
            except (json.JSONDecodeError, IOError) as e:
                messagebox.showerror("Error", f"Failed to load config file:\n{e}")
                self.config = {
                    "last_opened_file": "",
                    "recent_files": []
                }
        else:
            # Initialize default config
            self.config = {
                "last_opened_file": "",
                "recent_files": []
            }

    def save_config(self):
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            messagebox.showerror("Error", f"Failed to save config file:\n{e}")

    def add_to_recent_files(self, file_path):
        # Remove the file if it's already in the list
        if file_path in self.config["recent_files"]:
            self.config["recent_files"].remove(file_path)
        # Insert the file at the beginning
        self.config["recent_files"].insert(0, file_path)
        # Keep only the last 10 entries
        self.config["recent_files"] = self.config["recent_files"][:10]
        # Save the config
        self.save_config()
        # Update the Recent Files menu
        self.update_recent_files_menu()

    def update_recent_files_menu(self):
        # Clear the current menu
        self.recent_files_menu.delete(0, tk.END)
        if not self.config["recent_files"]:
            self.recent_files_menu.add_command(label="No Recent Files", state=tk.DISABLED)
            return
        for idx, file_path in enumerate(self.config["recent_files"], start=1):
            # Check if the file exists
            if os.path.exists(file_path):
                display_name = f"{idx}. {os.path.basename(file_path)}"
                # Use lambda with default argument to capture file_path
                self.recent_files_menu.add_command(
                    label=display_name,
                    command=lambda path=file_path: self.open_recent_file(path)
                )
            else:
                # If file doesn't exist, disable the menu item
                display_name = f"{idx}. {os.path.basename(file_path)} (Missing)"
                self.recent_files_menu.add_command(
                    label=display_name,
                    state=tk.DISABLED
                )

    def open_recent_file(self, file_path):
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"The file does not exist:\n{file_path}")
            # Remove the missing file from recent_files
            self.config["recent_files"].remove(file_path)
            self.save_config()
            self.update_recent_files_menu()
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list) and all(isinstance(item, str) for item in data):
                self.items = data
                self.list_file = file_path
                self.config["last_opened_file"] = file_path
                self.add_to_recent_files(file_path)
                self.refresh_tree()
                self.save_items()  # Save to the newly loaded file
                messagebox.showinfo("Success", f"Loaded {file_path} successfully.")
            else:
                messagebox.showerror("Error", "Selected file does not contain a valid list of strings.")
        except (json.JSONDecodeError, IOError) as e:
            messagebox.showerror("Error", f"Failed to load {file_path}:\n{e}")

    def load_file(self):
        """
        Open a file dialog to select a JSON file and load items from it.
        """
        # Prompt the user to select a JSON file
        file_path = filedialog.askopenfilename(
            title="Select a JSON file",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list) and all(isinstance(item, str) for item in data):
                    self.items = data
                    self.list_file = file_path  # Update current file
                    self.config["last_opened_file"] = file_path
                    self.add_to_recent_files(file_path)
                    self.refresh_tree()
                    self.save_items()  # Save to the newly loaded file
                    messagebox.showinfo("Success", f"Loaded {file_path} successfully.")
                else:
                    messagebox.showerror("Error", "Selected file does not contain a valid list of strings.")
            except (json.JSONDecodeError, IOError) as e:
                messagebox.showerror("Error", f"Failed to load {file_path}:\n{e}")

    def new_file(self):
        """
        Create a new list file. Optionally, prompt for a filename.
        """
        # Confirm if the user wants to create a new file (overwrite current)
        if self.items:
            if not messagebox.askyesno("Create New File", "Are you sure you want to create a new file? Unsaved changes will be lost."):
                return

        # Prompt the user to specify a new file name
        file_path = filedialog.asksaveasfilename(
            title="Create New JSON File",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if file_path:
            # Check if the file already exists
            if os.path.exists(file_path):
                if not messagebox.askyesno("Overwrite File", f"The file {file_path} already exists. Do you want to overwrite it?"):
                    return
            # Initialize an empty list
            self.items = []
            self.list_file = file_path
            self.config["last_opened_file"] = file_path
            self.add_to_recent_files(file_path)
            self.refresh_tree()
            self.save_items()  # Save the new empty list to the specified file
            messagebox.showinfo("Success", f"Created new file: {file_path}")

    def load_items(self):
        if os.path.exists(self.list_file):
            try:
                with open(self.list_file, 'r', encoding='utf-8') as f:
                    self.items = json.load(f)
                # Validate the loaded data
                if not isinstance(self.items, list) or not all(isinstance(item, str) for item in self.items):
                    raise ValueError("JSON file does not contain a list of strings.")
            except (json.JSONDecodeError, IOError, ValueError) as e:
                messagebox.showerror("Error", f"Failed to load {self.list_file}:\n{e}")
                self.items = []
        else:
            self.items = []

        self.refresh_tree()

    def save_items(self):
        try:
            with open(self.list_file, 'w', encoding='utf-8') as f:
                json.dump(self.items, f, indent=4, ensure_ascii=False)
        except IOError as e:
            messagebox.showerror("Error", f"Failed to save {self.list_file}:\n{e}")

    def refresh_tree(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Insert items with index
        for idx, item in enumerate(self.items, start=1):
            self.tree.insert('', 'end', values=(idx, item))

    def add_item(self):
        new_item = self.entry_var.get().strip()
        if not new_item:
            messagebox.showwarning("Input Error", "Cannot add empty item.")
            return
        if len(new_item) > 200:
            messagebox.showwarning("Input Error", "Item must be 200 characters or less.")
            return
        self.items.append(new_item)
        self.entry_var.set('')
        self.refresh_tree()
        self.save_items()
        self.add_to_recent_files(self.list_file)  # Update recent files

    def remove_items(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "No item selected to remove.")
            return
        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion", f"Are you sure you want to remove {len(selected)} item(s)?"):
            return
        # Get indices of selected items
        indices_to_remove = sorted([int(self.tree.item(item, 'values')[0]) -1 for item in selected], reverse=True)
        for idx in indices_to_remove:
            del self.items[idx]
        self.refresh_tree()
        self.save_items()
        self.add_to_recent_files(self.list_file)  # Update recent files

    def on_reorder(self, event):
        # Update self.items based on the new order in the tree
        new_items = []
        for child in self.tree.get_children():
            item_text = self.tree.item(child, 'values')[1]
            new_items.append(item_text)
        self.items = new_items
        self.refresh_tree()
        self.save_items()
        self.add_to_recent_files(self.list_file)  # Update recent files

    def on_escape(self, event=None):
        """
        Save the current list and exit the application,
        discarding any partially entered text.
        """
        # Clear the entry field (discard partial input)
        self.entry_var.set('')
        # Save the current list
        self.save_items()
        # Save the config
        self.save_config()
        # Exit the application
        self.root.quit()

def main():
    root = tk.Tk()
    app = ListApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
