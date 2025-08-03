# Testing Directory

This directory contains all test scripts for the CSNETWK.MP project. All scripts have been moved here from the root directory and updated to work correctly from this location.

## Test Scripts

### Core Functionality Tests
- **`test_imports.py`** - Tests protocol import and basic encoding/decoding
- **`test_p2p_setup.py`** - Tests P2P implementation setup and verification
- **`test_dm.py`** - Tests Direct Message (DM) functionality
- **`test_profile.py`** - Tests PROFILE message functionality with avatar support
- **`test_p2p.py`** - Tests Peer-to-Peer architecture functionality

### Display and UI Tests
- **`test_verbose_mode.py`** - Simulates verbose vs non-verbose mode displays
- **`demo_verbose_modes.py`** - Interactive demo showing mode differences

### Utility Scripts
- **`create_test_avatar.py`** - Utility for creating test avatar images (placeholder)
- **`run_all_tests.py`** - Runs all tests and provides a summary report

### Legacy Test
- **`test.py`** - Original test file (pre-existing)

## How to Run Tests

### Run Individual Tests
```bash
# From the testing directory
cd testing
python test_imports.py
python test_dm.py
python test_profile.py
python test_verbose_mode.py
python demo_verbose_modes.py
python create_test_avatar.py
```

### Run All Tests at Once
```bash
# From the testing directory
cd testing
python run_all_tests.py
```

### Run from Root Directory
```bash
# From the project root
python testing/test_imports.py
python testing/test_dm.py
python testing/test_profile.py
# etc...
```

## Test Coverage

### Protocol Testing
- Message encoding/decoding (POST, DM, PROFILE)
- Field validation and preservation
- Avatar data handling (base64 encoding)
- Message size testing (UDP buffer limits)

### Feature Testing
- Direct messaging with recipient validation
- Profile creation with avatar support
- Verbose vs non-verbose display modes
- Display name storage and retrieval

### Integration Testing
- Import path validation
- Cross-module functionality
- File I/O operations (avatar creation)

## Expected Output

All tests should pass with output like:
```
Protocol import successful!
Protocol encoding/decoding test successful!
DM message format test passed!
POST message format test passed!
PROFILE message format test passed!
PROFILE message with avatar test passed!
```

## Troubleshooting

### Import Errors
If you get import errors, ensure you're running from the correct directory:
- Scripts use `sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))` to find the protocol module
- This adds the parent directory (project root) to the Python path

### File Not Found Errors
- `create_test_avatar.py` creates files in the project root directory
- Test avatar images are created as temporary files and cleaned up automatically

### Permission Errors
- Ensure you have write permissions in the project directory
- Some tests create temporary files that need to be written and deleted

## Integration with Main Application

### Running the Full Application
After tests pass, run the full application:
```bash
# From project root - Modular P2P Architecture
python run_peer.py          # Terminal 1
python run_peer.py          # Terminal 2 
python run_peer.py          # Terminal 3

# Or use the alternative modular launcher
python run_peer_modular.py  # Terminal 1
python run_peer_modular.py  # Terminal 2
```

### Testing Features
1. **POST Messages**: Test broadcasting to all peers
2. **DM Messages**: Test direct messaging between specific peers
3. **PROFILE Updates**: Test profile creation with/without avatars
4. **Verbose Modes**: Toggle between verbose and non-verbose display
5. **User Lists**: Test online peer listing functionality

## Notes

- All tests are standalone and don't require any external processes to be running
- Tests use mock data and don't create network connections
- Avatar tests use minimal PNG images for testing purposes
- File paths are automatically resolved relative to script locations
