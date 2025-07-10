import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import GUI_db
import deepseek_agent
import threading
import csv
import os
from tkinter import filedialog
import db  # Add this import at the top if not present

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

NAV_LABELS = [
    "Dashboard",
    "Quick Buyer Search (AI)",
    "Verified Buyer Leads (Apollo)",
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

class BuyerSearchPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#F5F7FA")
        self._build_ui()
        self.search_results = []
        self.worker = None

    def _build_ui(self):
        # Title
        title_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        title_frame.pack(fill="x", pady=(24, 16), padx=32)
        ctk.CTkLabel(title_frame, text="Quick Buyer Search (AI)", font=("Poppins", 24, "bold"), text_color="#2E3A59").pack()
        
        # Search Parameters Card
        search_card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=16)
        search_card.pack(fill="x", padx=32, pady=(0, 16))
        
        search_content = ctk.CTkFrame(search_card, fg_color="transparent")
        search_content.pack(fill="x", padx=20, pady=18)
        
        ctk.CTkLabel(search_content, text="Search Parameters", font=("Poppins", 18, "bold"), text_color="#0078D4").pack(anchor="w", pady=(0, 12))
        
        # Parameters grid
        param_frame = ctk.CTkFrame(search_content, fg_color="transparent")
        param_frame.pack(fill="x", pady=8)
        param_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Country selection
        country_frame = ctk.CTkFrame(param_frame, fg_color="transparent")
        country_frame.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=4)
        ctk.CTkLabel(country_frame, text="Country:", font=("Poppins", 15), text_color="#6B7C93").pack(anchor="w")
        self.country_var = tk.StringVar(value="Select Country")
        country_display_frame = ctk.CTkFrame(country_frame, fg_color="transparent")
        country_display_frame.pack(fill="x", pady=(4, 0))
        self.country_display = ctk.CTkEntry(country_display_frame, textvariable=self.country_var, state="readonly", width=200, font=("Poppins", 15))
        self.country_display.pack(side="left")
        select_country_btn = ctk.CTkButton(country_display_frame, text="Select", fg_color="#4CAF50", hover_color="#388E3C", text_color="#FFFFFF", font=("Poppins", 12, "bold"), width=60, height=32, command=self.open_country_selector)
        select_country_btn.pack(side="left", padx=(8, 0))
        
        # HS Code selection
        hs_frame = ctk.CTkFrame(param_frame, fg_color="transparent")
        hs_frame.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)
        ctk.CTkLabel(hs_frame, text="HS Code:", font=("Poppins", 15), text_color="#6B7C93").pack(anchor="w")
        self.hs_var = tk.StringVar(value="Select HS Code")
        hs_display_frame = ctk.CTkFrame(hs_frame, fg_color="transparent")
        hs_display_frame.pack(fill="x", pady=(4, 0))
        self.hs_display = ctk.CTkEntry(hs_display_frame, textvariable=self.hs_var, state="readonly", width=200, font=("Poppins", 15))
        self.hs_display.pack(side="left")
        select_hs_btn = ctk.CTkButton(hs_display_frame, text="Select", fg_color="#4CAF50", hover_color="#388E3C", text_color="#FFFFFF", font=("Poppins", 12, "bold"), width=60, height=32, command=self.open_hs_code_selector)
        select_hs_btn.pack(side="left", padx=(8, 0))
        
        # Keyword selection
        keyword_frame = ctk.CTkFrame(param_frame, fg_color="transparent")
        keyword_frame.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=4)
        ctk.CTkLabel(keyword_frame, text="Product Keyword:", font=("Poppins", 15), text_color="#6B7C93").pack(anchor="w")
        self.keyword_var = tk.StringVar(value="Select Keyword")
        keyword_display_frame = ctk.CTkFrame(keyword_frame, fg_color="transparent")
        keyword_display_frame.pack(fill="x", pady=(4, 0))
        self.keyword_display = ctk.CTkEntry(keyword_display_frame, textvariable=self.keyword_var, state="readonly", width=200, font=("Poppins", 15))
        self.keyword_display.pack(side="left")
        select_keyword_btn = ctk.CTkButton(keyword_display_frame, text="Select", fg_color="#4CAF50", hover_color="#388E3C", text_color="#FFFFFF", font=("Poppins", 12, "bold"), width=60, height=32, command=self.open_keyword_selector)
        select_keyword_btn.pack(side="left", padx=(8, 0))
        
        # Custom keyword entry
        custom_frame = ctk.CTkFrame(param_frame, fg_color="transparent")
        custom_frame.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)
        ctk.CTkLabel(custom_frame, text="Custom Keyword:", font=("Poppins", 15), text_color="#6B7C93").pack(anchor="w")
        self.custom_keyword_var = tk.StringVar()
        self.custom_keyword_entry = ctk.CTkEntry(custom_frame, textvariable=self.custom_keyword_var, placeholder_text="Enter custom keyword...", width=200, font=("Poppins", 15), state="disabled")
        self.custom_keyword_entry.pack(fill="x", pady=(4, 0))
        
        # Search button
        button_frame = ctk.CTkFrame(param_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        
        self.search_btn = ctk.CTkButton(button_frame, text="Search Buyers with AI", fg_color="#0078D4", hover_color="#005A9E", text_color="#FFFFFF", font=("Poppins", 15, "bold"), corner_radius=8, command=self.perform_search)
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
        export_btn = ctk.CTkButton(info_action_frame, text="Export Results", fg_color="#0078D4", hover_color="#005A9E", text_color="#FFFFFF", font=("Poppins", 15, "bold"), corner_radius=8, width=180, height=40, command=self.export_results)
        export_btn.pack(side="right", padx=(0, 8))
        
        # Table
        table_frame = ctk.CTkFrame(results_content, fg_color="#FFFFFF", corner_radius=12)
        table_frame.pack(fill="both", expand=True, pady=(0, 8))
        
        style = ttk.Style()
        style.configure("BuyerSearch.Treeview", font=("Poppins", 13), rowheight=32, background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#2E3A59")
        style.configure("BuyerSearch.Treeview.Heading", font=("Poppins", 14, "bold"), background="#F5F7FA", foreground="#2E3A59")
        style.map("BuyerSearch.Treeview", background=[("selected", "#1E3A8A")], foreground=[("selected", "#FFFFFF")])
        
        self.table = ttk.Treeview(table_frame, columns=("no", "company", "country", "website", "description"), show="headings", style="BuyerSearch.Treeview")
        self.table.heading("no", text="No.")
        self.table.heading("company", text="Company Name")
        self.table.heading("country", text="Country")
        self.table.heading("website", text="Website")
        self.table.heading("description", text="Description")
        self.table.column("no", width=60, anchor="center")
        self.table.column("company", width=200, anchor="w")
        self.table.column("country", width=120, anchor="center")
        self.table.column("website", width=200, anchor="w")
        self.table.column("description", width=300, anchor="w")
        self.table.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(results_content, orientation="horizontal", mode="indeterminate", width=320)
        self.progress_bar.pack(pady=8)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # Hide initially
        
        # Initialize data
        self.load_countries()
        self.load_keywords()
        self.load_hs_codes()

    def load_countries(self):
        """Load available countries from database that have HS codes"""
        try:
            # Get all HS codes from database
            hs_codes = GUI_db.get_all_hs_codes()
            # Extract unique countries that have HS codes
            countries_with_hs_codes = set()
            for code in hs_codes:
                if code.get('country'):
                    countries_with_hs_codes.add(code['country'])
            
            # Sort the countries
            countries = ["Select Country"] + sorted(list(countries_with_hs_codes))
            self.country_list = countries
        except Exception as e:
            print(f"Error loading countries: {e}")
            self.country_list = ["Select Country"]

    def load_keywords(self):
        """Load keyword options from file and add custom option"""
        try:
            keyword_file = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'keyword_options.txt')
            if os.path.exists(keyword_file):
                with open(keyword_file, 'r', encoding='utf-8') as f:
                    keywords = [line.strip() for line in f if line.strip()]
                self.keyword_list = ["Select Keyword"] + keywords + ["Custom Keyword"]
            else:
                self.keyword_list = ["Select Keyword", "Custom Keyword"]
        except Exception as e:
            print(f"Error loading keywords: {e}")
            self.keyword_list = ["Select Keyword", "Custom Keyword"]

    def load_hs_codes(self):
        """Load HS codes based on selected country"""
        try:
            # Default to empty list, will be populated when country is selected
            self.hs_code_list = ["Select HS Code"]
        except Exception as e:
            print(f"Error loading HS codes: {e}")
            self.hs_code_list = ["Select HS Code"]

    def open_country_selector(self):
        """Open country selection dialog"""
        dialog = CountrySelectorDialog(self, self.country_list)
        self.wait_window(dialog)
        selected_country = dialog.get_selected()
        if selected_country and selected_country != "Select Country":
            self.country_var.set(selected_country)
            # Update HS codes for selected country
            self.update_hs_codes_for_country(selected_country)
            # Reset keyword selection when country changes
            self.reset_keyword_selection()

    def open_hs_code_selector(self):
        """Open HS code selection dialog"""
        country = self.country_var.get().strip()
        if country == "Select Country" or not country:
            messagebox.showwarning("Select Country First", "Please select a country first to see available HS codes.")
            return
        
        # Get HS codes for selected country
        try:
            hs_codes = GUI_db.get_hs_codes_by_country(country)
            hs_options = ["Select HS Code"]
            for code in hs_codes:
                hs_options.append(f"{code['hs_code']} - {code['description']}")
            
            dialog = HSCodeSelectorDialog(self, hs_options)
            self.wait_window(dialog)
            selected_hs = dialog.get_selected()
            if selected_hs and selected_hs != "Select HS Code":
                self.hs_var.set(selected_hs)
        except Exception as e:
            print(f"Error loading HS codes for country: {e}")
            messagebox.showerror("Error", f"Error loading HS codes for {country}")

    def open_keyword_selector(self):
        """Open keyword selection dialog"""
        dialog = KeywordSelectorDialog(self, self.keyword_list)
        self.wait_window(dialog)
        selected_keyword = dialog.get_selected()
        if selected_keyword and selected_keyword != "Select Keyword":
            if selected_keyword == "Custom Keyword":
                # Enable custom keyword entry and clear other selections
                self.keyword_var.set("Custom Keyword")
                self.custom_keyword_entry.configure(state="normal")
                self.custom_keyword_entry.focus()
            else:
                # Disable custom keyword entry and set the selected keyword
                self.keyword_var.set(selected_keyword)
                self.custom_keyword_entry.configure(state="disabled")
                self.custom_keyword_var.set("")

    def reset_keyword_selection(self):
        """Reset keyword selection to default state"""
        self.keyword_var.set("Select Keyword")
        self.custom_keyword_entry.configure(state="disabled")
        self.custom_keyword_var.set("")

    def update_hs_codes_for_country(self, country):
        """Update HS codes when country changes"""
        try:
            if country == "Select Country":
                self.hs_code_list = ["Select HS Code"]
            else:
                hs_codes = GUI_db.get_hs_codes_by_country(country)
                self.hs_code_list = ["Select HS Code"] + [f"{code['hs_code']} - {code['description']}" for code in hs_codes]
            self.hs_var.set("Select HS Code")
        except Exception as e:
            print(f"Error updating HS codes for country: {e}")

    def refresh_buyer_search_data(self):
        """Refresh BuyerSearchPage data after new HS codes are added"""
        self.load_countries()
        print("[DEBUG] Refreshed BuyerSearchPage data")

    def perform_search(self):
        """Perform AI buyer search"""
        country = self.country_var.get().strip()
        hs_selection = self.hs_var.get().strip()
        keyword = self.keyword_var.get().strip()
        custom_keyword = self.custom_keyword_var.get().strip()
        
        # Validation
        if country == "Select Country" or not country:
            messagebox.showwarning("Missing Country", "Please select a country.")
            return
            
        if hs_selection == "Select HS Code" or not hs_selection:
            messagebox.showwarning("Missing HS Code", "Please select an HS code.")
            return
            
        # Check if custom keyword is selected but no custom keyword entered
        if keyword == "Custom Keyword":
            if not custom_keyword:
                messagebox.showwarning("Missing Custom Keyword", "Please enter a custom keyword.")
                return
            final_keyword = custom_keyword
        elif keyword == "Select Keyword" or not keyword:
            messagebox.showwarning("Missing Keyword", "Please select a keyword or choose custom keyword.")
            return
        else:
            final_keyword = keyword
        
        # Extract HS code from selection
        hs_code = hs_selection.split(" - ")[0] if " - " in hs_selection else hs_selection
        
        # Start search
        self.search_btn.configure(state="disabled")
        self.progress_bar.pack(pady=8)
        self.progress_bar.start()
        
        def run_ai_search():
            try:
                import deepseek_agent
                import db
                
                print(f"[DEBUG] Starting DeepSeek search with parameters:")
                print(f"[DEBUG] HS Code: {hs_code}")
                print(f"[DEBUG] Keyword: {final_keyword}")
                print(f"[DEBUG] Country: {country}")
                
                # Query DeepSeek for buyers
                print("[DEBUG] Calling deepseek_agent.query_deepseek...")
                result = deepseek_agent.query_deepseek(hs_code, final_keyword, country, [])
                print(f"[DEBUG] DeepSeek raw result received: {len(str(result))} characters")
                print(f"[DEBUG] First 500 chars of result: {str(result)[:500]}...")
                
                # Parse results
                print("[DEBUG] Parsing DeepSeek output...")
                companies = db.parse_deepseek_output(result)
                print(f"[DEBUG] Parsed {len(companies) if companies else 0} companies from result")
                
                # Debug: Show what fields each company has
                if companies:
                    print("[DEBUG] Sample company data:")
                    for i, company in enumerate(companies[:3]):  # Show first 3 companies
                        print(f"[DEBUG] Company {i+1}:")
                        print(f"[DEBUG]   Name: {company.get('company_name', 'MISSING')}")
                        print(f"[DEBUG]   Country: {company.get('company_country', 'MISSING')}")
                        print(f"[DEBUG]   Website: {company.get('company_website_link', 'MISSING')}")
                        print(f"[DEBUG]   Description: {company.get('description', 'MISSING')[:100]}...")
                
                # Save to database
                if companies:
                    print("[DEBUG] Saving companies to database...")
                    # Use the new deepseek_buyer_search_results table
                    saved_count = GUI_db.insert_deepseek_results(hs_code, final_keyword, country, companies)
                    print(f"[DEBUG] Saved {saved_count} companies to deepseek_buyer_search_results table")
                
                def on_complete():
                    self.search_btn.configure(state="normal")
                    self.progress_bar.stop()
                    self.progress_bar.pack_forget()
                    
                    if not companies:
                        self.results_info_label.configure(text="")
                        messagebox.showinfo("No Results", "No buyers found for the specified criteria.")
                        return
                    
                    self.search_results = companies
                    self.populate_table(companies)
                    self.results_info_label.configure(text=f"Found {len(companies)} potential buyers")
                    
                    # Auto-refresh country list after successful search
                    self.load_countries()
                    
                    messagebox.showinfo("Search Complete", f"Found and saved {len(companies)} potential buyers to the database.")
                
                self.after(0, on_complete)
                
            except Exception as search_error:
                print(f"[DEBUG] Error during AI search: {search_error}")
                print(f"[DEBUG] Error type: {type(search_error)}")
                import traceback
                print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
                
                def on_error(error=search_error):
                    self.search_btn.configure(state="normal")
                    self.progress_bar.stop()
                    self.progress_bar.pack_forget()
                    messagebox.showerror("Search Error", f"Error during AI search: {str(error)}")
                self.after(0, on_error)
        
        threading.Thread(target=run_ai_search, daemon=True).start()

    def populate_table(self, data):
        """Populate the results table"""
        for row in self.table.get_children():
            self.table.delete(row)
        
        for i, company in enumerate(data):
            self.table.insert("", "end", values=(
                str(i + 1),
                company.get('company_name', ''),
                company.get('company_country', ''),
                company.get('company_website_link', ''),
                company.get('description', '')
            ))

    def export_results(self):
        """Export results to CSV"""
        if not self.search_results:
            messagebox.showwarning("No Data", "No results to export.")
            return
            
        try:
            # Generate default filename
            country = self.country_var.get()
            hs_code = self.hs_var.get().split(" - ")[0] if " - " in self.hs_var.get() else self.hs_var.get()
            default_filename = f"{country}_{hs_code}_buyers.csv"
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Buyer Search Results",
                initialfile=default_filename
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    # Write headers
                    headers = ["No.", "Company Name", "Country", "Website", "Description"]
                    writer.writerow(headers)
                    
                    # Write data
                    for i, company in enumerate(self.search_results):
                        writer.writerow([
                            str(i + 1),
                            company.get('company_name', ''),
                            company.get('company_country', ''),
                            company.get('company_website_link', ''),
                            company.get('description', '')
                        ])
                
                messagebox.showinfo("Export Complete", f"Results exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting results: {e}")


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
        style.map("Zen.Treeview", background=[("selected", "#1E3A8A")], foreground=[("selected", "#FFFFFF")])
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
                
                # Refresh other pages that depend on HS codes
                self.refresh_other_pages()
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
                        
                        # Refresh other pages that depend on HS codes
                        self.refresh_other_pages()
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
                # Refresh other pages that depend on HS codes
                self.refresh_other_pages()
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
                # Refresh other pages that depend on HS codes
                self.refresh_other_pages()
            else:
                messagebox.showerror("Error", "Failed to delete HS code.")

    def refresh_other_pages(self):
        """Refresh other pages that depend on HS codes"""
        try:
            # Find the main app instance to access other pages
            main_app = self.winfo_toplevel()
            if hasattr(main_app, 'pages'):
                # Refresh BuyerSearchPage country list
                buyer_search_page = main_app.pages[1]  # Index 1 is BuyerSearchPage
                if hasattr(buyer_search_page, 'refresh_buyer_search_data'):
                    buyer_search_page.refresh_buyer_search_data()
                    print("[DEBUG] Refreshed BuyerSearchPage data")
        except Exception as e:
            print(f"[DEBUG] Error refreshing other pages: {e}")



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
        country_frame = ctk.CTkFrame(param_frame, fg_color="transparent")
        country_frame.pack(side="left", padx=(8, 24))
        
        # Country display (read-only)
        self.country_display = ctk.CTkEntry(country_frame, textvariable=self.country_var, state="readonly", width=200, font=("Poppins", 15))
        self.country_display.pack(side="left")
        
        # Select country button
        select_country_btn = ctk.CTkButton(country_frame, text="Select", fg_color="#4CAF50", hover_color="#388E3C", text_color="#FFFFFF", font=("Poppins", 12, "bold"), width=60, height=32, command=self.open_country_selector)
        select_country_btn.pack(side="left", padx=(8, 0))
        
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
        style.map("Apollo.Treeview", background=[("selected", "#1E3A8A")], foreground=[("selected", "#FFFFFF")])
        
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
        
        # No need to update dropdown since we're using a Select button now

    def load_countries(self):
        """Load available countries from database that have companies"""
        try:
            # Get all companies from database
            companies = GUI_db.get_all_companies()
            # Extract unique countries that have companies
            countries_with_companies = set()
            for company in companies:
                if company.get('country'):
                    countries_with_companies.add(company['country'])
            
            # Sort the countries
            countries = ["Select Country"] + sorted(list(countries_with_companies))
            self.country_list = countries
            print(f"[DEBUG] Apollo countries loaded: {len(countries)} countries with companies in DB")
        except Exception as e:
            print(f"Error loading countries: {e}")
            self.country_list = ["Select Country"]

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

    def open_country_selector(self):
        """Open a searchable country selection dialog"""
        dialog = CountrySelectorDialog(self, self.country_list)
        self.wait_window(dialog)  # Wait for dialog to close
        selected_country = dialog.get_selected()
        if selected_country and selected_country != "Select Country":
            self.country_var.set(selected_country)
            # Update company completer when country changes
            self.update_company_completer()

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

    def refresh_apollo_data(self):
        """Refresh Apollo page data after new companies are added"""
        self.load_countries()
        self.load_companies()
        print("[DEBUG] Refreshed Apollo page data")

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
                    
                    # Auto-refresh country and company lists after successful search
                    self.load_countries()
                    self.load_companies()
                    
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
        # The refresh will be handled by the dialog's on_complete callback

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
        self.country_var = tk.StringVar(value="Select Country")
        country_display_frame = ctk.CTkFrame(country_frame, fg_color="transparent")
        country_display_frame.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self.country_display = ctk.CTkEntry(country_display_frame, textvariable=self.country_var, state="readonly", font=("Poppins", 14))
        self.country_display.pack(side="left", fill="x", expand=True)
        select_country_btn = ctk.CTkButton(country_display_frame, text="Select", fg_color="#4CAF50", hover_color="#388E3C", text_color="#FFFFFF", font=("Poppins", 12, "bold"), width=60, height=32, command=self.open_country_selector)
        select_country_btn.pack(side="right", padx=(8, 0))
        
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

    def open_country_selector(self):
        """Open a searchable country selection dialog"""
        country_list = ["Select Country"] + self._get_all_countries()
        dialog = CountrySelectorDialog(self, country_list)
        self.wait_window(dialog)  # Wait for dialog to close
        selected_country = dialog.get_selected()
        if selected_country and selected_country != "Select Country":
            self.country_var.set(selected_country)

    def start_search(self):
        """Start the Apollo company search"""
        country = self.country_var.get().strip()
        if country == "Select Country" or not country:
            messagebox.showwarning("Missing Country", "Please select a country.")
            return
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
                    
                    # Refresh the parent Apollo page after successful search
                    if hasattr(self.master, 'refresh_apollo_data'):
                        self.master.refresh_apollo_data()
                    
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


class CountrySelectorDialog(ctk.CTkToplevel):
    def __init__(self, parent, country_list):
        super().__init__(parent)
        self.title("Select Country")
        self.geometry("500x400")
        self.grab_set()
        
        self.country_list = country_list
        self.selected_country = None
        
        ctk.CTkLabel(self, text="Select a country:", font=("Poppins", 16, "bold"), text_color="#2E3A59").pack(pady=(24, 12))
        
        # Search frame
        search_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        search_frame.pack(fill="x", padx=24, pady=(0, 12))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search)
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, placeholder_text="Search countries...", font=("Poppins", 14))
        search_entry.pack(fill="x", padx=16, pady=16)
        
        # Scrollable frame for countries
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=250)
        self.scroll_frame.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        
        # Country buttons (will be populated)
        self.country_buttons = []
        self.populate_countries(self.country_list)
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        button_frame.pack(fill="x", padx=24, pady=(0, 24))
        
        ctk.CTkButton(button_frame, text="Cancel", fg_color="#B0BEC5", text_color="#FFFFFF", font=("Poppins", 14), command=self.destroy).pack(side="right")

    def populate_countries(self, countries):
        """Populate the scrollable frame with country buttons"""
        # Clear existing buttons
        for btn in self.country_buttons:
            btn.destroy()
        self.country_buttons.clear()
        
        # Add country buttons
        for country in countries:
            if country != "Select Country":
                btn = ctk.CTkButton(
                    self.scroll_frame,
                    text=country, 
                    fg_color="#FFFFFF", 
                    hover_color="#EAF3FF",
                    text_color="#2E3A59", 
                    font=("Poppins", 13),
                    anchor="w",
                    command=lambda c=country: self.select_country(c)
                )
                btn.pack(fill="x", padx=8, pady=2)
                self.country_buttons.append(btn)

    def on_search(self, *args):
        """Filter countries based on search term"""
        search_term = self.search_var.get().lower()
        filtered_countries = []
        
        for country in self.country_list:
            if search_term in country.lower():
                filtered_countries.append(country)
        
        self.populate_countries(filtered_countries)

    def select_country(self, country):
        """Select a country and close dialog"""
        self.selected_country = country
        self.destroy()

    def get_selected(self):
        """Return the selected country"""
        return self.selected_country


