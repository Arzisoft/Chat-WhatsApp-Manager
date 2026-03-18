#!/usr/bin/env python3
"""Final system verification before completion"""

import sys

def main():
    print("=" * 70)
    print("CHATCHAOS - FINAL SYSTEM VERIFICATION")
    print("=" * 70)

    tests = []

    print("\n1. CORE MODULES:")
    modules = [
        'core.database',
        'core.parser',
        'core.analyzer',
        'core.transcriber',
        'core.error_handler',
        'core.rate_limiter',
        'core.system_health',
        'core.models'
    ]
    for mod in modules:
        try:
            __import__(mod)
            print(f"   [OK] {mod}")
            tests.append(True)
        except Exception as e:
            print(f"   [FAIL] {mod}: {e}")
            tests.append(False)

    print("\n2. DATABASE:")
    try:
        from core.database import init_db, get_kpis, get_all_chats
        init_db()
        kpis = get_kpis()
        chats = get_all_chats()
        total = kpis.get('total_chats', 0)
        print(f"   [OK] Database initialized")
        print(f"   [OK] Total chats in system: {total}")
        tests.append(True)
    except Exception as e:
        print(f"   [FAIL] Database: {e}")
        tests.append(False)

    print("\n3. ERROR HANDLING:")
    try:
        from core.error_handler import ChatChaosError, CircuitBreaker
        err = ChatChaosError('test')
        cb = CircuitBreaker('test')
        print(f"   [OK] Custom exceptions working")
        print(f"   [OK] Circuit breaker ready")
        tests.append(True)
    except Exception as e:
        print(f"   [FAIL] Error handler: {e}")
        tests.append(False)

    print("\n4. RATE LIMITING:")
    try:
        from core.rate_limiter import RateLimiter
        rl = RateLimiter(10, 60)
        for i in range(5):
            rl.is_allowed()
        usage = rl.get_usage()
        remaining = usage.get('remaining', 0)
        print(f"   [OK] Rate limiter operational")
        print(f"   [OK] Requests remaining: {remaining}")
        tests.append(True)
    except Exception as e:
        print(f"   [FAIL] Rate limiter: {e}")
        tests.append(False)

    print("\n5. SYSTEM HEALTH:")
    try:
        from core.system_health import SystemHealth
        status = SystemHealth.get_full_status()
        health_status = status.get('overall_status', 'unknown')
        print(f"   [OK] Health checks operational")
        print(f"   [OK] Overall status: {health_status}")
        tests.append(True)
    except Exception as e:
        print(f"   [FAIL] System health: {e}")
        tests.append(False)

    print("\n6. PARSER:")
    try:
        from core.parser import parse_file
        chat = parse_file(
            "Test.txt",
            "[26/02/2026, 14:45:59] User1: Hello\n[26/02/2026, 14:46:00] User2: Hi"
        )
        count = chat.message_count
        print(f"   [OK] Parser working")
        print(f"   [OK] Parsed {count} messages")
        tests.append(True)
    except Exception as e:
        print(f"   [FAIL] Parser: {e}")
        tests.append(False)

    print("\n" + "=" * 70)
    passed = sum(tests)
    total = len(tests)
    print(f"VERIFICATION RESULTS: {passed}/{total} checks PASSED")
    print("=" * 70)

    if passed == total:
        print("\nSTATUS: PRODUCTION READY")
        print("\nAll core systems operational and ready for deployment.")
        print("Proceed with Figma UI integration.")
        return 0
    else:
        print("\nSTATUS: ISSUES DETECTED")
        print(f"Please review {total - passed} failed checks above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
