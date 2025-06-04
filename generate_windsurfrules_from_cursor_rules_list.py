#!/usr/bin/env python3
"""
Interactively scans a local codebase to detect languages/frameworks, then fetches 
corresponding rules from the awesome-cursor-rules-mdc GitHub repo, converts them
to Windsurf format, and writes them to the .windsurf/rules/ directory.

- Uses GitHub API (requires GITHUB_TOKEN environment variable).
- Prompts user for each detected technology before fetching/converting.
- Outputs individual .md files to .windsurf/rules/.

Requirements:
    - Python 3.8+
    - requests, PyYAML (install with: pip install requests pyyaml)
"""
import os
import sys
import requests
import yaml
import re
import shutil
from pathlib import Path
from collections import defaultdict
import argparse

# --- Constants from fetch_and_convert_cursor_rules_to_windsurf.py --- 
REPO_OWNER = "sanjeed5"
REPO_NAME = "awesome-cursor-rules-mdc"
RULES_PATH = "rules-mdc" # Subdirectory in the repo where .mdc rules are
TARGET_DIR = Path(".windsurf/rules")
GITHUB_API = "https://api.github.com"

import json

PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))

# Load detection maps from codeMaps directory
CODEMAPS_DIR = PROJECT_ROOT / "codeMaps"
with open(CODEMAPS_DIR / "language_detection.json") as f:
    LANGUAGE_DETECTION = json.load(f)
with open(CODEMAPS_DIR / "framework_detection.json") as f:
    FRAMEWORK_DETECTION = json.load(f)
with open(CODEMAPS_DIR / "tool_detection.json") as f:
    TOOL_DETECTION = json.load(f)

# --- Helper Functions (adapted from both scripts) ---

def preprocess_frontmatter(lines):
    new_lines = []
    for line in lines:
        m = re.match(r'^(\s*globs\s*:\s*)([^\[\"\n][^\n]*)$', line)
        if m:
            prefix, value = m.groups()
            value = value.strip()
            if not value.startswith('[') and not (value.startswith('"') or value.startswith("'")):
                value = f'"{value}"'
            new_lines.append(f'{prefix}{value}\n')
        else:
            new_lines.append(line)
    return new_lines

def parse_frontmatter_and_content(text):
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].strip().startswith('---'):
        return { }, ''.join(lines)
    fm_end = None
    for i in range(1, len(lines)):
        if lines[i].strip().startswith('---'):
            fm_end = i
            break
    if fm_end is None:
        return { }, ''.join(lines)
    frontmatter_lines = preprocess_frontmatter(lines[1:fm_end])
    frontmatter = yaml.safe_load(''.join(frontmatter_lines)) or { }
    content = ''.join(lines[fm_end+1:])
    return frontmatter, content

def convert_frontmatter_for_windsurf(fm):
    new_fm = {}
    if fm.get('alwaysApply', False) is True or fm.get('alwaysApply', 'false') == 'true':
        new_fm['trigger'] = 'always_on'
        if 'globs' in fm:
            new_fm['globs'] = fm['globs']
    elif 'globs' in fm:
        new_fm['trigger'] = 'glob'
        new_fm['globs'] = fm['globs']
    if 'description' in fm:
        new_fm['description'] = fm['description']
    return new_fm

def update_references_in_content(content):
    return content.replace('Cursor', 'Windsurf')

def fetch_github_file_list(token, owner, repo, path):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return {item['name'].replace('.mdc', ''): item for item in r.json() if item['type'] == 'file' and item['name'].endswith('.mdc')}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching file list from GitHub: {e}")
        return None

def fetch_github_file_content(token, file_info):
    url = file_info['download_url']
    headers = {"Authorization": f"token {token}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching file content for {file_info['name']}: {e}")
        return None

# --- Codebase Scanning Logic (from original generate_windsurfrules.py) ---
def find_codebase_dir(start_dir):
    # Simplified: Assumes script is run from project root or one level above.
    # For more robust detection, expand this or use a fixed relative path.
    if any(os.path.exists(os.path.join(start_dir, f)) for f in ['package.json', 'pom.xml', 'pyproject.toml', 'go.mod', 'Cargo.toml']):
        return start_dir
    # Check one level down for common src/ or app/ dirs
    for subdir in ['src', 'app', '.']:
        potential_dir = os.path.join(start_dir, subdir)
        if os.path.isdir(potential_dir) and any(os.path.exists(os.path.join(potential_dir, f)) for f in ['package.json', 'pom.xml', 'pyproject.toml', 'go.mod', 'Cargo.toml']):
             return potential_dir
    return start_dir # Default to current if no better found

