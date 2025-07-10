# display.py - Table formatting and display helpers

def truncate_company_name(company_name: str, max_length: int = 30) -> str:
    """
    Truncate company name to prevent button shrinking in GUI.
    If the name is longer than max_length, it will be truncated and asterisks added.
    
    Args:
        company_name (str): The original company name
        max_length (int): Maximum length before truncation (default: 30)
    
    Returns:
        str: Truncated company name with asterisks if needed
    """
    if not company_name:
        return ""
    
    if len(company_name) <= max_length:
        return company_name
    
    # Truncate and add asterisks
    truncated = company_name[:max_length-3] + "..."
    return truncated 