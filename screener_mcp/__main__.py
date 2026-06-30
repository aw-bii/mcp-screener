from __future__ import annotations
import os
import sys
from .server import run as run_server


def cmd_login():
    auto = "--auto" in sys.argv
    from .login import get_session_id
    session = get_session_id(auto_mode=auto)
    if not session:
        sys.exit(1)
    env_path = os.path.join(os.getcwd(), ".env")
    with open(env_path, "w") as f:
        f.write(f"SCREENER_SESSION_ID={session}\n")
    print(f"Session saved to {env_path}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        cmd_login()
    else:
        run_server()


if __name__ == "__main__":
    main()
