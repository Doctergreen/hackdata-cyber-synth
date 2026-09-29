import hashlib
import re
from typing import Any, Optional

def mask_email(email: str) -> str:
    """
    Mask email address: s***@domain.com
    Preserves the first character and domain name while obscuring the rest of the username.
    """
    if not email or not isinstance(email, str) or "@" not in email:
        return email
    
    parts = email.split("@", 1)
    username = parts[0]
    domain = parts[1]
    
    if len(username) <= 1:
        masked_user = f"{username}***"
    else:
        masked_user = f"{username[0]}***"
        
    return f"{masked_user}@{domain}"

def hash_value(value: Any, salt: str = "") -> str:
    """
    Computes a SHA-256 hash for identifiers, IP addresses, or sensitive strings.
    Returns standard 64-character lowercase hex digest.
    """
    if value is None:
        return ""
    str_val = f"{salt}{value}"
    return hashlib.sha256(str_val.encode("utf-8")).hexdigest()

def mask_ip(ip: str) -> str:
    """
    Masks IP address: 192.168.***.***
    """
    if not ip or not isinstance(ip, str):
        return ip
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***.***"
    return ip

def mask_generic(text: Any) -> str:
    """
    Generic masking: keeps first character and obscures the rest.
    """
    if text is None:
        return ""
    s = str(text)
    if len(s) <= 2:
        return "***"
    return f"{s[0]}{'*' * (len(s) - 2)}{s[-1]}"

def redact(value: Any) -> str:
    """
    Completely redacts value.
    """
    return "[REDACTED]"

def apply_privacy(value: Any, field_type: str, privacy_mode: str) -> Any:
    """
    Applies privacy filter based on policy: 'none', 'mask', 'hash', 'redact'.
    """
    if value is None:
        return None
        
    mode = str(privacy_mode).lower().strip() if privacy_mode else "none"
    if mode == "none":
        return value
    elif mode == "redact":
        return redact(value)
    elif mode == "hash":
        return hash_value(value)
    elif mode == "mask":
        if "email" in field_type.lower():
            return mask_email(str(value))
        elif "ip" in field_type.lower():
            return mask_ip(str(value))
        else:
            return mask_generic(value)
            
    return value