class HSCodeSelectorDialog(ctk.CTkToplevel):
    def __init__(self, parent, hs_code_list):
        super().__init__(parent)
        self.title("Select HS Code")
        self.geometry("600x400")
        self.grab_set()
        
        self.hs_code_list = hs_code_list
        self.selected_hs_code = None
        
        ctk.CTkLabel(self, text="Select an HS Code:", font=("Poppins", 16, "bold"), text_color="#2E3A59").pack(pady=(24, 12))
        
        # Search frame
        search_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        search_frame.pack(fill="x", padx=24, pady=(0, 12))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search)
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, placeholder_text="Search HS codes...", font=("Poppins", 14))
        search_entry.pack(fill="x", padx=16, pady=16)
        
        # Scrollable frame for HS codes
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=250)
        self.scroll_frame.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        
        # HS code buttons (will be populated)
        self.hs_code_buttons = []
        self.populate_hs_codes(self.hs_code_list)
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        button_frame.pack(fill="x", padx=24, pady=(0, 24))
        
        ctk.CTkButton(button_frame, text="Cancel", fg_color="#B0BEC5", text_color="#FFFFFF", font=("Poppins", 14), command=self.destroy).pack(side="right")

    def populate_hs_codes(self, hs_codes):
        """Populate the scrollable frame with HS code buttons"""
        # Clear existing buttons
        for btn in self.hs_code_buttons:
            btn.destroy()
        self.hs_code_buttons.clear()
        
        # Add HS code buttons
        for hs_code in hs_codes:
            if hs_code != "Select HS Code":
                # Truncate long descriptions for display
                display_text = hs_code
                if len(display_text) > 60:
                    display_text = display_text[:57] + "..."
                
                btn = ctk.CTkButton(
                    self.scroll_frame,
                    text=display_text, 
                    fg_color="#FFFFFF", 
                    hover_color="#EAF3FF",
                    text_color="#2E3A59", 
                    font=("Poppins", 12),
                    anchor="w",
                    command=lambda hc=hs_code: self.select_hs_code(hc)
                )
                btn.pack(fill="x", padx=8, pady=2)
                self.hs_code_buttons.append(btn)

    def on_search(self, *args):
        """Filter HS codes based on search term"""
        search_term = self.search_var.get().lower()
        filtered_hs_codes = []
        
        for hs_code in self.hs_code_list:
            if search_term in hs_code.lower():
                filtered_hs_codes.append(hs_code)
        
        self.populate_hs_codes(filtered_hs_codes)

    def select_hs_code(self, hs_code):
        """Select an HS code and close dialog"""
        self.selected_hs_code = hs_code
        self.destroy()

    def get_selected(self):
        """Return the selected HS code"""
        return self.selected_hs_code


