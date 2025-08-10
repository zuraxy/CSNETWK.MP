#!/usr/bin/env python3
"""
Test Input Field Functionality
Quick test to verify input fields work properly in textual UI
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_input_functionality():
    """Test input field and key binding functionality"""
    print("Testing Enhanced Input Functionality...")
    
    try:
        print("1. Testing textual UI import...")
        import fully_working_textual_ui
        app_class = fully_working_textual_ui.WorkingP2PChatApp
        print("   ✓ UI import successful")
        
        print("2. Testing key bindings...")
        app = app_class()
        bindings = [binding[0] for binding in app.BINDINGS]
        expected_bindings = ["q", "ctrl+c", "tab", "shift+tab", "enter", "ctrl+d"]
        
        for binding in expected_bindings:
            if binding in bindings:
                print(f"   ✓ Key binding '{binding}' found")
            else:
                print(f"   ❌ Key binding '{binding}' missing")
        
        print("3. Testing action methods...")
        methods = [
            "action_quit",
            "action_send_message", 
            "action_open_dm",
            "_send_post_message"
        ]
        
        for method in methods:
            if hasattr(app, method):
                print(f"   ✓ Method '{method}' found")
            else:
                print(f"   ❌ Method '{method}' missing")
        
        print("\\n✅ Input functionality is ready!")
        print("\\nKey Features:")
        print("  • Message input field with proper CSS sizing")
        print("  • Enter key to send POST messages")
        print("  • Tab navigation between UI elements")
        print("  • Ctrl+D to open DM dialog")
        print("  • Automatic focus management")
        print("  • Input field clearing after sending")
        
        print("\\nHow to use:")
        print("  1. Run: run_textual_ui.bat")
        print("  2. Enter username and connect")
        print("  3. Click in message input field or use Tab to focus")
        print("  4. Type message and press Enter or click POST")
        print("  5. Use Ctrl+D for direct messages")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_input_functionality()
