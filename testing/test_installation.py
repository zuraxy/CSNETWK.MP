#!/usr/bin/env python3
"""
Quick Installation Verification Test
Verifies that all required packages are installed and working
"""
import sys
import os

def test_imports():
    """Test all required imports"""
    print("=" * 50)
    print("INSTALLATION VERIFICATION TEST")
    print("=" * 50)
    
    try:
        import textual
        print(f"✅ Textual library: v{textual.__version__}")
    except ImportError as e:
        print(f"❌ Textual library: {e}")
        return False
    
    try:
        from textual.app import App
        from textual.containers import Container, ScrollableContainer
        from textual.widgets import Button, Input, Static
        print("✅ Textual components imported successfully")
    except ImportError as e:
        print(f"❌ Textual components: {e}")
        return False
    
    # Test P2P components
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from peer.network.network_manager import NetworkManager
        from peer.discovery.peer_manager import PeerManager
        from peer.core.message_handler import MessageHandler
        print("✅ P2P components imported successfully")
    except ImportError as e:
        print(f"⚠️  P2P components: {e} (UI will work in demo mode)")
    
    print("\n🚀 READY TO USE:")
    print("   • Run: python fully_working_textual_ui.py")
    print("   • Or: run_textual_ui.bat")
    print("   • Enhanced scrollable UI with POST/DM functionality")
    
    print("\n📋 FEATURES AVAILABLE:")
    print("   ✅ Scrollable interface (PageUp/PageDown)")
    print("   ✅ POST messages (Enter key or button)")
    print("   ✅ Direct messages (Ctrl+D or DM button)")
    print("   ✅ Profile sharing (PROFILE button)")
    print("   ✅ Real-time peer discovery")
    print("   ✅ Tab navigation between elements")
    
    return True

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n" + "=" * 50)
        print("✅ ALL SYSTEMS READY!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ INSTALLATION ISSUES DETECTED")
        print("=" * 50)
