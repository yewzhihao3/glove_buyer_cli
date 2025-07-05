import os
import requests
from dotenv import load_dotenv
import re
from typing import List, Dict

PROMPT_PATH = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'deepseek_prompt.txt')

def load_prompt_template():
    with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def is_multipart_response(response: str) -> bool:
    """Detect if the response is part of a multi-part answer (e.g., contains 'Part 1', 'Part 2', etc.)."""
    return bool(re.search(r'Part\s*\d+', response, re.IGNORECASE))

def get_next_part_prompt(original_prompt: str, part_number: int) -> str:
    """Generate a follow-up prompt to request the next part of the answer."""
    return f"{original_prompt}\n\nPlease continue with Part {part_number}. Only return the next part of the list, do not repeat previous results."

def query_deepseek(hs_code: str, keyword: str, country: str, existing_companies: List[str] = None) -> str:
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
    api_key = os.getenv('DEEPSEEK_API_KEY')
    api_url = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    if not api_key:
        raise ValueError('DEEPSEEK_API_KEY not found in environment.')
    prompt_template = load_prompt_template()
    
    # Add existing companies to the prompt if provided
    if existing_companies:
        existing_companies_text = "\n\nIMPORTANT: Please EXCLUDE the following companies that we already have in our database:\n"
        for company in existing_companies:
            existing_companies_text += f"- {company}\n"
        existing_companies_text += "\nPlease provide DIFFERENT companies that are not in this list."
        prompt = prompt_template.format(hs_code=hs_code, keyword=keyword, country=country) + existing_companies_text
    else:
        prompt = prompt_template.format(hs_code=hs_code, keyword=keyword, country=country)
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    data = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    all_parts = []
    part_number = 1
    while True:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        all_parts.append(content)
        # Check if this part indicates there is a next part
        if re.search(rf'Part\s*{part_number}', content, re.IGNORECASE):
            # Look for explicit end or next part
            if re.search(rf'Part\s*{part_number + 1}', content, re.IGNORECASE):
                # The model already included the next part, so break
                break
            # Prepare to fetch the next part
            part_number += 1
            next_prompt = get_next_part_prompt(prompt, part_number)
            data["messages"] = [
                {"role": "user", "content": next_prompt}
            ]
        else:
            break
    return '\n'.join(all_parts)

def query_deepseek_for_hs_codes(country: str) -> str:
    """
    Query DeepSeek to find country-specific HS codes for gloves.
    Returns the raw response from DeepSeek.
    """
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
    api_key = os.getenv('DEEPSEEK_API_KEY')
    api_url = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    if not api_key:
        raise ValueError('DEEPSEEK_API_KEY not found in environment.')
    
    # Load prompt template from file
    prompt_file = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'hs_code_prompt.txt')
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # Fallback prompt if file doesn't exist
        prompt_template = """
        I need to find the most relevant HS codes for {product_type} in {country}. 
        
        Please provide a list of HS codes that are commonly used for {product_type} in {country}, 
        along with their descriptions. Focus on the most relevant codes that would be used 
        for importing or exporting {product_type} to/from {country}.
        
        IMPORTANT: Please format your response EXACTLY as follows:
        
        1. HS Code: [6-digit code] - Description: [detailed description]
        2. HS Code: [6-digit code] - Description: [detailed description]
        3. HS Code: [6-digit code] - Description: [detailed description]
        
        Please provide 5-10 most relevant HS codes for {product_type} in {country}.
        
        Requirements:
        - Use exactly 6-digit HS codes
        - Provide clear, concise descriptions
        - Focus on codes commonly used in {country}
        - Include both import and export relevant codes
        - Do not include any additional formatting, notes, or explanations after the numbered list
        """
    
    prompt = prompt_template.format(country=country)
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    data = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    response = requests.post(api_url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    return result['choices'][0]['message']['content']

def parse_hs_codes_from_deepseek(output: str) -> List[Dict]:
    """
    Parse DeepSeek output for HS codes into a list of dicts.
    Returns a list of dicts with 'hs_code' and 'description' keys.
    Uses a similar approach to parse_deepseek_output in db.py
    """
    import re
    codes = []
    
    # Remove markdown formatting
    output = output.replace('**', '').replace('*', '')
    
    # Split into blocks by numbered list (e.g., 1. HS Code: 4015.12.1000...)
    blocks = re.split(r'\n\d+\. ', '\n' + output)
    
    for block in blocks:
        if not block.strip():
            continue
            
        code_info = {}
        
        # Extract HS Code: match 'HS Code: Value' or similar patterns
        hs_code_match = re.search(r'HS Code:\s*([\d\.]+)', block, re.IGNORECASE)
        if hs_code_match:
            code_info['hs_code'] = hs_code_match.group(1).strip()
        else:
            # Fallback: look for 6+ digit codes at the beginning
            hs_code_match = re.match(r'([\d\.]{6,})', block)
            if hs_code_match:
                code_info['hs_code'] = hs_code_match.group(1).strip()
        
        # Extract Description: match 'Description: Value' or everything after the code
        desc_match = re.search(r'Description:\s*(.+?)(?=\n\d+\.|$)', block, re.DOTALL | re.IGNORECASE)
        if desc_match:
            description = desc_match.group(1).strip()
        else:
            # Fallback: everything after the HS code
            if code_info.get('hs_code'):
                desc_match = re.search(rf'{re.escape(code_info["hs_code"])}\s*[-:]\s*(.+?)(?=\n\d+\.|$)', block, re.DOTALL)
                if desc_match:
                    description = desc_match.group(1).strip()
                else:
                    # Last resort: everything after the first line
                    lines = block.split('\n')
                    if len(lines) > 1:
                        description = ' '.join(lines[1:]).strip()
                    else:
                        description = ''
            else:
                description = ''
        
        # Clean up description
        if description:
            description = re.sub(r'\n+', ' ', description)
            description = re.sub(r'\s+', ' ', description)
            description = description.strip()
        
        # Validate and add to list
        if code_info.get('hs_code') and description:
            # Validate HS code format (8-10 digits with dots or 6+ digits)
            hs_code = code_info['hs_code']
            if (
                (len(hs_code) >= 8 and '.' in hs_code) or  # Full tariff code like 4015.12.1000
                (len(hs_code) >= 6 and re.match(r'^[\d\.]+$', hs_code))  # 6+ digit code
            ):
                # Check if this code is already added
                if not any(code['hs_code'] == hs_code for code in codes):
                    codes.append({
                        'hs_code': hs_code,
                        'description': description
                    })
    
    return codes 