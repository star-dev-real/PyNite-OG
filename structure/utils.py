import json
from pathlib import Path

def load_json_safe(file_path, default=None):
    if default is None:
        default = {}
    
    if not file_path.exists():
        print(f"Warning: File not found: {file_path}")
        return default
    
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            continue
        except Exception as e:
            print(f"Error loading {file_path} with {encoding}: {e}")
            continue
    
    print(f"Warning: Could not load {file_path} with any encoding")
    return default