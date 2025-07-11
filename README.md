# 🧤 Glove Buyer Intel CLI

A command-line tool to help you search for and manage international buyers of gloves (and similar products) using HS codes, product keywords, and country filters. The tool leverages AI (DeepSeek) to find real-world importers and buyers, and provides a database and exportable CSV for your research.

---

## Features

- **Search Buyers**: Find real, verifiable glove buyers/importers by HS code, product keyword, and country/region.
- **HS Code Management**: Add, edit, delete, and view HS codes and their descriptions.
- **Buyer Search History**: View, edit, or delete past search results.
- **Export**: Export your buyer search results to CSV for further analysis.
- **Customizable**: Easily add new product keywords or countries.

---

## Installation

1. **Clone the repository:**

   ```bash
   git clone <your-repo-url>
   cd glove_buyer_cli
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   **Dependencies:**

   - `typer`
   - `rich`
   - `python-dotenv`
   - `requests`
   - `pandas` (required for Excel/HS code management)

3. **(Optional) Set up environment variables:**
   - If you use any API keys or secrets, place them in `config/.env` (not included by default).

---

## Usage

Run the CLI from the project root:

```bash
python src/main.py run
```

You will be presented with an interactive menu:

### Sample Main Menu Screenshot

```
───────────────────────────── 🧠 Glove Buyer Intel CLI 🧠 ─────────────────────────────
1. Select HS Code to Search
2. Search Buyers with DeepSeek
3. Manage HS Codes (CRUD)
4. Manage Buyer Search History
5. Export Results (CSV)
6. Exit

Select an option: _
```

### User Flow Diagram

```mermaid
flowchart TD
    A[Start CLI] --> B[Show Main Menu]
    B --> C{Choose Action}
    C -->|Select HS Code to Search| D[Select HS Code]
    D --> E[Return to Main Menu]
    C -->|Search Buyers with DeepSeek| F[Select HS Code]
    F --> G[Select Product Keyword]
    G --> H[Select Country/Region]
    H --> I[Build Prompt with HS Code, Keyword, Country]
    I --> J[Query DeepSeek API]
    J --> K[Display & Save Results]
    K --> B
    C -->|Manage HS Codes| L[Add/Edit/Delete/View HS Codes]
    L --> B
    C -->|Manage Search History| M[View/Edit/Delete Past Results]
    M --> B
    C -->|Export Results| N[Export Results to CSV]
    N --> B
    C -->|Exit| O[Quit Application]
```

### Menu Options

1. **Select HS Code to Search**: Choose an HS code and description for your search.
2. **Search Buyers with DeepSeek**:
   - Choose a region (Asia or Global).
   - Select a country (from the list or enter a custom one).
   - Select a product keyword (from `prompts/keyword_options.txt` or enter your own).
   - The tool will query DeepSeek and display/save the results.
3. **Manage HS Codes (CRUD)**: Add, edit, delete, or view HS codes.
4. **Manage Buyer Search History**: View, edit, or delete previous search results.
5. **Export Results (CSV)**: Export all search results to a CSV file in the `EXPORT/` directory.
6. **Exit**: Quit the application.

---

## Data & Configuration

- **HS Codes**: Stored in `data/hs_codes.xlsx` (columns: `HS Code`, `Description`). You can manage these via the CLI.
- **Buyer Results**: Stored in a local SQLite database at `data/results.db`.
- **Prompts**:
  - `prompts/asia_countries.txt` — List of Asian countries.
  - `prompts/global_countries.txt` — List of global countries.
  - `prompts/keyword_options.txt` — List of product keywords (e.g., `nitrile gloves`, `latex gloves`).
  - `prompts/deepseek_prompt.txt` — The AI prompt template for DeepSeek queries.

---

## Example Workflow

1. **Start the CLI**:  
   `python src/main.py run`

2. **Search for Buyers**:

   - Select "Search Buyers with DeepSeek".
   - Choose "Asia" or "Global".
   - Pick a country (or enter a custom one).
   - Select a product keyword (or enter your own).
   - View and save the results.

3. **Export Results**:
   - Choose "Export Results (CSV)" to save all results to `EXPORT/buyer_search_results.csv`.

---

## Customization

- **Add More Keywords**: Edit `prompts/keyword_options.txt` to add more product keywords.
- **Add More Countries**: Edit `prompts/asia_countries.txt` or `prompts/global_countries.txt`.
- **Modify the AI Prompt**: Edit `prompts/deepseek_prompt.txt` for advanced customization of the search instructions.

---

## Requirements

- Python 3.7+
- See `requirements.txt` for Python dependencies.

---

## Notes

- The tool uses a local SQLite database (`data/results.db`) to store search results and prevent duplicates.
- The HS code Excel file (`data/hs_codes.xlsx`) is required for HS code management and search.
- The `EXPORT/` directory will contain your exported CSV files.
- If you encounter issues with Excel file handling, ensure `pandas` is installed.

---

## License

MIT License

---

## Acknowledgements

- [Typer](https://typer.tiangolo.com/) for CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- [Pandas](https://pandas.pydata.org/) for Excel/CSV handling
