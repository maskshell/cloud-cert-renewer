# How to Install Recommended Extensions

Cursor/VS Code will automatically detect the `.vscode/extensions.json` file and prompt to install recommended extensions.

## Method 1: Automatic Prompt (Recommended)

1. **Open Project**
   - Open the project folder in Cursor
   - If extensions are not installed, a notification will appear in the bottom right corner

2. **Click Install**
   - When you see the "This workspace has extension recommendations" notification
   - Click "Install All" or "Show Recommendations"
   - Click "Install" in the popup window to install all recommended extensions

3. **Verify Installation**
   - Open Extensions panel: `Cmd+Shift+X` (Mac) or `Ctrl+Shift+X` (Windows/Linux)
   - View the list of installed extensions
   - Confirm all recommended extensions are installed

## Method 2: Manual Trigger

If the automatic prompt doesn't appear, you can trigger it manually:

1. **Open Command Palette**
   - `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)

2. **Run Command**
   - Type "Extensions: Show Recommended Extensions"
   - Select the command

3. **Install Extensions**
   - View the recommended extensions list in the popup window
   - Click the "Install" button next to each extension

## Method 3: Install Individually

If the above methods don't work, you can install them one by one:

1. **Open Extensions Panel**
   - `Cmd+Shift+X` (Mac) or `Ctrl+Shift+X` (Windows/Linux)

2. **Search and Install**
   - Search for the extension ID (e.g., `charliermarsh.ruff`)
   - Click the "Install" button

### Recommended Extensions List

- `charliermarsh.ruff` - Ruff (Python linter and formatter)
- `ms-python.python` - Python
- `ms-python.vscode-pylance` - Pylance
- `redhat.vscode-yaml` - YAML
- `eamodio.gitlens` - GitLens
- `yzhang.markdown-all-in-one` - Markdown All in One
- `davidanson.vscode-markdownlint` - Markdownlint
- `editorconfig.editorconfig` - EditorConfig

**Note:** JSON support is built into VS Code/Cursor, no additional extension is needed.

## Verification

After installation, verify that extensions are working correctly:

1. **Check Ruff**
   - Open any Python file
   - Modify code (add extra spaces)
   - Save the file (`Cmd+S`)
   - It should auto-format

2. **Check YAML**
   - Open any YAML file
   - You should see YAML syntax highlighting

3. **Check Tasks**
   - `Cmd+Shift+P` → "Tasks: Run Task"
   - You should see the project task list

## Troubleshooting

### Recommendation Prompt Not Appearing

1. **Check if File Exists**

   ```bash
   ls -la .vscode/extensions.json
   ```

2. **Reload Window**
   - `Cmd+Shift+P` → "Developer: Reload Window"

3. **Manual Trigger**
   - `Cmd+Shift+P` → "Extensions: Show Recommended Extensions"

### Extension Installation Failed

1. **Check Network Connection**
   - Ensure you can access the extension marketplace

2. **Check Cursor Version**
   - Ensure you are using the latest version of Cursor

3. **View Error Messages**
   - Check the Output panel for error details
   - `View` → `Output` → Select "Extensions"

## Next Steps

After installing extensions, please refer to `.vscode/README.md` for detailed configuration and usage instructions.
