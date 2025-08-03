#!/usr/bin/env python3
"""
Test runner for all CSNETWK.MP test scripts
Run this script to execute all tests in the testing directory
"""
import sys
import os
import subprocess
import time

def run_test(script_name, description):
    """Run a test script and report results"""
    print(f"\n{'='*60}")
    print(f"RUNNING: {description}")
    print(f"Script: {script_name}")
    print(f"{'='*60}")
    
    try:
        # Run the script and capture output
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, 
                              text=True, 
                              timeout=30)
        
        if result.returncode == 0:
            print("[PASS] TEST PASSED")
            print(result.stdout)
        else:
            print("[FAIL] TEST FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("[FAIL] TEST TIMEOUT")
        return False
    except Exception as e:
        print(f"[FAIL] TEST ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("CSNETWK.MP Test Suite")
    print("="*60)
    print("Running all test scripts from the testing directory...")
    
    # Get the directory where this script is located (should be testing/)
    test_dir = os.path.dirname(os.path.abspath(__file__))
    original_dir = os.getcwd()
    
    try:
        # Change to test directory
        os.chdir(test_dir)
        print(f"Test directory: {test_dir}")
        
        # List of tests to run
        tests = [
            ("test_imports.py", "Protocol Import and Basic Functionality Test"),
            ("test_p2p_setup.py", "P2P Implementation Setup and Verification Test"),
            ("test_dm.py", "Direct Message (DM) Functionality Test"),
            ("test_profile.py", "Profile Message Functionality Test"),
            ("test_p2p.py", "Peer-to-Peer (P2P) Architecture Test"),
            ("test_verbose_mode.py", "Verbose Mode Display Simulation"),
            ("demo_verbose_modes.py", "Verbose vs Non-Verbose Mode Comparison"),
            ("create_test_avatar.py", "Test Avatar Image Creation Utility"),
            ("test_modular_components.py", "Modular P2P Components Test"),
            ("test_modular_discovery.py", "Modular Discovery Implementation Test")
        ]
        
        # Run each test
        passed = 0
        total = len(tests)
        
        for script, description in tests:
            if os.path.exists(script):
                success = run_test(script, description)
                if success:
                    passed += 1
                time.sleep(1)  # Small delay between tests
            else:
                print(f"\n[FAIL] MISSING: {script} not found")
        
        # Summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Tests Run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n[SUCCESS] ALL TESTS PASSED!")
            print("The CSNETWK.MP implementation is working correctly!")
        else:
            print(f"\n[WARNING] {total - passed} test(s) failed. Please check the output above.")
        
        print(f"\n[INFO] Next Steps:")
        print("1. Start peer(s): python ../run_peer.py (in multiple terminals)")
        print("2. Test peer discovery: python ../peer/discover_peers_modular.py")
        print("3. Test modular discovery: python ../peer/discover_peers_modular.py")
        print("4. Compare implementations: python compare_implementations.py")
        print("5. Compare discovery implementations: python compare_discovery_implementations.py")
        print("6. Test the full P2P application with multiple peers")
        print("7. Try both verbose and non-verbose modes")
        print("8. No server needed - fully peer-to-peer architecture!")
        
    finally:
        # Change back to original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    main()
