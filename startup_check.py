#!/usr/bin/env python3
"""
ChatChaos Startup Health Check
Run this before starting the system to verify all components are ready
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def check_file_exists(path, description):
    if os.path.exists(path):
        print(f"  [OK] {description}")
        return True
    else:
        print(f"  [FAIL] {description} - NOT FOUND: {path}")
        return False

def check_directory_writable(path, description):
    try:
        os.makedirs(path, exist_ok=True)
        test_file = os.path.join(path, '.test_write')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(f"  [OK] {description} - writable")
        return True
    except Exception as e:
        print(f"  [FAIL] {description} - {str(e)}")
        return False

def check_module_import(module_name, description):
    try:
        __import__(module_name)
        print(f"  [OK] {description}")
        return True
    except ImportError as e:
        print(f"  [FAIL] {description} - {str(e)}")
        return False

def check_env_file():
    env_files = ['.env.txt', '.env']
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"  [OK] Environment file found: {env_file}")
            
            with open(env_file) as f:
                content = f.read()
                if 'GEMINI_API_KEY' in content:
                    api_key = None
                    for line in content.split('\n'):
                        if line.startswith('GEMINI_API_KEY'):
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                api_key = parts[1].strip()
                                if api_key and api_key != '':
                                    print(f"  [OK] GEMINI_API_KEY configured")
                                    return True
                    if not api_key:
                        print(f"  [WARN] GEMINI_API_KEY is empty")
                        return False
                else:
                    print(f"  [WARN] GEMINI_API_KEY not found in {env_file}")
                    return False
    
    print(f"  [FAIL] No .env file found")
    return False

def main():
    print("=" * 70)
    print("CHATCHAOS WHATSAPP MANAGER - STARTUP HEALTH CHECK")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 70)

    results = []

    print("\n1. DIRECTORY STRUCTURE")
    results.append(check_directory_writable('data', 'Data directory'))
    results.append(check_directory_writable('logs', 'Logs directory'))
    results.append(check_directory_writable('exports', 'Exports directory'))

    print("\n2. CONFIGURATION FILES")
    results.append(check_env_file())

    print("\n3. CORE MODULES")
    results.append(check_module_import('core.database', 'Database module'))
    results.append(check_module_import('core.parser', 'Parser module'))
    results.append(check_module_import('core.analyzer', 'Analyzer module'))
    results.append(check_module_import('core.transcriber', 'Transcriber module'))
    results.append(check_module_import('core.error_handler', 'Error handler module'))
    results.append(check_module_import('core.rate_limiter', 'Rate limiter module'))
    results.append(check_module_import('core.system_health', 'System health module'))

    print("\n4. DATABASE INITIALIZATION")
    try:
        from core.database import init_db, get_kpis
        init_db()
        kpis = get_kpis()
        print(f"  [OK] Database initialized - {kpis['total_chats']} chats in system")
        results.append(True)
    except Exception as e:
        print(f"  [FAIL] Database initialization - {str(e)}")
        results.append(False)

    print("\n5. SYSTEM HEALTH CHECKS")
    try:
        from core.system_health import SystemHealth
        api_status = SystemHealth.get_api_status()
        db_status = SystemHealth.get_database_status()
        queue_status = SystemHealth.get_queue_status()
        
        if api_status.get('healthy'):
            print(f"  [OK] Gemini API available")
        else:
            print(f"  [WARN] Gemini API unavailable - using environment key")
        results.append(True)
        
        if db_status.get('healthy'):
            print(f"  [OK] Database healthy")
            results.append(True)
        else:
            print(f"  [FAIL] Database unhealthy")
            results.append(False)
    except Exception as e:
        print(f"  [WARN] Health check failed - {str(e)}")

    print("\n6. BRIDGE CONNECTIVITY")
    try:
        import requests
        try:
            response = requests.get('http://localhost:3001/health', timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                print(f"  [OK] Bridge online (status: {status})")
                results.append(True)
            else:
                print(f"  [WARN] Bridge not ready yet (status: {response.status_code})")
                results.append(True)
        except requests.exceptions.ConnectionError:
            print(f"  [WARN] Bridge not running - start it before importing chats")
            results.append(True)
    except Exception as e:
        print(f"  [WARN] Bridge check failed - {str(e)}")
        results.append(True)

    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"STARTUP CHECK: {passed}/{total} checks passed")

    if passed == total:
        print("Status: READY TO START")
        print("=" * 70)
        return 0
    else:
        print("Status: WARNINGS/ERRORS DETECTED")
        print("Review the items marked [FAIL] and [WARN] above")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
