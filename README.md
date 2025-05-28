# Windsurf Rules Generator

This script (`generate_windsurfrules.py`) scans your codebase, detects frameworks/languages, and fetches coding rules from cursor.directory. The output is a `.windsurfrules` (or `.cursorrules`) file tailored to your stack.

## How It Works

### 1. Argument Parsing
- Accepts `--iscursor` flag. If set, outputs to `.cursorrules`; otherwise, to `.windsurfrules`.

### 2. Project Root Discovery
- Determines the root directory and rules directory based on the script's location.

### 3. Codebase Scanning
- Recursively walks the codebase to collect all files and directories.

### 4. Key Detection
For each key in the KEYS list, the script checks:
- **File extension mapping:** If a file extension matches a language (e.g., `.py` → Python).
- **File and directory names:** If a filename or directory contains the key.
- **Dependency files:**
  - For JavaScript/TypeScript: Scans `package.json` dependencies.
  - For Python: Scans `requirements.txt` and `pyproject.toml`.
  - For Ruby: Scans `Gemfile`.
  - For Rust: Scans `Cargo.toml`.
  - For PHP: Scans `composer.json`.
  - **For Java:**
    - Detects `.java` files, `pom.xml` (Maven), and `build.gradle`/`build.gradle.kts` (Gradle).
    - Parses `pom.xml` for dependencies and matches against KEYS.
    - Scans Gradle build files for KEYS matches in dependencies.

### 5. Rule Fetching and User Interaction
- For each detected key, fetches rules from cursor.directory.
- Prompts the user to accept or reject each rule.
- Only rules inside `<code class="text-sm block pr-3">...</code>` HTML elements or downloadable `.txt` files are considered.

### 6. Output
- Accepted rules are written to `.windsurfrules` or `.cursorrules` in the project root.
- Summarizes which keys/rules were accepted or rejected.

## Example Usage

```sh
python3 generate_windsurfrules.py
```

To generate `.cursorrules`:

```sh
python3 generate_windsurfrules.py --iscursor
```

## Customization
- **IMPORTANT:** The `KEYS` list in the script must match the available sections in [cursor.directory/rules/](https://cursor.directory/rules/). If you add or remove keys, ensure they correspond to actual rule sections.
- Edit the `KEYS` list in the script to adjust what is detected.
- Extend the extension-to-language mapping as needed.
- Modify dependency scanning logic to support other ecosystems.

## License
MIT
