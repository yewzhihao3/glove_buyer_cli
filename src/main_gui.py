import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import GUI_db
import deepseek_agent
import threading
import csv
from tkinter import filedialog

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

NAV_LABELS = [
    "Dashboard",
    "Buyer Search",
    "Potential Buyer Leads",
    "Buyer List",
    "HS Code",
    "Export",
    "Settings"
]

class DashboardContent(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#F5F7FA")
        self._build_ui()
    def _build_ui(self):
        # App Title
        title = ctk.CTkLabel(self, text="Glove Buyer Intelligence Dashboard", font=("Poppins", 28, "bold"), text_color="#2E3A59")
        title.pack(pady=(32, 12))
        # Quick Stats Frame
        stats_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=16)
        stats_frame.pack(pady=8, padx=32, fill="x")
        stats_frame.grid_columnconfigure((0,1,2), weight=1)
        ctk.CTkLabel(stats_frame, text="Total Buyers", font=("Poppins", 16), text_color="#6B7C93").grid(row=0, column=0, padx=24, pady=16)
        ctk.CTkLabel(stats_frame, text="0", font=("Poppins", 22, "bold"), text_color="#0078D4").grid(row=1, column=0)
        ctk.CTkLabel(stats_frame, text="Companies", font=("Poppins", 16), text_color="#6B7C93").grid(row=0, column=1, padx=24, pady=16)
        ctk.CTkLabel(stats_frame, text="0", font=("Poppins", 22, "bold"), text_color="#0078D4").grid(row=1, column=1)
        ctk.CTkLabel(stats_frame, text="HS Codes", font=("Poppins", 16), text_color="#6B7C93").grid(row=0, column=2, padx=24, pady=16)
        ctk.CTkLabel(stats_frame, text="0", font=("Poppins", 22, "bold"), text_color="#0078D4").grid(row=1, column=2)
        # Quick Actions Frame
        actions_frame = ctk.CTkFrame(self, fg_color="#F5F7FA", corner_radius=16)
        actions_frame.pack(pady=24, padx=32, fill="x")
        actions_frame.grid_columnconfigure((0,1,2,3), weight=1)
        ctk.CTkButton(actions_frame, text="Buyer Search", fg_color="#0078D4", hover_color="#005A9E", text_color="#FFFFFF", font=("Poppins", 15, "bold"), corner_radius=8).grid(row=0, column=0, padx=18, pady=18, sticky="ew")
        ctk.CTkButton(actions_frame, text="Potential Buyer Leads", fg_color="#0078D4", hover_color="#005A9E", text_color="#FFFFFF", font=("Poppins", 15, "bold"), corner_radius=8).grid(row=0, column=1, padx=18, pady=18, sticky="ew")
        ctk.CTkButton(actions_frame, text="HS Code Manager", fg_color="#0078D4", hover_color="#005A9E", text_color="#FFFFFF", font=("Poppins", 15, "bold"), corner_radius=8).grid(row=0, column=2, padx=18, pady=18, sticky="ew")
        ctk.CTkButton(actions_frame, text="Export", fg_color="#4CAF50", hover_color="#388E3C", text_color="#FFFFFF", font=("Poppins", 15, "bold"), corner_radius=8).grid(row=0, column=3, padx=18, pady=18, sticky="ew")
        # Recent Activity Placeholder
        recent_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=16)
        recent_frame.pack(pady=8, padx=32, fill="both", expand=True)
        ctk.CTkLabel(recent_frame, text="Recent Activity", font=("Poppins", 18, "bold"), text_color="#2E3A59").pack(pady=(16,8))
        ctk.CTkLabel(recent_frame, text="No recent activity yet.", font=("Poppins", 15), text_color="#B0BEC5").pack(pady=(0,16))

class WorkInProgress(ctk.CTkFrame):
    def __init__(self, master, label):
        super().__init__(master, fg_color="#F5F7FA")
        ctk.CTkLabel(self, text=f"🚧 {label} - Work in Progress 🚧", font=("Poppins", 24, "bold"), text_color="#0078D4").pack(expand=True, pady=80)

