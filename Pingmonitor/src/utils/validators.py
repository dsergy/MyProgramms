"""
Validation utilities for host names and IP addresses
"""
import re
from typing import Tuple


def is_valid_host(host: str) -> Tuple[bool, str]:
    """
    Validate host/IP format
    Returns: (is_valid, error_message)
    """
    if not host or len(host) > 255:
        return False, "Host name cannot be empty or longer than 255 characters"

    if is_ip_address(host):
        return True, ""

    if is_valid_domain(host):
        return True, ""

    return False, "Invalid host format"


def is_ip_address(ip: str) -> bool:
    """
    Validate IP address format
    Example: 192.168.1.1
    """
    try:
        # Split IP address into octets
        parts = ip.split('.')

        # Check if we have exactly 4 parts
        if len(parts) != 4:
            return False

        # Check each octet
        for part in parts:
            # Check if it's a number and in valid range
            if not part.isdigit():
                return False
            num = int(part)
            if num < 0 or num > 255:
                return False

            # Check for leading zeros
            if len(part) > 1 and part[0] == '0':
                return False

        return True
    except:
        return False


def is_valid_domain(domain: str) -> bool:
    """
    Validate domain name format
    Example: google.com, sub.domain.com
    """
    try:
        if len(domain) > 255:
            return False

        # Check for valid characters and format
        allowed = re.compile(
            r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?'
            r'(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*'
            r'\.[a-zA-Z]{2,}$'
        )

        return bool(allowed.match(domain))
    except:
        return False
