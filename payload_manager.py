from itertools import product
import sys
import os


def load_file(file_path):
    """Load non-empty lines from a file into a list."""
    if not os.path.isfile(file_path):
        print(f"[-] Error: File not found: {file_path}")
        sys.exit(1)
    
    if not os.access(file_path, os.R_OK):
        print(f"[-] Error: File not readable: {file_path}")
        sys.exit(1)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = [line.strip() for line in file if line.strip()]
        
        if not lines:
            print(f"[-] Error: File is empty or contains only empty lines: {file_path}")
            sys.exit(1)
        
        return lines
    except Exception as e:
        print(f"[-] Error reading file {file_path}: {e}")
        sys.exit(1)


def generate_payload(payload_spec):
    """Generate payloads from 'generate:chars:length' specification or load from file."""
    if payload_spec.startswith("generate:"):
        try:
            parts = payload_spec.split(":", 2)
            if len(parts) != 3:
                raise ValueError("Invalid format")
            
            _, chars, length = parts
            length = int(length)
            
            if length <= 0:
                raise ValueError("Length must be positive")
            if not chars:
                raise ValueError("Characters must be provided")
            if length > 10:  # Prevent excessive memory usage
                print(f"[-] Warning: Large payload generation (length={length}). This may consume significant memory.")
            
            payloads = [''.join(combo) for combo in product(chars, repeat=length)]
            
            if not payloads:
                raise ValueError("No payloads generated")
            
            return payloads
            
        except ValueError as e:
            print(f"[-] Invalid payload format: {payload_spec}. Use 'generate:chars:length'. Error: {e}")
            sys.exit(1)
    
    return load_file(payload_spec)


def prepare_payloads(field_keys, payload_sources):
    """Prepare payload lists for each brute-force field."""
    if len(field_keys) != len(payload_sources):
        print("[-] Error: Number of brute-force fields and payload sources must match")
        sys.exit(1)
    
    return [generate_payload(source) for source in payload_sources]