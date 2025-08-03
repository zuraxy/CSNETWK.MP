#!/usr/bin/env python3
"""
Test suite for modular discovery implementation
Tests individual modules and integration
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from peer.discovery import ConnectivityTester, NetworkScanner, DiscoveryManager


class TestConnectivityTester(unittest.TestCase):
    """Test cases for ConnectivityTester module"""
    
    def setUp(self):
        self.tester = ConnectivityTester()
    
    def test_initialization(self):
        """Test proper initialization"""
        self.assertIsInstance(self.tester, ConnectivityTester)
        self.assertEqual(self.tester.results, {})
    
    @patch('socket.socket')
    def test_loopback_success(self, mock_socket):
        """Test successful loopback test"""
        # Mock successful loopback
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        mock_sock.getsockname.return_value = ('127.0.0.1', 12345)
        mock_sock.recvfrom.return_value = (b"UDP_TEST", ('127.0.0.1', 12345))
        
        result = self.tester._test_loopback()
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(result['port'], 12345)
    
    def test_get_results(self):
        """Test results retrieval"""
        self.tester.results = {'test': 'data'}
        self.assertEqual(self.tester.get_last_results(), {'test': 'data'})


class TestNetworkScanner(unittest.TestCase):
    """Test cases for NetworkScanner module"""
    
    def setUp(self):
        self.scanner = NetworkScanner()
    
    def test_initialization(self):
        """Test proper initialization"""
        self.assertIsInstance(self.scanner, NetworkScanner)
        self.assertEqual(self.scanner.discovery_port, 50999)
        self.assertEqual(self.scanner.scan_timeout, 5.0)
        self.assertEqual(self.scanner.discovered_peers, [])
    
    def test_peer_count(self):
        """Test peer count functionality"""
        self.assertEqual(self.scanner.get_peer_count(), 0)
        
        # Add mock peers
        self.scanner.discovered_peers = [
            {'user_id': 'test1@192.168.1.1', 'ip': '192.168.1.1'},
            {'user_id': 'test2@192.168.1.2', 'ip': '192.168.1.2'}
        ]
        self.assertEqual(self.scanner.get_peer_count(), 2)
    
    def test_clear_peers(self):
        """Test clearing discovered peers"""
        self.scanner.discovered_peers = ['peer1', 'peer2']
        self.scanner.clear_discovered_peers()
        self.assertEqual(self.scanner.discovered_peers, [])
    
    def test_timeout_configuration(self):
        """Test timeout configuration"""
        self.scanner.set_scan_timeout(10.0)
        self.assertEqual(self.scanner.scan_timeout, 10.0)
    
    def test_scan_summary(self):
        """Test scan summary generation"""
        summary = self.scanner.get_scan_summary()
        self.assertIn('peer_count', summary)
        self.assertIn('peers', summary)
        self.assertIn('scan_timeout', summary)
        self.assertIn('discovery_port', summary)


class TestDiscoveryManager(unittest.TestCase):
    """Test cases for DiscoveryManager module"""
    
    def setUp(self):
        self.manager = DiscoveryManager()
    
    def test_initialization(self):
        """Test proper initialization"""
        self.assertIsInstance(self.manager, DiscoveryManager)
        self.assertIsInstance(self.manager.connectivity_tester, ConnectivityTester)
        self.assertIsInstance(self.manager.network_scanner, NetworkScanner)
    
    def test_configuration(self):
        """Test configuration methods"""
        self.manager.configure_scan_timeout(15.0)
        self.assertEqual(self.manager.network_scanner.scan_timeout, 15.0)
    
    def test_export_formats(self):
        """Test different export formats"""
        # Set up mock results
        self.manager.discovery_results = {
            'peers': [],
            'network_ready': True,
            'discovery_time': 1234567890
        }
        
        # Test dict format
        dict_export = self.manager.export_results('dict')
        self.assertIsInstance(dict_export, dict)
        
        # Test summary format
        summary_export = self.manager.export_results('summary')
        self.assertIn('network_ready', summary_export)
        self.assertIn('peer_count', summary_export)
        
        # Test invalid format
        with self.assertRaises(ValueError):
            self.manager.export_results('invalid_format')


class TestIntegration(unittest.TestCase):
    """Integration tests for the discovery system"""
    
    def setUp(self):
        self.manager = DiscoveryManager()
    
    @patch.object(ConnectivityTester, 'test_all')
    @patch.object(NetworkScanner, 'scan_for_peers')
    def test_full_discovery_workflow(self, mock_scan, mock_connectivity):
        """Test complete discovery workflow"""
        # Mock connectivity test results
        mock_connectivity.return_value = {
            'loopback': {'status': 'OK'},
            'broadcast': {'status': 'OK'}
        }
        
        # Mock peer scan results
        mock_scan.return_value = [
            {'user_id': 'test@192.168.1.1', 'display_name': 'test@192.168.1.1:8000'}
        ]
        
        # Mock network ready status
        self.manager.connectivity_tester.is_network_ready = MagicMock(return_value=True)
        
        # Run discovery
        results = self.manager.run_full_discovery(verbose=False)
        
        # Verify results structure
        self.assertIn('connectivity', results)
        self.assertIn('peers', results)
        self.assertIn('scan_summary', results)
        self.assertIn('discovery_time', results)
        self.assertEqual(len(results['peers']), 1)


def run_discovery_tests():
    """Run all discovery module tests"""
    print("=" * 60)
    print("MODULAR DISCOVERY IMPLEMENTATION TESTS")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestConnectivityTester))
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkScanner))
    suite.addTests(loader.loadTestsFromTestCase(TestDiscoveryManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\\n✅ All tests passed! Modular discovery implementation is working correctly.")
    else:
        print("\\n❌ Some tests failed. Check the output above for details.")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_discovery_tests()
    exit(0 if success else 1)
