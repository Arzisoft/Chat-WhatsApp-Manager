#!/usr/bin/env python3
"""Verify all imports work correctly - run on startup"""

import sys
from pathlib import Path

def check_import(module_name, package_name=None):
    try:
        __import__(module_name)
        print(f"[OK] {module_name}")
        return True
    except ImportError as e:
        print(f"[FAIL] {module_name}: {e}")
        return False

def main():
    print("=" * 60)
    print("CHATCHAOS IMPORT VERIFICATION")
    print("=" * 60)

    results = []

    print("\nCore Modules:")
    results.append(check_import("core.database"))
    results.append(check_import("core.parser"))
    results.append(check_import("core.analyzer"))
    results.append(check_import("core.transcriber"))
    results.append(check_import("core.error_handler"))
    results.append(check_import("core.rate_limiter"))
    results.append(check_import("core.system_health"))
    results.append(check_import("core.models"))

    print("\nUI Components:")
    results.append(check_import("components.brand"))
    results.append(check_import("components.colors"))
    results.append(check_import("components.theme"))
    results.append(check_import("components.ui_components"))
    results.append(check_import("components.modern_ui"))

    print("\nExternal Dependencies:")
    results.append(check_import("streamlit"))
    results.append(check_import("dotenv"))
    results.append(check_import("sqlite3"))
    results.append(check_import("json"))
    results.append(check_import("requests"))

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Import Verification: {passed}/{total} passed")

    if passed == total:
        print("Status: ALL IMPORTS OK")
        print("=" * 60)
        return 0
    else:
        print("Status: SOME IMPORTS FAILED")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
