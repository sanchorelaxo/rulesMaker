#!/usr/bin/env python3
"""
Sync and convert Cursor rules from the awesome-cursor-rules-mdc GitHub repo to the latest Windsurf format (.md) for project-only scope.
- Fetches all .mdc files from the GitHub repo sanjeed5/awesome-cursor-rules-mdc/rules-mdc
- Converts frontmatter and references as per latest Windsurf requirements
- Outputs to .windsurf/rules/<rule>.md in the current working directory
- Requires GITHUB_TOKEN environment variable for authentication

Requirements:
    - Python 3.8+
    - requests, PyYAML (install with: pip install requests pyyaml)
"""
import os
import sys
import requests
import yaml
import re
from pathlib import Path

REPO_OWNER = "sanjeed5"
REPO_NAME = "awesome-cursor-rules-mdc"
RULES_PATH = "rules-mdc"
TARGET_DIR = Path(".windsurf/rules")
GITHUB_API = "https://api.github.com"

# Helper: preprocess frontmatter to quote unquoted glob patterns
def preprocess_frontmatter(lines):
    new_lines = []
    for line in lines:
        # Match: globs: *.rs or globs: [*.rs, *.foo] (unquoted)
        m = re.match(r'^(\s*globs\s*:\s*)([^\[\"\
][^\n]*)$', line)
        if m:
            prefix, value = m.groups()
            # Quote value if not already quoted or a list
            value = value.strip()
            if not value.startswith('[') and not (value.startswith('"') or value.startswith("'")):
                value = f'"{value}"'
            new_lines.append(f'{prefix}{value}\n')
        else:
            new_lines.append(line)
    return new_lines

# Helper: parse YAML frontmatter from Markdown
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
    # Preprocess frontmatter for YAML compatibility
    frontmatter_lines = preprocess_frontmatter(lines[1:fm_end])
    frontmatter = yaml.safe_load(''.join(frontmatter_lines)) or { }
    content = ''.join(lines[fm_end+1:])
    return frontmatter, content

# Helper: convert Cursor frontmatter to Windsurf frontmatter
def convert_frontmatter(fm):
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

def update_references(content):
    content = content.replace('Cursor', 'Windsurf')
    return content

def fetch_github_file_list(token, owner, repo, path):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

def fetch_github_file_content(token, file_info):
    url = file_info['download_url']
    headers = {"Authorization": f"token {token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.text

def main():
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        sys.exit(1)

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    file_list = fetch_github_file_list(token, REPO_OWNER, REPO_NAME, RULES_PATH)
    written_files = set()

    for file_info in file_list:
        if not file_info['name'].endswith('.mdc'):
            continue
        text = fetch_github_file_content(token, file_info)
        fm, content = parse_frontmatter_and_content(text)
        new_fm = convert_frontmatter(fm)
        new_content = update_references(content)
        out = '---\n' + yaml.safe_dump(new_fm, sort_keys=False).strip() + '\n---\n' + new_content
        out_name = file_info['name'].replace('.mdc', '.md')
        out_path = TARGET_DIR / out_name
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(out)
        written_files.add(str(out_path.resolve()))
        print(f"Converted: {file_info['name']} -> {out_path}")

    # Optionally, delete orphaned files in target dir
    for f in TARGET_DIR.glob('*.md'):
        if str(f.resolve()) not in written_files:
            print(f"Deleting orphaned file: {f}")
            f.unlink()

if __name__ == '__main__':
    main()