class KeywordSelectorDialog(ctk.CTkToplevel):
    def __init__(self, parent, keyword_list):
        super().__init__(parent)
        self.title("Select Keyword")
        self.geometry("500x400")
        self.grab_set()
        
        self.keyword_list = keyword_list
        self.selected_keyword = None
        
        ctk.CTkLabel(self, text="Select a keyword:", font=("Poppins", 16, "bold"), text_color="#2E3A59").pack(pady=(24, 12))
        
        # Search frame
        search_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        search_frame.pack(fill="x", padx=24, pady=(0, 12))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search)
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, placeholder_text="Search keywords...", font=("Poppins", 14))
        search_entry.pack(fill="x", padx=16, pady=16)
        
        # Scrollable frame for keywords
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=250)
        self.scroll_frame.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        
        # Keyword buttons (will be populated)
        self.keyword_buttons = []
        self.populate_keywords(self.keyword_list)
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        button_frame.pack(fill="x", padx=24, pady=(0, 24))
        
        ctk.CTkButton(button_frame, text="Cancel", fg_color="#B0BEC5", text_color="#FFFFFF", font=("Poppins", 14), command=self.destroy).pack(side="right")

    def populate_keywords(self, keywords):
        """Populate the scrollable frame with keyword buttons"""
        # Clear existing buttons
        for btn in self.keyword_buttons:
            btn.destroy()
        self.keyword_buttons.clear()
        
        # Add keyword buttons
        for keyword in keywords:
            if keyword != "Select Keyword":
                btn = ctk.CTkButton(
                    self.scroll_frame,
                    text=keyword, 
                    fg_color="#FFFFFF", 
                    hover_color="#EAF3FF",
                    text_color="#2E3A59", 
                    font=("Poppins", 13),
                    anchor="w",
                    command=lambda k=keyword: self.select_keyword(k)
                )
                btn.pack(fill="x", padx=8, pady=2)
                self.keyword_buttons.append(btn)

    def on_search(self, *args):
        """Filter keywords based on search term"""
        search_term = self.search_var.get().lower()
        filtered_keywords = []
        
        for keyword in self.keyword_list:
            if search_term in keyword.lower():
                filtered_keywords.append(keyword)
        
        self.populate_keywords(filtered_keywords)

    def select_keyword(self, keyword):
        """Select a keyword and close dialog"""
        self.selected_keyword = keyword
        self.destroy()

    def get_selected(self):
        """Return the selected keyword"""
        return self.selected_keyword


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Glove Buyer Intelligence Dashboard")
        # Launch in fullscreen more reliably
        self.after(10, self.maximize_window)
        self.configure(bg="#F5F7FA")
        
        # Sidebar with increased width for longer names
        self.sidebar = ctk.CTkFrame(self, fg_color="#F5F7FA", width=280, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Branding/logo placeholder
        ctk.CTkLabel(self.sidebar, text="LOGO", font=("Poppins", 22, "bold"), text_color="#0078D4").pack(pady=(32, 24))
        
        # Nav buttons
        self.nav_btns = []
        for i, label in enumerate(NAV_LABELS):
            btn = ctk.CTkButton(
                self.sidebar, 
                text=label, 
                font=("Poppins", 15, "bold"), 
                fg_color="#F5F7FA", 
                text_color="#6B7C93", 
                hover_color="#E0E4EA", 
                corner_radius=8, 
                anchor="w", 
                height=44, 
                command=lambda idx=i: self.switch_page(idx)
            )
            btn.pack(fill="x", padx=16, pady=2)
            self.nav_btns.append(btn)
        
        # Main content area
        self.content_frame = ctk.CTkFrame(self, fg_color="#F5F7FA")
        self.content_frame.pack(side="left", fill="both", expand=True)
        
        self.pages = [
            DashboardContent(self.content_frame),
            BuyerSearchPage(self.content_frame),
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