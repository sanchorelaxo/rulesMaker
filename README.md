# Windsurf Rules Generator

This project provides a script (`generate_windsurfrules.py`) to automatically scan your codebase, identify relevant frameworks and languages, and fetch corresponding coding rules from [cursor.directory](https://cursor.directory/). The result is a consolidated `.windsurfrules` file tailored to your project's stack.

You can also use the `--iscursor` flag to generate a `.cursorrules` file instead of `.windsurfrules`.

---

## How the Codebase is Scanned

### 1. **Project Root Discovery**
- The script expects to be run in a directory containing your project(s).
- It searches for a subdirectory with a `package.json` file to identify the main codebase directory.

### 2. **Key List Loading**
- The list of possible frameworks, languages, and technologies is now hardcoded directly in the script as the `KEYS` variable.
- You can edit the `KEYS` list at the top of `generate_windsurfrules.py` to customize which technologies are detected.

### 3. **Matching Algorithm**
The script matches keys to your project using three strategies:

#### a. **Directory Name Match**
- For each directory in the codebase, if the directory name contains a key (case-insensitive), it's a match.

#### b. **File Extension and Filename Match**
- Uses a mapping of file extensions to languages/frameworks (e.g., `.py` → `Python`, `.tsx` → `TypeScript`).
- For every file:
    - If the file's extension maps to a language that matches a key (case-insensitive), it's a match.
    - If the filename contains a key (case-insensitive), it's a match.

#### c. **Dependency Match (package.json)**
- Loads the project's `package.json` (if present).
- For each dependency in `dependencies`, `devDependencies`, `peerDependencies`, and `optionalDependencies`:
    - If the dependency name contains a key (case-insensitive), it's a match.

### 4. **Result**
- All unique keys that match by any of the above methods are collected for rule fetching.

---

## Rule Fetching and User Interaction

1. **Prompting**: For each matched key, the script prompts you to confirm whether to fetch rules for that key.
2. **Rule Entry Selection**: For each key, the script fetches the corresponding page from cursor.directory and:
    - Only considers rule entries that are inside `<code class="text-sm block pr-3">...</code>` HTML elements or downloadable `.txt` files.
    - For each rule entry, shows you a preview (first 200 characters) and prompts for acceptance.
    - As soon as you accept a rule for a key, no further entries for that key are shown.
3. **.windsurfrules Generation**: All accepted rules are combined and written to `.windsurfrules` in your project root. The script also summarizes accepted and rejected keys and entries.

---

## Summary of Matching Logic

- **Case-insensitive** matching for all strategies
- **Keys** can match via directory, filename, file extension, or dependency name
- **Multiple matches** for a key are possible; user selects which rule to include
- **Only rules in `<code class="text-sm block pr-3">` or .txt files are considered valid**

---

## Example Usage

To generate a `.windsurfrules` file (default):

```sh
python3 generate_windsurfrules.py
```
- Respond to prompts to select which rules to include.
- The resulting `.windsurfrules` file will contain only the rules you accepted.

To generate a `.cursorrules` file instead, use the `--iscursor` flag:

```sh
python3 generate_windsurfrules.py --iscursor
```
- This will output to `.cursorrules` in your project root.

---

## Customization
- Add or remove keys in `keys.txt` to control what is detected.
- Extend the extension-to-language mapping in the script for additional file types.
- Modify the script to support other package managers or project structures as needed.

---

## License
MIT
