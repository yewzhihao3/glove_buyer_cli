import os
from typing import List, Tuple, Optional

HS_CODES_TXT = os.path.join(os.path.dirname(__file__), '..', 'data', 'hs_codes.txt')
HS_CODES_XLSX = os.path.join(os.path.dirname(__file__), '..', 'data', 'hs_codes.xlsx')

def load_hs_codes_txt() -> List[Tuple[str, str]]:
    """Load HS codes from txt file. Returns list of (code, description)."""
    codes = []
    if not os.path.exists(HS_CODES_TXT):
        return codes
    with open(HS_CODES_TXT, 'r', encoding='utf-8') as f:
        for line in f:
            if '-' in line:
                code, desc = line.strip().split('-', 1)
                codes.append((code.strip(), desc.strip()))
    return codes

def load_hs_codes_xlsx() -> List[Tuple[str, str]]:
    """Load HS codes from xlsx file. Returns list of (code, description)."""
    try:
        import pandas as pd
    except ImportError:
        print('pandas is required to read Excel files.')
        return []
    if not os.path.exists(HS_CODES_XLSX):
        return []
    df = pd.read_excel(HS_CODES_XLSX)
    return [(str(row['HS Code']), str(row['Description'])) for _, row in df.iterrows()]

def display_hs_codes(codes: List[Tuple[str, str]]):
    """Display HS codes as a numbered list."""
    for idx, (code, desc) in enumerate(codes, 1):
        print(f"{idx}. {code} - {desc}")

def select_hs_code(codes: List[Tuple[str, str]]) -> Optional[Tuple[str, str]]:
    """Prompt user to select an HS code by number."""
    if not codes:
        print('No HS codes available.')
        return None
    display_hs_codes(codes)
    try:
        choice = int(input('Select HS code by number: '))
        if 1 <= choice <= len(codes):
            return codes[choice-1]
    except Exception:
        pass
    print('Invalid selection.')
    return None


#CRUD Functions
def add_hs_code(code: str, desc: str) -> bool:
    """Add a new HS code to Excel file. Returns True if successful, False if duplicate."""
    try:
        import pandas as pd
    except ImportError:
        print('pandas is required to write Excel files.')
        return False
    # Add to Excel
    if os.path.exists(HS_CODES_XLSX):
        df = pd.read_excel(HS_CODES_XLSX)
        # Check for duplicates
        if ((df['HS Code'] == code) & (df['Description'] == desc)).any():
            print('HS code and description already exist in Excel.')
            return False
        df = pd.concat([df, pd.DataFrame([[code, desc]], columns=['HS Code', 'Description'])], ignore_index=True)
    else:
        df = pd.DataFrame([[code, desc]], columns=['HS Code', 'Description'])
    df.to_excel(HS_CODES_XLSX, index=False)
    return True

def edit_hs_code(index: int, new_code: str, new_desc: str) -> bool:
    """Edit HS code at the given index (1-based) in Excel. Returns True if successful."""
    try:
        import pandas as pd
    except ImportError:
        print('pandas is required to edit Excel files.')
        return False
    # Edit Excel
    if os.path.exists(HS_CODES_XLSX):
        df = pd.read_excel(HS_CODES_XLSX)
        if not (0 <= index-1 < len(df)):
            print('Invalid index for Excel.')
            return False
        df.at[index-1, 'HS Code'] = new_code
        df.at[index-1, 'Description'] = new_desc
        df.to_excel(HS_CODES_XLSX, index=False)
    else:
        print('Excel file not found.')
        return False
    return True

def delete_hs_code(index: int) -> bool:
    """Delete HS code at the given index (1-based) in Excel. Returns True if successful."""
    try:
        import pandas as pd
    except ImportError:
        print('pandas is required to edit Excel files.')
        return False
    # Delete from Excel
    if os.path.exists(HS_CODES_XLSX):
        df = pd.read_excel(HS_CODES_XLSX)
        if not (0 <= index-1 < len(df)):
            print('Invalid index for Excel.')
            return False
        df = df.drop(df.index[index-1]).reset_index(drop=True)
        df.to_excel(HS_CODES_XLSX, index=False)
    else:
        print('Excel file not found.')
        return False
    return True 