class HSCodePage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#F5F7FA")
        self._build_ui()

    def _build_ui(self):
        # Top bar: Add HS Code button (right)
        topbar = ctk.CTkFrame(self, fg_color="#F5F7FA")
        topbar.pack(fill="x", pady=(24, 0), padx=32)
        ctk.CTkLabel(topbar, text="HS Code Manager", font=("Poppins", 22, "bold"), text_color="#2E3A59").pack(side="left")
        add_btn = ctk.CTkButton(topbar, text="Add HS Code", fg_color="#0078D4", hover_color="#005A9E", text_color="#FFFFFF", font=("Poppins", 15, "bold"), corner_radius=8, command=self.add_hs_code)
        add_btn.pack(side="right")

        # Search/filter row
        filter_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        filter_frame.pack(fill="x", pady=(18, 0), padx=32)
        ctk.CTkLabel(filter_frame, text="Country:", font=("Poppins", 15), text_color="#6B7C93").pack(side="left", padx=(0, 8))
        self.country_var = tk.StringVar(value="All")
        countries = ["All"] + GUI_db.get_all_available_countries()
        self.country_combo = ctk.CTkComboBox(filter_frame, variable=self.country_var, values=countries, width=160, font=("Poppins", 15))
        self.country_combo.pack(side="left", padx=(0, 16))
        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(filter_frame, textvariable=self.search_var, placeholder_text="Enter HS code or description...", width=220, font=("Poppins", 15))
        search_entry.pack(side="left", padx=(0, 12))
        search_btn = ctk.CTkButton(filter_frame, text="Search", fg_color="#0078D4", hover_color="#005A9E", text_color="#FFFFFF", font=("Poppins", 15, "bold"), corner_radius=8, width=90, command=self.do_search)
        search_btn.pack(side="left", padx=(0, 8))
        refresh_btn = ctk.CTkButton(filter_frame, text="Refresh Table", fg_color="#4CAF50", hover_color="#388E3C", text_color="#FFFFFF", font=("Poppins", 15), corner_radius=8, width=120, command=self.do_search)
        refresh_btn.pack(side="left")

        # Table frame
        table_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=16)
        table_frame.pack(fill="both", expand=True, padx=32, pady=(18, 0))
        style = ttk.Style()
        style.configure("Zen.Treeview", font=("Poppins", 13), rowheight=32, background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#2E3A59")
        style.configure("Zen.Treeview.Heading", font=("Poppins", 14, "bold"), background="#F5F7FA", foreground="#0078D4")
        style.map("Zen.Treeview", background=[("selected", "#EAF3FF")])
        self.table = ttk.Treeview(table_frame, columns=("hs_code", "country", "desc"), show="headings", style="Zen.Treeview")
        self.table.heading("hs_code", text="HS Code")
        self.table.heading("country", text="Country")
        self.table.heading("desc", text="Description")
        self.table.column("hs_code", width=120, anchor="center")
        self.table.column("country", width=120, anchor="center")
        self.table.column("desc", width=400, anchor="w")
        self.table.pack(fill="both", expand=True, padx=8, pady=8)
        self.populate_table()

        # Action buttons below table
        action_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        action_frame.pack(fill="x", padx=32, pady=(8, 24))
        edit_btn = ctk.CTkButton(action_frame, text="Edit Selected", fg_color="#4CAF50", hover_color="#388E3C", text_color="#FFFFFF", font=("Poppins", 15), corner_radius=8, width=140, command=self.edit_selected)
        delete_btn = ctk.CTkButton(action_frame, text="Delete Selected", fg_color="#B0BEC5", hover_color="#B0BEC5", text_color="#FFFFFF", font=("Poppins", 15), corner_radius=8, width=140, command=self.delete_selected)
        edit_btn.pack(side="right", padx=(0, 12))
        delete_btn.pack(side="right", padx=(0, 12))

    def populate_table(self):
        for row in self.table.get_children():
            self.table.delete(row)
        country = self.country_var.get()
        query = self.search_var.get().strip().lower()
        if country == "All":
            data = GUI_db.get_all_hs_codes()
        else:
            data = GUI_db.get_hs_codes_by_country(country)
        for entry in data:
            if query and query not in entry['hs_code'].lower() and query not in entry['description'].lower():
                continue
            self.table.insert("", "end", iid=entry['id'], values=(entry['hs_code'], entry['country'], entry['description']))

    def do_search(self):
        self.populate_table()

    def add_hs_code(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add HS Code")
        dialog.geometry("500x600")  # Increased height
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Add HS Code", font=("Poppins", 20, "bold"), text_color="#2E3A59").pack(pady=(24, 16))
        
        # Country selection
        country_frame = ctk.CTkFrame(dialog, fg_color="#F5F7FA")
        country_frame.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(country_frame, text="Country:", font=("Poppins", 15)).pack(anchor="w", pady=(12, 4))
        country_var = tk.StringVar()
        countries = GUI_db.get_all_available_countries()
        country_combo = ctk.CTkComboBox(country_frame, variable=country_var, values=countries, font=("Poppins", 14))
        country_combo.pack(fill="x", pady=4)
        
        # HS Code input
        hs_frame = ctk.CTkFrame(dialog, fg_color="#F5F7FA")
        hs_frame.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(hs_frame, text="HS Code:", font=("Poppins", 15)).pack(anchor="w", pady=(12, 4))
        hs_var = tk.StringVar()
        hs_entry = ctk.CTkEntry(hs_frame, textvariable=hs_var, placeholder_text="Enter HS Code", font=("Poppins", 14))
        hs_entry.pack(fill="x", pady=4)
        
        # Description input
        desc_frame = ctk.CTkFrame(dialog, fg_color="#F5F7FA")
        desc_frame.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(desc_frame, text="Description:", font=("Poppins", 15)).pack(anchor="w", pady=(12, 4))
        desc_text = ctk.CTkTextbox(desc_frame, height=100, font=("Poppins", 14))
        desc_text.pack(fill="x", pady=4)
        
        # Progress label
        progress_label = ctk.CTkLabel(dialog, text="", font=("Poppins", 12), text_color="#6B7C93")
        progress_label.pack(pady=(8, 0))
        # Progress bar
        progress_bar = ctk.CTkProgressBar(dialog, orientation="horizontal", mode="indeterminate", width=320)
        progress_bar.pack(pady=(4, 8))
        progress_bar.set(0)
        progress_bar.pack_forget()  # Hide initially
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="#F5F7FA")
        button_frame.pack(fill="x", padx=24, pady=(16, 24))
        
        def on_manual_save():
            hs = hs_var.get().strip()
            desc = desc_text.get("1.0", "end-1c").strip()
            country = country_var.get().strip()
            if not hs or not desc or not country:
                messagebox.showwarning("Missing Data", "Please fill in all fields.")
                return
            if GUI_db.save_hs_code(hs, desc, country):
                dialog.destroy()
                self.populate_table()
            else:
                messagebox.showerror("Duplicate", "This HS code for the selected country already exists.")
        
        def on_deepseek_search():
            country = country_var.get().strip()
            if not country:
                messagebox.showwarning("Missing Country", "Please select a country to search for HS codes.")
                return
            progress_label.configure(text="Searching DeepSeek for HS codes...")
            progress_bar.pack(pady=(4, 8))
            progress_bar.start()
            dialog.update()
            
            def run_deepseek():
                try:
                    raw_response = deepseek_agent.query_deepseek_for_hs_codes(country)
                    parsed_codes = deepseek_agent.parse_hs_codes_from_deepseek(raw_response)
                except Exception as e:
                    def on_error():
                        progress_bar.stop()
                        progress_bar.pack_forget()
                        progress_label.configure(text="")
                        messagebox.showerror("DeepSeek Error", f"Error calling DeepSeek: {str(e)}")
                    dialog.after(0, on_error)
                    return
                def on_done():
                    progress_bar.stop()
                    progress_bar.pack_forget()
                    if not parsed_codes:
                        progress_label.configure(text="")
                        messagebox.showinfo("DeepSeek Results", "No results found from DeepSeek.")
                        return
                    
                    # Create and show the selection dialog
                    selection_dialog = DeepSeekSelectionDialog(dialog, parsed_codes, country)
                    dialog.wait_window(selection_dialog)  # Wait for user to close the dialog
                    
                    # Get the selected codes after dialog is closed
                    selected_codes = getattr(selection_dialog, 'selected_codes', [])
                    
                    if selected_codes:
                        saved_count = 0
                        for code in selected_codes:
                            if GUI_db.save_hs_code(code['hs_code'], code['description'], country, source='DeepSeek'):
                                saved_count += 1
                        messagebox.showinfo("Saved", f"Saved {saved_count} HS codes to the database.")
                        dialog.destroy()
                        self.populate_table()
                    else:
                        progress_label.configure(text="")
                        messagebox.showinfo("DeepSeek Results", "No HS codes were saved.")
                dialog.after(0, on_done)
            threading.Thread(target=run_deepseek, daemon=True).start()
        
        ctk.CTkButton(button_frame, text="Search with DeepSeek", fg_color="#4DA6FF", text_color="#121A26", font=("Poppins", 14, "bold"), command=on_deepseek_search).pack(side="left", padx=(0, 8))
        ctk.CTkButton(button_frame, text="Save", fg_color="#0078D4", text_color="#FFFFFF", font=("Poppins", 14, "bold"), command=on_manual_save).pack(side="left", padx=(0, 8))
        ctk.CTkButton(button_frame, text="Cancel", fg_color="#B0BEC5", text_color="#FFFFFF", font=("Poppins", 14), command=dialog.destroy).pack(side="right")

    def edit_selected(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Edit HS Code", "Please select a row to edit.")
            return
        hs_id = int(selected[0])
        entry = None
        for row in GUI_db.get_all_hs_codes():
            if row['id'] == hs_id:
                entry = row
                break
        if not entry:
            messagebox.showerror("Not Found", "Selected HS code not found.")
            return
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit HS Code")
        dialog.geometry("400x260")
        dialog.grab_set()
        ctk.CTkLabel(dialog, text="HS Code", font=("Poppins", 15)).pack(pady=(24, 4))
        hs_var = tk.StringVar(value=entry['hs_code'])
        hs_entry = ctk.CTkEntry(dialog, textvariable=hs_var, font=("Poppins", 15))
        hs_entry.pack(pady=4)
        ctk.CTkLabel(dialog, text="Description", font=("Poppins", 15)).pack(pady=(12, 4))
        desc_var = tk.StringVar(value=entry['description'])
        desc_entry = ctk.CTkEntry(dialog, textvariable=desc_var, font=("Poppins", 15))
        desc_entry.pack(pady=4)
        ctk.CTkLabel(dialog, text="Country", font=("Poppins", 15)).pack(pady=(12, 4))
        country_var = tk.StringVar(value=entry['country'])
        country_combo = ctk.CTkComboBox(dialog, variable=country_var, values=GUI_db.get_all_available_countries(), font=("Poppins", 15))
        country_combo.pack(pady=4)
        def on_save():
            hs = hs_var.get().strip()
            desc = desc_var.get().strip()
            country = country_var.get().strip()
            if not hs or not desc or not country:
                messagebox.showwarning("Missing Data", "Please fill in all fields.")
                return
            if GUI_db.update_hs_code(hs_id, hs, desc, country):
                dialog.destroy()
                self.populate_table()
            else:
                messagebox.showerror("Error", "Failed to update HS code.")
        ctk.CTkButton(dialog, text="Save", fg_color="#0078D4", text_color="#FFFFFF", font=("Poppins", 15, "bold"), command=on_save).pack(pady=(18, 8))

    def delete_selected(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Delete HS Code", "Please select a row to delete.")
            return
        hs_id = int(selected[0])
        if messagebox.askyesno("Delete HS Code", "Are you sure you want to delete this HS code?"):
            if GUI_db.delete_hs_code(hs_id):
                self.populate_table()
            else:
                messagebox.showerror("Error", "Failed to delete HS code.")



class DeepSeekSelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent, parsed_codes, country):
        super().__init__(parent)
        self.title("Save DeepSeek HS Codes")
        self.geometry("650x00")  # Increased height
        self.grab_set()
        
        self.parsed_codes = parsed_codes
        self.country = country
        self.selected_indices = []
        
        ctk.CTkLabel(self, text=f"Select which HS codes to save for {country}:", font=("Poppins", 18, "bold"), text_color="#2E3A59").pack(pady=(24, 16))
        
        # Select All checkbox
        self.select_all_var = tk.BooleanVar(value=True)
        select_all_cb = ctk.CTkCheckBox(self, text="Select All", variable=self.select_all_var, font=("Poppins", 15), command=self.toggle_all)
        select_all_cb.pack(anchor="w", padx=24, pady=(0, 16))
        
        # Scrollable frame for checkboxes
        scroll_frame = ctk.CTkScrollableFrame(self, height=300)
        scroll_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        
        self.checkboxes = []
        for i, code in enumerate(parsed_codes):
            cb = ctk.CTkCheckBox(
                scroll_frame, 
                text=f"HS Code: {code['hs_code']}\nDescription: {code['description']}", 
                variable=tk.BooleanVar(value=True),
                font=("Poppins", 14)
            )
            cb.pack(anchor="w", pady=4)
            self.checkboxes.append(cb)
        
        # Buttons with improved styling
        button_frame = ctk.CTkFrame(self, fg_color="#F5F7FA", height=80)
        button_frame.pack(fill="x", padx=24, pady=(16, 24))
        button_frame.pack_propagate(False)
        
        # Inner button container for better spacing
        inner_button_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        inner_button_frame.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Left side - Cancel button
        ctk.CTkButton(
            inner_button_frame, 
            text="Cancel", 
            fg_color="#B0BEC5", 
            hover_color="#90A4AE",
            text_color="#FFFFFF", 
            font=("Poppins", 14, "bold"),
            width=120,
            height=36,
            command=self.reject
        ).pack(side="left")
        
        # Right side - Save button
        ctk.CTkButton(
            inner_button_frame, 
            text="Save Selected", 
            fg_color="#0078D4", 
            hover_color="#005A9E",
            text_color="#FFFFFF", 
            font=("Poppins", 14, "bold"),
            width=140,
            height=36,
            command=self.accept
        ).pack(side="right")
    
    def toggle_all(self):
        state = self.select_all_var.get()
        for cb in self.checkboxes:
            cb.select() if state else cb.deselect()
    
    def get_selected(self):
        selected = []
        for i, cb in enumerate(self.checkboxes):
            if cb.get():
                selected.append(self.parsed_codes[i])
        return selected
    
    def accept(self):
        self.selected_codes = self.get_selected()
        self.destroy()
    
    def reject(self):
        self.selected_codes = []
        self.destroy()


class ApolloPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#F5F7FA")
        self._build_ui()
        self.worker = None

    def _build_ui(self):
        # Title
        title_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        title_frame.pack(fill="x", pady=(24, 16), padx=32)
        ctk.CTkLabel(title_frame, text="Potential Buyer Leads Search (Apollo)", font=("Poppins", 24, "bold"), text_color="#2E3A59").pack()
        
        # Search Potential Buyers' Companies button
        search_buyers_btn = ctk.CTkButton(title_frame, text="Search Potential Buyers' Companies", fg_color="#0078D4", hover_color="#005A9E", text_color="#FFFFFF", font=("Poppins", 16, "bold"), corner_radius=8, command=self.open_search_dialog)
        search_buyers_btn.pack(anchor="w", pady=(16, 0))
        
        # Search Parameters Card
        search_card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=16)
        search_card.pack(fill="x", padx=32, pady=(0, 16))
        
        search_content = ctk.CTkFrame(search_card, fg_color="transparent")
        search_content.pack(fill="x", padx=20, pady=18)
        
        ctk.CTkLabel(search_content, text="Search Parameters", font=("Poppins", 18, "bold"), text_color="#0078D4").pack(anchor="w", pady=(0, 12))
        
        # Parameters row
        param_frame = ctk.CTkFrame(search_content, fg_color="transparent")
        param_frame.pack(fill="x", pady=8)
        
        # Country selection
        ctk.CTkLabel(param_frame, text="Country:", font=("Poppins", 15), text_color="#6B7C93").pack(side="left")
        self.country_var = tk.StringVar(value="Select Country")
        self.country_combo = ctk.CTkComboBox(param_frame, variable=self.country_var, values=["Select Country"], width=200, font=("Poppins", 15), command=self.update_company_completer)
        self.country_combo.pack(side="left", padx=(8, 24))
        
        # Company selection
        ctk.CTkLabel(param_frame, text="Company:", font=("Poppins", 15), text_color="#6B7C93").pack(side="left")
        self.company_var = tk.StringVar(value="Type or select a company...")
        company_frame = ctk.CTkFrame(param_frame, fg_color="transparent")
        company_frame.pack(side="left", padx=(8, 24))
        
        # Company display (read-only)
        self.company_display = ctk.CTkEntry(company_frame, textvariable=self.company_var, state="readonly", width=280, font=("Poppins", 15))
        self.company_display.pack(side="left")
        
        # Select company button
        select_btn = ctk.CTkButton(company_frame, text="Select", fg_color="#4CAF50", hover_color="#388E3C", text_color="#FFFFFF", font=("Poppins", 12, "bold"), width=60, height=32, command=self.open_company_selector)
        select_btn.pack(side="left", padx=(8, 0))
        
        # Search button
        self.search_btn = ctk.CTkButton(param_frame, text="Search Decision Makers", fg_color="#0078D4", hover_color="#005A9E", text_color="#FFFFFF", font=("Poppins", 15, "bold"), corner_radius=8, command=self.do_search)
        self.search_btn.pack(side="right")
        
        # Results Card
        results_card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=16)
        results_card.pack(fill="both", expand=True, padx=32, pady=(0, 24))
        
        results_content = ctk.CTkFrame(results_card, fg_color="transparent")
        results_content.pack(fill="both", expand=True, padx=20, pady=18)
        
        # Info and action buttons row
        info_action_frame = ctk.CTkFrame(results_content, fg_color="transparent")
        info_action_frame.pack(fill="x", pady=(0, 12))
        
        self.results_info_label = ctk.CTkLabel(info_action_frame, text="", font=("Poppins", 15), text_color="#0078D4", fg_color="#EAF3FF", corner_radius=8)
        self.results_info_label.pack(side="left", padx=(0, 16))
        
        # Action buttons
        duplicate_btn = ctk.CTkButton(info_action_frame, text="Check for Duplicate", fg_color="#E0E4EA", hover_color="#B0BEC5", text_color="#2E3A59", font=("Poppins", 13, "bold"), corner_radius=6, width=180, height=40, command=self.check_duplicates)
        duplicate_btn.pack(side="right", padx=(0, 24))  # Increased spacing to 24 pixels
        
        export_btn = ctk.CTkButton(info_action_frame, text="Export Results", fg_color="#0078D4", hover_color="#005A9E", text_color="#FFFFFF", font=("Poppins", 15, "bold"), corner_radius=8, width=180, height=40, command=self.export_results)
        export_btn.pack(side="right", padx=(0, 8))  # Add some right padding to the export button
        
        # Table
        table_frame = ctk.CTkFrame(results_content, fg_color="#FFFFFF", corner_radius=12)
        table_frame.pack(fill="both", expand=True, pady=(0, 8))
        
        style = ttk.Style()
        style.configure("Apollo.Treeview", font=("Poppins", 13), rowheight=32, background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#2E3A59")
        style.configure("Apollo.Treeview.Heading", font=("Poppins", 14, "bold"), background="#F5F7FA", foreground="#2E3A59")
        style.map("Apollo.Treeview", background=[("selected", "#EAF3FF")])
        
        self.table = ttk.Treeview(table_frame, columns=("no", "name", "title", "email", "linkedin", "company"), show="headings", style="Apollo.Treeview")
        self.table.heading("no", text="No.")
        self.table.heading("name", text="Name")
        self.table.heading("title", text="Title")
        self.table.heading("email", text="Email")
        self.table.heading("linkedin", text="LinkedIn")
        self.table.heading("company", text="Company")
        self.table.column("no", width=60, anchor="center")
        self.table.column("name", width=150, anchor="w")
        self.table.column("title", width=200, anchor="w")
        self.table.column("email", width=200, anchor="w")
        self.table.column("linkedin", width=150, anchor="w")
        self.table.column("company", width=200, anchor="w")
        self.table.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(results_content, orientation="horizontal", mode="indeterminate", width=320)
        self.progress_bar.pack(pady=8)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # Hide initially
        
        # Initialize data
        self.load_countries()
        self.load_companies()

    def load_countries(self):
        """Load available countries from database"""
        try:
            from GUI_db import get_available_countries
            countries = ["Select Country"] + sorted(get_available_countries())
            self.country_combo.configure(values=countries)
        except Exception as e:
            print(f"Error loading countries: {e}")

    def update_company_completer(self, *args):
        """Update the company completer based on selected country"""
        try:
            from GUI_db import get_all_companies
            selected_country = self.country_var.get().strip()
            companies = get_all_companies()
            company_names = ["Type or select a company..."]
            
            
            
            for company in companies:
                if selected_country == "Select Country" or not selected_country or company.get('country', '').strip() == selected_country:
                    name = company.get('company_name', '')
                    if name:
                        company_names.append(name)
            

            
            # Store the filtered companies for the selector dialog
            self.filtered_companies = company_names
            # Reset to first option
            self.company_var.set("Type or select a company...")
        except Exception as e:
            print(f"Error updating company completer: {e}")

    def open_company_selector(self):
        """Open a searchable company selection dialog"""
        dialog = CompanySelectorDialog(self, self.filtered_companies if hasattr(self, 'filtered_companies') else ["Type or select a company..."])
        self.wait_window(dialog)  # Wait for dialog to close
        selected_company = dialog.get_selected()
        if selected_company and selected_company != "Type or select a company...":
            self.company_var.set(selected_company)
    

    def load_companies(self):
        """Load companies from database"""
        self.update_company_completer()

    def do_search(self):
        """Perform Apollo search for decision makers"""
        company_name = self.company_var.get().strip()
        country = self.country_var.get().strip()
        
        if not company_name or company_name == "Type or select a company...":
            messagebox.showwarning("Missing Company", "Please select or enter a company name.")
            return
            
        if country == "Select Country" or not country:
            messagebox.showwarning("Missing Country", "Please select a country.")
            return
        
        # Start worker thread
        self.search_btn.configure(state="disabled")
        self.progress_bar.pack(pady=8)
        self.progress_bar.start()
        
        def run_apollo_search():
            try:
                from apollo import find_decision_makers_apollo
                from GUI_db import insert_contact, get_all_companies, insert_company
                
                results = find_decision_makers_apollo(company_name, country)
                
                # Save results to database if any found
                if results:
                    # Find the company ID in the database
                    companies = get_all_companies()
                    company_id = None
                    for company in companies:
                        if company.get('company_name', '').lower() == company_name.lower():
                            company_id = company.get('id')
                            break
                    
                    # If company not found, create it
                    if not company_id:
                        company_id, _ = insert_company(company_name, country, '', '', 0)
                    
                    # Save each contact
                    saved_count = 0
                    for contact in results:
                        try:
                            insert_contact(
                                company_id,
                                company_name,
                                contact.get('name', ''),
                                contact.get('title', ''),
                                contact.get('email', ''),
                                contact.get('linkedin', '')
                            )
                            saved_count += 1
                        except Exception as e:
                            print(f"Error saving contact: {e}")
                
                # Add company name to each result for display
                for contact in results:
                    contact['company_name'] = company_name
                
                def on_complete():
                    self.search_btn.configure(state="normal")
                    self.progress_bar.stop()
                    self.progress_bar.pack_forget()
                    
                    if not results:
                        self.results_info_label.configure(text="")
                        messagebox.showinfo("No Results", "No decision makers found for this company.")
                        return
                    
                    self.populate_table(results)
                    from utils.display import truncate_company_name
                    truncated_company = truncate_company_name(company_name)
                    self.results_info_label.configure(text=f"Number of {len(results)} buyer leads found for {truncated_company}")
                    messagebox.showinfo("Search Complete", f"Found and saved {len(results)} decision makers to the database.")
                
                self.after(0, on_complete)
                
            except Exception as e:
                def on_error():
                    self.search_btn.configure(state="normal")
                    self.progress_bar.stop()
                    self.progress_bar.pack_forget()
                    messagebox.showerror("Search Error", f"Error during search: {str(e)}")
                self.after(0, on_error)
        
        threading.Thread(target=run_apollo_search, daemon=True).start()

    def populate_table(self, data):
        """Populate the results table"""
        for row in self.table.get_children():
            self.table.delete(row)
        
        for i, contact in enumerate(data):
            from utils.display import truncate_company_name
            company_name = contact.get('company_name', '')
            truncated_company = truncate_company_name(company_name, max_length=25)
            self.table.insert("", "end", values=(
                str(i + 1),
                contact.get('name', ''),
                contact.get('title', ''),
                contact.get('email', ''),
                contact.get('linkedin', ''),
                truncated_company
            ))

    def export_results(self):
        """Export results to CSV"""
        if not self.table.get_children():
            messagebox.showwarning("No Data", "No results to export.")
            return
            
        try:
            # Generate default filename based on selected company
            selected_company = self.company_var.get()
            if selected_company and selected_company != "Type or select a company...":
                # Clean company name for filename (remove special characters)
                clean_company = "".join(c for c in selected_company if c.isalnum() or c in (' ', '-', '_')).rstrip()
                default_filename = f"{clean_company}_buyer_list.csv"
            else:
                default_filename = "apollo_buyer_list.csv"
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Results",
                initialfile=default_filename
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    # Write headers
                    headers = ["No.", "Name", "Title", "Email", "LinkedIn", "Company"]
                    writer.writerow(headers)
                    
                    # Write data
                    for item in self.table.get_children():
                        values = self.table.item(item)['values']
                        writer.writerow(values)
                
                messagebox.showinfo("Export Complete", f"Results exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting results: {e}")

    def open_search_dialog(self):
        """Open the Apollo search dialog"""
        dialog = ApolloSearchDialog(self)
        # Refresh the companies list after successful search
        self.load_companies()
        self.load_countries()

    def check_duplicates(self):
        """Check the whole database for duplicate companies"""
        try:
            from GUI_db import get_all_companies
            companies = get_all_companies()
            seen = {}
            duplicates = []
            for company in companies:
                key = (company.get('company_name', '').strip().lower(), company.get('country', '').strip().lower())
                if key in seen:
                    duplicates.append(company)
                else:
                    seen[key] = company
            
            if duplicates:
                msg = "Duplicate companies found (same name and country):\n\n"
                for dup in duplicates:
                    msg += f"- {dup.get('company_name', '')} ({dup.get('country', '')})\n"
                messagebox.showwarning("Duplicate Companies", msg)
            else:
                messagebox.showinfo("Duplicate Companies", "No duplicate companies found in the database.")
        except Exception as e:
            messagebox.showerror("Error", f"Error checking duplicates: {e}")


class ApolloSearchDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Search Potential Buyers' Companies")
        self.geometry("500x400")
        self.grab_set()
        
        # Initialize Apollo database
        try:
            from GUI_db import init_apollo_db
            init_apollo_db()
        except Exception as e:
            print(f"Error initializing Apollo database: {e}")
        
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Search Potential Buyers' Companies", font=("Poppins", 18, "bold"), text_color="#2E3A59").pack(pady=(24, 16))
        
        # Search parameters
        params_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        params_frame.pack(fill="x", padx=24, pady=8)
        
        ctk.CTkLabel(params_frame, text="Search Parameters", font=("Poppins", 16, "bold"), text_color="#0078D4").pack(anchor="w", pady=(16, 12))
        
        # Country selection
        country_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
        country_frame.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(country_frame, text="Country:", font=("Poppins", 14)).pack(side="left")
        self.country_var = tk.StringVar(value="")
        self.country_combo = ctk.CTkComboBox(country_frame, variable=self.country_var, values=[""] + self._get_all_countries(), font=("Poppins", 14))
        self.country_combo.pack(side="right", fill="x", expand=True, padx=(8, 0))
        
        # Search depth
        depth_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
        depth_frame.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(depth_frame, text="Search Depth:", font=("Poppins", 14)).pack(side="left")
        self.depth_var = tk.StringVar(value="Medium (1,000 companies)")
        depth_combo = ctk.CTkComboBox(depth_frame, variable=self.depth_var, values=[
            "Small (500 companies)", "Medium (1,000 companies)", "Large (2,500 companies)", 
            "Very Large (5,000 companies)", "Maximum (10,000 companies)"
        ], font=("Poppins", 14))
        depth_combo.pack(side="right", fill="x", expand=True, padx=(8, 0))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", mode="indeterminate", width=320)
        self.progress_bar.pack(pady=16)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # Hide initially
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        button_frame.pack(fill="x", padx=24, pady=(16, 24))
        
        ctk.CTkButton(button_frame, text="Search", fg_color="#0078D4", text_color="#FFFFFF", font=("Poppins", 14, "bold"), command=self.start_search).pack(side="left", padx=(0, 8))
        ctk.CTkButton(button_frame, text="Cancel", fg_color="#B0BEC5", text_color="#FFFFFF", font=("Poppins", 14), command=self.destroy).pack(side="right")

    def _get_all_countries(self):
        """Get all available countries"""
        return [
            # Global countries
            'United States', 'Germany', 'United Kingdom', 'France', 'Italy', 'Spain', 'Canada', 'Australia', 'Brazil', 'Mexico',
            'Russia', 'Turkey', 'Netherlands', 'Switzerland', 'Sweden', 'Norway', 'Denmark', 'Finland', 'Poland', 'Austria',
            'Belgium', 'South Africa', 'Egypt', 'Saudi Arabia', 'United Arab Emirates', 'Argentina', 'Chile', 'New Zealand',
            'Ireland', 'Portugal', 'Greece', 'Czech Republic', 'Hungary', 'Romania', 'Israel', 'Ukraine',
            # Asia countries
            'Malaysia', 'Indonesia', 'Thailand', 'Vietnam', 'Singapore', 'Philippines', 'China', 'India', 'Japan', 'South Korea',
            'Hong Kong', 'Taiwan', 'Bangladesh', 'Pakistan', 'Sri Lanka', 'Myanmar', 'Cambodia', 'Laos', 'Nepal', 'Mongolia',
            'Brunei', 'Timor-Leste', 'Maldives', 'Bhutan'
        ]

    def start_search(self):
        """Start the Apollo company search"""
        country = self.country_var.get().strip()
        depth_text = self.depth_var.get()
        
        # Parse search depth
        depth_map = {
            "Small (500 companies)": 5,
            "Medium (1,000 companies)": 10,
            "Large (2,500 companies)": 25,
            "Very Large (5,000 companies)": 50,
            "Maximum (10,000 companies)": 100
        }
        max_pages = depth_map.get(depth_text, 10)
        
        self.progress_bar.pack(pady=16)
        self.progress_bar.start()
        
        def run_search():
            try:
                from apollo import APOLLO_API_KEY
                import requests
                from GUI_db import insert_company, count_companies
                
                if not APOLLO_API_KEY:
                    raise Exception("APOLLO_API_KEY environment variable not set!")
                
                headers = {
                    "Cache-Control": "no-cache", 
                    "Content-Type": "application/json", 
                    "x-api-key": APOLLO_API_KEY
                }
                
                initial_count = count_companies()
                total_saved = 0
                
                for page in range(1, max_pages + 1):
                    body = {
                        "page": page,
                        "per_page": 100,
                        "industry_tags": [
                            "Pharmaceuticals", "Medical Devices", "Healthcare",
                            "Manufacturing", "Medical Supplies"
                        ],
                        "q_organization_keyword_tags": [
                            "latex gloves", "nitrile gloves", "medical gloves",
                            "surgical gloves", "exam gloves", "biohazard protection"
                        ]
                    }
                    
                    if country:
                        body["organization_locations"] = [country]
                    
                    resp = requests.post(
                        "https://api.apollo.io/v1/mixed_companies/search",
                        headers=headers,
                        json=body
                    )
                    
                    if resp.status_code != 200:
                        raise Exception(f"Apollo API error (status {resp.status_code}): {resp.text}")
                    
                    data = resp.json()
                    companies = data.get("organizations", [])
                    
                    if not companies:
                        break
                    
                    for comp in companies:
                        company_name = comp.get("name", "")
                        country_val = comp.get("location_country") or comp.get("country") or country
                        domain = comp.get("primary_domain")
                        industry = comp.get("industry", "")
                        employee_count = comp.get("estimated_num_employees")
                        
                        if not company_name or not domain:
                            continue
                        
                        cid, is_new = insert_company(company_name, country_val, domain, industry, employee_count)
                        if is_new:
                            total_saved += 1
                
                def on_complete():
                    self.progress_bar.stop()
                    self.progress_bar.pack_forget()
                    messagebox.showinfo("Search Complete", f"Found and saved {total_saved} new companies to the database.")
                    self.destroy()
                
                self.after(0, on_complete)
                
            except Exception as e:
                def on_error():
                    self.progress_bar.stop()
                    self.progress_bar.pack_forget()
                    messagebox.showerror("Search Error", f"Error during search: {str(e)}")
                self.after(0, on_error)
        
        threading.Thread(target=run_search, daemon=True).start()


class CompanySelectorDialog(ctk.CTkToplevel):
    def __init__(self, parent, company_list):
        super().__init__(parent)
        self.title("Select Company")
        self.geometry("500x400")
        self.grab_set()
        
        self.company_list = company_list
        self.selected_company = None
        
        ctk.CTkLabel(self, text="Select a company:", font=("Poppins", 16, "bold"), text_color="#2E3A59").pack(pady=(24, 12))
        
        # Search frame
        search_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        search_frame.pack(fill="x", padx=24, pady=(0, 12))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search)
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, placeholder_text="Search companies...", font=("Poppins", 14))
        search_entry.pack(fill="x", padx=16, pady=16)
        
        # Scrollable frame for companies
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=250)
        self.scroll_frame.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        
        # Company buttons (will be populated)
        self.company_buttons = []
        self.populate_companies(self.company_list)
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        button_frame.pack(fill="x", padx=24, pady=(0, 24))
        
        ctk.CTkButton(button_frame, text="Cancel", fg_color="#B0BEC5", text_color="#FFFFFF", font=("Poppins", 14), command=self.destroy).pack(side="right")

    def populate_companies(self, companies):
        """Populate the scrollable frame with company buttons"""
        # Clear existing buttons
        for btn in self.company_buttons:
            btn.destroy()
        self.company_buttons.clear()
        

        
        # Add company buttons
        for company in companies:
            if company != "Type or select a company...":
                from utils.display import truncate_company_name
                truncated_company = truncate_company_name(company, max_length=35)
                btn = ctk.CTkButton(
                    self.scroll_frame,  # Create button in scroll_frame, not self
                    text=truncated_company, 
                    fg_color="#FFFFFF", 
                    hover_color="#EAF3FF",
                    text_color="#2E3A59", 
                    font=("Poppins", 13),
                    anchor="w",
                    command=lambda c=company: self.select_company(c)
                )
                btn.pack(fill="x", padx=8, pady=2)
                self.company_buttons.append(btn)
        


    def on_search(self, *args):
        """Filter companies based on search term"""
        search_term = self.search_var.get().lower()
        filtered_companies = []
        
        for company in self.company_list:
            if search_term in company.lower():
                filtered_companies.append(company)
        
        self.populate_companies(filtered_companies)

    def select_company(self, company):
        """Select a company and close dialog"""
        
        self.selected_company = company
        self.destroy()

    def get_selected(self):
        """Return the selected company"""
        return self.selected_company


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Glove Buyer Intelligence Dashboard")
        # Launch in fullscreen more reliably
        self.after(10, self.maximize_window)
        self.configure(bg="#F5F7FA")
        self.sidebar = ctk.CTkFrame(self, fg_color="#F5F7FA", width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        # Branding/logo placeholder
        ctk.CTkLabel(self.sidebar, text="LOGO", font=("Poppins", 22, "bold"), text_color="#0078D4").pack(pady=(32, 24))
        # Nav buttons
        self.nav_btns = []
        for i, label in enumerate(NAV_LABELS):
            btn = ctk.CTkButton(self.sidebar, text=label, font=("Poppins", 16, "bold"), fg_color="#F5F7FA", text_color="#6B7C93", hover_color="#E0E4EA", corner_radius=8, anchor="w", width=180, height=44, command=lambda idx=i: self.switch_page(idx))
            btn.pack(fill="x", padx=16, pady=2)
            self.nav_btns.append(btn)
        # Main content area
        self.content_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        self.content_frame.pack(side="left", fill="both", expand=True)
        self.pages = [
            DashboardContent(self.content_frame),
            WorkInProgress(self.content_frame, "Buyer Search"),
            ApolloPage(self.content_frame),
            WorkInProgress(self.content_frame, "Buyer List"),
            HSCodePage(self.content_frame),
            WorkInProgress(self.content_frame, "Export"),
            WorkInProgress(self.content_frame, "Settings"),
        ]
        for page in self.pages:
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            page.lower()
        self.switch_page(0)
    
    def maximize_window(self):
        """Maximize the window reliably"""
        self.state('zoomed')
        self.update()
    
    def switch_page(self, idx):
        for i, btn in enumerate(self.nav_btns):
            if i == idx:
                btn.configure(fg_color="#FFFFFF", text_color="#0078D4")
            else:
                btn.configure(fg_color="#F5F7FA", text_color="#6B7C93")
        for i, page in enumerate(self.pages):
            if i == idx:
                page.lift()
            else:
                page.lower()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop() 