def obfuscate_token(clear_token):
    key = 123
    try:
        return "".join(chr(ord(c) ^ key) for c in clear_token)
    except TypeError:
        return ""

def deobfuscate_token(obfuscated_token):
    key = 123
    try:
        return "".join(chr(ord(c) ^ key) for c in obfuscated_token)
    except TypeError:
        return ""
