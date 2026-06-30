from __future__ import annotations
import os
import sys


def _try_extract() -> str | None:
    import browser_cookie3
    for name, loader in [
        ("brave", browser_cookie3.brave),
        ("chrome", browser_cookie3.chrome),
        ("edge", browser_cookie3.edge),
        ("firefox", browser_cookie3.firefox),
    ]:
        try:
            cj = loader(domain_name="screener.in")
            for cookie in cj:
                if cookie.name == "sessionid":
                    print(f"Found session in {name}")
                    return cookie.value
        except PermissionError:
            continue
        except Exception:
            continue
    return None


def get_session_id(auto_mode: bool = False) -> str | None:
    try:
        session = _try_extract()
        if session:
            return session
    except ImportError:
        pass

    if auto_mode:
        return None

    if os.name == "nt":
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("Session extraction needs administrator access.")
            print("Rel launching with admin privileges...")
            import subprocess
            subprocess.run(
                ["powershell", "-Command",
                 f"Start-Process '{sys.argv[0]}' -ArgumentList 'login,--auto' -Verb RunAs -Wait"],
                capture_output=True
            )
            return _try_extract()

    print("Could not find screener.in session in any browser.")
    print("Make sure you're logged into screener.in in your browser.")
    return None
