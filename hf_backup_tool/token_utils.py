# token_utils.py
def deobfuscate_token(obfuscated_token):
    """Deobfuscates the API token."""
    # Your deobfuscation logic here (example: simple XOR)
    key = 123  # Replace with your actual key
    try:
        return "".join(chr(ord(c) ^ key) for c in obfuscated_token)
    except TypeError:
        return ""  # Return empty on error
