# VS Code Extension Compatibility

## VS Code 1.99.3 Compatibility

### Pylance Extension Compatibility

**Confirmed Compatible Version:** VS Code 1.99.3 is fully compatible with Pylance 2025.6.2.

**Recommended Installation Methods:**

1. **Automatic Installation (Recommended)**
   - When opening the project, Cursor/VS Code will automatically prompt to install recommended extensions
   - Click "Install All" to install all recommended extensions, including Pylance

2. **Manual Installation**
   - Open Extensions panel: `Cmd+Shift+X` (Mac) or `Ctrl+Shift+X` (Windows/Linux)
   - Search for `ms-python.vscode-pylance`
   - Click "Install" to install the latest version
   - If you encounter compatibility issues, you can install a specific version:
     - Click the gear icon next to the extension
     - Select "Install Another Version..."
     - Choose version `2025.6.2`

**Compatibility Reference:**

- VS Code 1.99.3: Pylance 2025.6.2 (confirmed compatible)

### Current Recommended Extensions

**Required Extensions:**

1. `charliermarsh.ruff` - Python formatting and linting
2. `ms-python.python` - Python language support
3. `ms-python.vscode-pylance` - Advanced Python language server (type checking, code completion, etc.)

### Verification

After installing extensions, verify they are working correctly:

1. **Check Python Support**
   - Open any Python file
   - You should see syntax highlighting and basic code completion

2. **Check Ruff**
   - Modify code (add extra spaces)
   - Save the file (`Cmd+S`)
   - It should auto-format

3. **Check Pylance**
   - Open a Python file
   - Hover over variables, you should see type information
   - Should provide intelligent code completion and type checking

### Related Links

- [VS Code Updates](https://code.visualstudio.com/updates)
- [Pylance Extension Page](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
- [Python Extension Page](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