def scan_for_languages_and_tech(base_dir):
    detected_langs = set()
    detected_frameworks = set()
    detected_tools = set()
    known_extensions = set()
    # Collect all extensions from language detection JSON
    for lang, data in LANGUAGE_DETECTION.items():
        known_extensions.update(data.get("extensions", []))
    # Also add extensions from legacy EXT_LANG_MAP for backward compatibility
    legacy_ext_map = {
        '.py': 'python', '.js': 'javascript', '.jsx': 'javascript', '.ts': 'typescript', '.tsx': 'typescript',
        '.java': 'java', '.rb': 'ruby', '.go': 'go', '.php': 'php', '.rs': 'rust', '.cpp': 'cpp', '.c': 'c',
        '.cs': 'csharp', '.swift': 'swift', '.kt': 'kotlin', '.scala': 'scala', '.sh': 'shell',
    }
    known_extensions.update(legacy_ext_map.keys())
    # Build reverse maps for quick lookup
    ext_to_lang = {ext: lang for lang, data in LANGUAGE_DETECTION.items() for ext in data.get("extensions", [])}
    ext_to_lang.update(legacy_ext_map)
    # Prepare filename and build file lookup
    special_filenames = set()
    for lang, data in LANGUAGE_DETECTION.items():
        special_filenames.update(data.get("filenames", []))
        special_filenames.update(data.get("build_files", []))
    for fw, data in FRAMEWORK_DETECTION.items():
        special_filenames.update(data.get("build_files", []))
    for tool, data in TOOL_DETECTION.items():
        special_filenames.update(data.get("build_files", []))
        special_filenames.update(data.get("filenames", []))
    # Scan files
    for root, _, files in os.walk(base_dir):
        # Avoid scanning .git, node_modules, venv, __pycache__, etc.
        if any(skip in root for skip in ['.git', 'node_modules', 'venv', '__pycache__']):
            continue
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in known_extensions:
                lang = ext_to_lang.get(ext)
                if lang:
                    detected_langs.add(lang)
            # Check for special filenames/build files
            if fname in special_filenames:
                # Try to match to a language, framework, or tool
                for lang, data in LANGUAGE_DETECTION.items():
                    if fname in data.get("filenames", []) or fname in data.get("build_files", []):
                        detected_langs.add(lang)
                for fw, data in FRAMEWORK_DETECTION.items():
                    if fname in data.get("build_files", []):
                        detected_frameworks.add(fw)
                for tool, data in TOOL_DETECTION.items():
                    if fname in data.get("build_files", []) or fname in data.get("filenames", []):
                        detected_tools.add(tool)
            # Check for shebangs and modelines in scripts
            try:
                file_path = os.path.join(root, fname)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [f.readline() for _ in range(5)] # Read first 5 lines
                    f.seek(0, os.SEEK_END)
                    if f.tell() > 0:
                        f.seek(max(f.tell() - 200, 0))
                        tail_lines = f.readlines()[-5:]
                    else:
                        tail_lines = []
                # Shebang detection
                for line in lines:
                    if line.startswith('#!'):
                        for lang, data in LANGUAGE_DETECTION.items():
                            if any(shebang in line for shebang in data.get("shebangs", [])):
                                detected_langs.add(lang)
                # Modeline detection
                for line in lines + tail_lines:
                    for lang, data in LANGUAGE_DETECTION.items():
                        if any(modeline in line for modeline in data.get("modelines", [])):
                            detected_langs.add(lang)
                # Framework marker detection
                for fw, data in FRAMEWORK_DETECTION.items():
                    if any(marker in l for l in lines for marker in data.get("markers", [])):
                        detected_frameworks.add(fw)
                # Tool marker detection
                for tool, data in TOOL_DETECTION.items():
                    if any(marker in l for l in lines for marker in data.get("markers", [])):
                        detected_tools.add(tool)
            except Exception:
                continue
    # Also check for dependency markers in build files (e.g., spring-boot in pom.xml)
    # This can be expanded for more robust detection.
    return list(detected_langs | detected_frameworks | detected_tools)

