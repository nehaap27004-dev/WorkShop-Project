import contextvars
import re

# Context storage per request thread/coroutine
_audit_context = contextvars.ContextVar('audit_context', default={})


def set_audit_context(context_dict):
    """Sets current request's audit context."""
    return _audit_context.set(context_dict)


def get_audit_context():
    """Retrieves current request's audit context dict."""
    return _audit_context.get()


def extract_client_ip(request):
    """
    Extracts the client IP address from the request.
    Handles reverse proxies, load balancers, and direct connections.
    """
    if not request:
        return None

    # Check X-Forwarded-For header
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # The first IP address is the original client
        ip = x_forwarded_for.split(',')[0].strip()
        if ip:
            return ip

    # Check X-Real-IP header
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip.strip()

    # Fallback to REMOTE_ADDR
    remote_addr = request.META.get('REMOTE_ADDR')
    if remote_addr:
        return remote_addr.strip()

    return '127.0.0.1'


def parse_device_info(user_agent_str):
    """
    Parses browser name/version, OS, and device type from User-Agent header.
    Lightweight, fast, and robust regex-based parser without external C dependencies.
    """
    ua = (user_agent_str or "").strip()
    if not ua:
        return {
            'device_type': 'Unknown',
            'browser': 'Unknown',
            'os': 'Unknown',
            'user_agent': '',
        }

    # 1. Device Type
    device_type = "Desktop"
    if re.search(r'iPad|Tablet|PlayBook|Silk', ua, re.I):
        device_type = "Tablet"
    elif re.search(r'Mobile|Android|iPhone|iPod|BlackBerry|IEMobile|Opera Mini', ua, re.I):
        device_type = "Mobile"
    elif re.search(r'bot|crawler|spider|slurp|curl|wget|python-requests', ua, re.I):
        device_type = "Bot"

    # 2. Operating System
    os_name = "Unknown OS"
    if "Windows NT 10.0" in ua:
        os_name = "Windows 10/11"
    elif "Windows NT 6.3" in ua:
        os_name = "Windows 8.1"
    elif "Windows NT 6.1" in ua:
        os_name = "Windows 7"
    elif "Windows" in ua:
        os_name = "Windows"
    elif "iPhone" in ua or "iPad" in ua or "iPod" in ua:
        match = re.search(r'OS (\d+[_.]\d+)', ua)
        os_name = f"iOS {match.group(1).replace('_', '.')}" if match else "iOS"
    elif "Macintosh" in ua or "Mac OS X" in ua:
        match = re.search(r'Mac OS X (\d+[_.]\d+)', ua)
        os_name = f"macOS {match.group(1).replace('_', '.')}" if match else "macOS"
    elif "Android" in ua:
        match = re.search(r'Android (\d+(\.\d+)?)', ua)
        os_name = f"Android {match.group(1)}" if match else "Android"
    elif "Linux" in ua:
        os_name = "Linux"

    # 3. Browser
    browser_name = "Unknown Browser"
    if "Edg/" in ua:
        match = re.search(r'Edg/(\d+)', ua)
        browser_name = f"Edge {match.group(1)}" if match else "Edge"
    elif "Chrome/" in ua and "Chromium/" not in ua:
        match = re.search(r'Chrome/(\d+)', ua)
        browser_name = f"Chrome {match.group(1)}" if match else "Chrome"
    elif "Firefox/" in ua:
        match = re.search(r'Firefox/(\d+)', ua)
        browser_name = f"Firefox {match.group(1)}" if match else "Firefox"
    elif "Safari/" in ua and "Chrome/" not in ua:
        match = re.search(r'Version/(\d+)', ua)
        browser_name = f"Safari {match.group(1)}" if match else "Safari"
    elif "MSIE" in ua or "Trident/" in ua:
        browser_name = "Internet Explorer"

    return {
        'device_type': device_type,
        'browser': browser_name,
        'os': os_name,
        'user_agent': ua[:1000],
    }