# Replace calls to scan_for_languages with scan_for_languages_and_tech in main()

# --- Main Application Logic ---
def main():
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        sys.exit(1)

    print("Fetching list of available rules from GitHub...")
    available_rules_map = fetch_github_file_list(github_token, REPO_OWNER, REPO_NAME, RULES_PATH)
    if available_rules_map is None:
        sys.exit(1)
    print(f"Found {len(available_rules_map)} rules available in the GitHub repository.")

    codebase_dir_to_scan = find_codebase_dir(PROJECT_ROOT) 
    print(f"Scanning codebase at: {codebase_dir_to_scan}")
    
    detected_tech = scan_for_languages_and_tech(codebase_dir_to_scan)
    # Add more sophisticated framework detection here if needed, 
    # then map to rule names (e.g. 'react' might map to 'React.mdc')
    # For now, detected_tech contains language names like 'python', 'javascript', plus frameworks/tools

    if not detected_tech:
        print("No supported languages/frameworks/tools found in the codebase.")
        return

    print(f"\nDetected technologies in your project: {', '.join(sorted(detected_tech))}")

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    accepted_rules_count = 0
    written_files_summary = []

    for tech_key in sorted(detected_tech):
        # Try to find a direct match (e.g., 'python' for 'python.mdc')
        # More sophisticated mapping might be needed if tech_key doesn't match filename stem
        rule_file_info = available_rules_map.get(tech_key) 
        # Try common variations if direct match fails (e.g. Node.js -> nodejs)
        if not rule_file_info:
            rule_file_info = available_rules_map.get(tech_key.lower().replace('.',''))
        if not rule_file_info:
            rule_file_info = available_rules_map.get(tech_key.capitalize())
        
        if rule_file_info:
            print(f"\n--- {tech_key.capitalize()} --- ")
            resp = input(f"A rule for '{tech_key}' is available. Add it to .windsurf/rules/{tech_key}.md? [y/N]: ").strip().lower()
            if resp == 'y':
                print(f"Fetching and converting rule for {tech_key}...")
                mdc_content = fetch_github_file_content(github_token, rule_file_info)
                if mdc_content:
                    fm, content = parse_frontmatter_and_content(mdc_content)
                    new_fm = convert_frontmatter_for_windsurf(fm)
                    new_content = update_references_in_content(content)
                    
                    # Preview (customize as needed)
                    print("\n--- Rule Preview (Converted for Windsurf) ---")
                    print(yaml.dump({'frontmatter': new_fm}, sort_keys=False, allow_unicode=True).strip())
                    print("---------------------------------------------")
                    # print(content[:300] + "..." if len(content) > 300 else content)
                    # print("---------------------------------------------")
                    
                    confirm_add = input("Add this rule? [y/N]: ").strip().lower()
                    if confirm_add == 'y':
                        windsurf_rule_content = '---\n' + yaml.safe_dump(new_fm, sort_keys=False).strip() + '\n---\n' + new_content
                        output_path = TARGET_DIR / f"{tech_key}.md"
                        try:
                            with open(output_path, 'w', encoding='utf-8') as f:
                                f.write(windsurf_rule_content)
                            print(f"Successfully wrote rule to: {output_path}")
                            written_files_summary.append(str(output_path))
                            accepted_rules_count += 1
                        except IOError as e:
                            print(f"Error writing file {output_path}: {e}")
                    else:
                        print(f"Skipped rule for {tech_key}.")
                else:
                    print(f"Could not fetch content for {tech_key} rule.")
            else:
                print(f"Skipped rule for {tech_key}.")
        # If no rule exists in GitHub for this tech_key, skip output entirely (no redundant message)

    print("\n--- Summary ---")
    if accepted_rules_count > 0:
        print(f"Successfully wrote {accepted_rules_count} rules to {TARGET_DIR}:")
        for f_path in written_files_summary:
            print(f"  - {f_path}")
    else:
        print("No rules were added.")

if __name__ == "__main__":
    main()
