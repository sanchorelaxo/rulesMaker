import os
import shutil
from collections import defaultdict

# Mapping of file extensions to languages
EXT_LANG_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.rb': 'ruby',
    '.go': 'go',
    '.php': 'php',
    '.rs': 'rust',
    '.cpp': 'cpp',
    '.c': 'c',
    '.cs': 'csharp',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.sh': 'shell',
}

# IMPORTANT: These must match the available sections in cursor.directory/rules/
KEYS = [
    'AL', 'API', 'Accessibility', 'Bloc', 'CSS', 'Expo', 'Function', 'Global', 'Go', 'HTML', 'IBC', 'Java', 'JavaScript',
    'Next.js', 'Node', 'Node.js', 'PHP', 'Python', 'React', 'Ruby', 'Rust', 'Security', 'Testing', 'Transformer',
    'TypeScript', 'Unity', 'Zod', 'bootstrap', 'cpp', 'ex', 'html', 'python', 'typescript'
]

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
RULES_DIR = os.path.join(PROJECT_ROOT, 'cursor.directory', 'rules')
import argparse

parser = argparse.ArgumentParser(description="Generate Windsurf or Cursor rules file.")
parser.add_argument('--iscursor', action='store_true', help='If set, output to .cursorrules instead of .windsurfrules')
args = parser.parse_args()

if args.iscursor:
    WINDSURF_RULES = os.path.join(PROJECT_ROOT, '.cursorrules')
else:
    WINDSURF_RULES = os.path.join(PROJECT_ROOT, '.windsurfrules')


def scan_codebase(base_dir):
    lang_line_counts = defaultdict(int)
    for root, _, files in os.walk(base_dir):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            lang = EXT_LANG_MAP.get(ext)
            if lang:
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        lang_line_counts[lang] += len(lines)
                except Exception as e:
                    print(f"Warning: Could not read {fpath}: {e}")
    return lang_line_counts


def get_dominant_language(lang_line_counts):
    if not lang_line_counts:
        return None
    return max(lang_line_counts.items(), key=lambda x: x[1])[0]


def fetch_ruleset(lang):
    ruleset_path = os.path.join(RULES_DIR, lang)
    if os.path.isfile(ruleset_path):
        with open(ruleset_path, 'r', encoding='utf-8') as f:
            return f.read()
    print(f"No ruleset found for language: {lang} at {ruleset_path}")
    return None


def backup_existing_rules():
    if os.path.isfile(WINDSURF_RULES):
        backup_path = WINDSURF_RULES + '_OLD'
        shutil.move(WINDSURF_RULES, backup_path)
        print(f"Existing .windsurfrules backed up to {backup_path}")


def find_codebase_dir(project_root):
    project_files = [
        'package.json', 'pom.xml', 'build.gradle', 'build.gradle.kts', 'requirements.txt',
        'pyproject.toml', 'Pipfile', 'setup.py', 'Gemfile', 'Cargo.toml', 'composer.json',
        'go.mod', 'pubspec.yaml', 'CMakeLists.txt', 'tsconfig.json', 'next.config.js',
        'openapi.yaml', 'swagger.yaml', 'security.txt', '.env', 'trivy.config', 'bandit.yaml',
        'style.css', 'globals.css', 'global.css', 'index.html', 'jest.config.js', 'axe.config.js',
        'app.json', 'build.gradle', 'build.gradle.kts'
    ]
    # Check root itself first
    for proj_file in project_files:
        if os.path.isfile(os.path.join(project_root, proj_file)):
            return project_root
    # Then check subdirectories
    for entry in os.listdir(project_root):
        full_path = os.path.join(project_root, entry)
        if os.path.isdir(full_path):
            for proj_file in project_files:
                if os.path.isfile(os.path.join(full_path, proj_file)):
                    return full_path
    # If nothing found, default to project_root
    return project_root


def read_package_json(codebase_dir):
    import json
    pkg_json_path = os.path.join(codebase_dir, 'package.json')
    if os.path.isfile(pkg_json_path):
        with open(pkg_json_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"Could not parse package.json: {e}")
    return {}

def scan_for_keys_canonical(codebase_dir, keys):
    found_keys = set()
    # Pre-scan the codebase for files, dirs, and package/dependency files
    all_files = []
    all_dirs = set()
    for root, dirs, files in os.walk(codebase_dir):
        for d in dirs:
            all_dirs.add(d.lower())
        for f in files:
            all_files.append((root, f))

    # Helper: check if any file exists with a given name (case-insensitive)
    def file_exists(filename):
        return any(f.lower() == filename.lower() for _, f in all_files)
    # Helper: check if any file endswith ext
    def file_ext_exists(ext):
        return any(f.lower().endswith(ext.lower()) for _, f in all_files)
    # Helper: check if any dir exists
    def dir_exists(dirname):
        return dirname.lower() in all_dirs
    # Helper: check if any file matches pattern
    def file_pattern_exists(pattern):
        import fnmatch
        return any(fnmatch.fnmatch(f.lower(), pattern.lower()) for _, f in all_files)
    # Helper: check if a dependency exists in a package file
    def dep_in_package_json(dep):
        pkg_json_path = os.path.join(codebase_dir, 'package.json')
        if not os.path.isfile(pkg_json_path):
            return False
        import json
        try:
            with open(pkg_json_path, 'r', encoding='utf-8') as f:
                pkg = json.load(f)
            for section in ['dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies']:
                deps = pkg.get(section, {})
                if any(dep.lower() in d.lower() for d in deps):
                    return True
        except Exception:
            pass
        return False


    for key in keys:
        k = key.lower()
        # AL
        if k == 'al':
            if file_ext_exists('.al') or file_exists('app.json'):
                found_keys.add(key)
        # API
        elif k == 'api':
            if file_exists('openapi.yaml') or file_exists('swagger.yaml') or dir_exists('api') or file_pattern_exists('api*.*'):
                found_keys.add(key)
        # Java (enhanced detection for Maven and Gradle)
        elif k == 'java':
            import xml.etree.ElementTree as ET
            java_detected = False
            # Check for .java files or canonical build files
            if file_ext_exists('.java') or file_exists('pom.xml') or file_exists('build.gradle') or file_exists('build.gradle.kts'):
                java_detected = True
            # Check Maven dependencies (pom.xml)
            pom_path = os.path.join(codebase_dir, 'pom.xml')
            if os.path.isfile(pom_path):
                try:
                    tree = ET.parse(pom_path)
                    root = tree.getroot()
                    ns = {'m': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
                    for dep in root.findall('.//m:dependency', ns) if ns else root.findall('.//dependency'):
                        groupId = dep.find('m:groupId', ns).text if ns and dep.find('m:groupId', ns) is not None else (dep.find('groupId').text if dep.find('groupId') is not None else '')
                        artifactId = dep.find('m:artifactId', ns).text if ns and dep.find('m:artifactId', ns) is not None else (dep.find('artifactId').text if dep.find('artifactId') is not None else '')
                        for k2 in keys:
                            if k2.lower() in groupId.lower() or k2.lower() in artifactId.lower():
                                java_detected = True
                                break
                except Exception as e:
                    print(f"Warning: Could not parse pom.xml for Java detection: {e}")
            # Check Gradle dependencies (build.gradle, build.gradle.kts)
            for gradle_file in ['build.gradle', 'build.gradle.kts']:
                gradle_path = os.path.join(codebase_dir, gradle_file)
                if os.path.isfile(gradle_path):
                    try:
                        with open(gradle_path, 'r', encoding='utf-8') as f:
                            gradle_content = f.read().lower()
                        for k2 in keys:
                            if k2.lower() in gradle_content:
                                java_detected = True
                                break
                    except Exception as e:
                        print(f"Warning: Could not parse {gradle_file} for Java detection: {e}")
            if java_detected:
                found_keys.add(key)
        # Accessibility
        elif k == 'accessibility':
            if file_exists('.accessibilityrc') or file_exists('axe.config.js'):
                found_keys.add(key)
        # Bloc
        elif k == 'bloc':
            if file_exists('pubspec.yaml'):
                try:
                    with open(os.path.join(codebase_dir, 'pubspec.yaml'), 'r', encoding='utf-8') as f:
                        if any('bloc' in l.lower() for l in f):
                            found_keys.add(key)
                except Exception:
                    pass
        # CSS
        elif k == 'css':
            if file_ext_exists('.css') or file_exists('style.css') or dir_exists('styles') or dep_in_package_json('css'):
                found_keys.add(key)
        # Expo
        elif k == 'expo':
            if file_exists('app.json'):
                try:
                    with open(os.path.join(codebase_dir, 'app.json'), 'r', encoding='utf-8') as f:
                        import json
                        app = json.load(f)
                        if 'expo' in app:
                            found_keys.add(key)
                except Exception:
                    pass
            elif dep_in_package_json('expo'):
                found_keys.add(key)
        # Function
        elif k == 'function':
            if dir_exists('functions') or file_pattern_exists('*.func.*'):
                found_keys.add(key)
        # Global
        elif k == 'global':
            if file_exists('globals.css') or file_exists('global.css') or dir_exists('global'):
                found_keys.add(key)
        # Go
        elif k == 'go':
            if file_exists('go.mod') or file_ext_exists('.go'):
                found_keys.add(key)
        # HTML
        elif k == 'html':
            if file_ext_exists('.html') or file_exists('index.html') or dir_exists('public'):
                found_keys.add(key)
        # IBC
        elif k == 'ibc':
            if file_exists('go.mod'):
                try:
                    with open(os.path.join(codebase_dir, 'go.mod'), 'r', encoding='utf-8') as f:
                        if any('github.com/cosmos/ibc-go' in l for l in f):
                            found_keys.add(key)
                except Exception:
                    pass

        # JavaScript
        elif k == 'javascript':
            if file_ext_exists('.js') or dep_in_package_json('javascript'):
                found_keys.add(key)
        # Next.js
        elif k == 'next.js':
            if dep_in_package_json('next') or file_exists('next.config.js'):
                found_keys.add(key)
        # Node
        elif k == 'node' or k == 'node.js':
            if file_exists('package.json') or file_ext_exists('.js') or dir_exists('node_modules'):
                found_keys.add(key)
        # PHP
        elif k == 'php':
            if file_ext_exists('.php') or file_exists('composer.json'):
                found_keys.add(key)
        # Python
        elif k == 'python':
            if file_ext_exists('.py') or file_exists('requirements.txt') or file_exists('pyproject.toml') or file_exists('Pipfile') or file_exists('setup.py'):
                found_keys.add(key)
        # React
        elif k == 'react':
            if dep_in_package_json('react') or file_ext_exists('.jsx') or file_ext_exists('.tsx'):
                found_keys.add(key)
        # Ruby
        elif k == 'ruby':
            if file_ext_exists('.rb') or file_exists('Gemfile'):
                found_keys.add(key)
        # Rust
        elif k == 'rust':
            if file_exists('Cargo.toml') or file_ext_exists('.rs'):
                found_keys.add(key)
        # Security
        elif k == 'security':
            if file_exists('security.txt') or file_exists('.env') or file_exists('trivy.config') or file_exists('bandit.yaml'):
                found_keys.add(key)
        # Testing
        elif k == 'testing':
            if dir_exists('test') or dir_exists('tests') or file_pattern_exists('test_*.py') or file_pattern_exists('*.test.js') or file_exists('jest.config.js'):
                found_keys.add(key)
        # Transformer
        elif k == 'transformer':
            if dir_exists('transformers') or file_pattern_exists('transformer.*') or dep_in_package_json('transformer'):
                found_keys.add(key)
        # TypeScript
        elif k == 'typescript':
            if file_ext_exists('.ts') or file_ext_exists('.tsx') or dep_in_package_json('typescript') or file_exists('tsconfig.json'):
                found_keys.add(key)
        # Unity
        elif k == 'unity':
            if dir_exists('assets') or dir_exists('projectsettings') or file_ext_exists('.unity'):
                found_keys.add(key)
        # Zod
        elif k == 'zod':
            if dep_in_package_json('zod'):
                found_keys.add(key)
        # bootstrap
        elif k == 'bootstrap':
            if dep_in_package_json('bootstrap') or file_exists('bootstrap.css'):
                found_keys.add(key)
        # cpp
        elif k == 'cpp':
            if file_ext_exists('.cpp') or file_ext_exists('.hpp') or file_ext_exists('.cc') or file_ext_exists('.cxx') or file_exists('CMakeLists.txt'):
                found_keys.add(key)
        # ex
        elif k == 'ex':
            if file_ext_exists('.ex') or file_ext_exists('.exs'):
                found_keys.add(key)
        # fallback: generic extension, filename, or directory match
        #else:
            #if any(k in f.lower() for _, f in all_files) or any(k in d for d in all_dirs):
                #found_keys.add(key)
    return found_keys

def fetch_rules_for_key_interactive(key):
    import requests
    from bs4 import BeautifulSoup
    url = f"https://cursor.directory/rules/{key.lower()}"
    print(f"Fetching rule(s) for {key} from {url}")
    accepted = []
    rejected = []
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Gather all .txt links
        rule_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].lower().endswith('.txt')]
        rule_blocks = []
        # Only gather <code class="text-sm block pr-3"> blocks
        for code in soup.find_all('code', class_='text-sm block pr-3'):
            if code.text.strip():
                rule_blocks.append(code.text.strip())
        # For .txt links, fetch content
        found = False
        for link in rule_links:
            rule_url = link
            if rule_url.startswith('/'):
                rule_url = f"https://cursor.directory{rule_url}"
            try:
                rule_resp = requests.get(rule_url, timeout=10)
                rule_resp.raise_for_status()
                rule_content = rule_resp.text.strip()
                preview = rule_content[:400].replace('\n', ' ')
                green_preview = f"\033[92m{preview}\033[0m"
                resp_in = input(f"Add this rule for {key} from .txt link? Preview: {green_preview}... [y/N]: ").strip().lower()
                if resp_in == 'y':
                    accepted.append(rule_content)
                    found = True
                    break
                else:
                    rejected.append(preview)
            except Exception as e:
                print(f"Failed to fetch rule file for {key}: {e}")
        # For HTML blocks (only if not already accepted)
        if not found:
            for idx, rule in enumerate(rule_blocks):
                preview = rule[:400].replace('\n', ' ')
                green_preview = f"\033[92m{preview}\033[0m"
                resp_in = input(f"Add this rule for {key} from HTML block #{idx+1}? Preview: {green_preview}... [y/N]: ").strip().lower()
                if resp_in == 'y':
                    accepted.append(rule)
                    found = True
                    break
                else:
                    rejected.append(preview)
        if not rule_links and not rule_blocks:
            print(f"No rule file or main rule content found for {key} at {url}")
    except Exception as e:
        print(f"Failed to fetch rule for {key}: {e}")
    return accepted, rejected

def write_windsurfrules(all_rules):
    with open(WINDSURF_RULES, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(all_rules))

def main():
    codebase_dir = find_codebase_dir(PROJECT_ROOT)
    if not codebase_dir:
        print("No project codebase found.")
        return
    keys = KEYS
    found_keys = scan_for_keys_canonical(codebase_dir, keys)
    if not found_keys:
        print("No matching frameworks/languages found in codebase or dependencies.")
        return
    print(f"Matched keys: {sorted(found_keys)}")

    accepted_keys = []
    rejected_keys = []
    all_rules = []
    accepted_rules_summary = {}
    rejected_rules_summary = {}
    for key in sorted(found_keys):
        resp = input(f"Add rules for {key}? [y/N]: ").strip().lower()
        if resp == 'y':
            accepted, rejected = fetch_rules_for_key_interactive(key)
            if accepted:
                for rule_content in accepted:
                    all_rules.append(f"# {key}\n{rule_content}")
                accepted_keys.append(key)
                accepted_rules_summary[key] = len(accepted)
            else:
                print(f"No rules accepted for {key}.")
                rejected_keys.append(key)
            if rejected:
                rejected_rules_summary[key] = len(rejected)
        else:
            rejected_keys.append(key)
    if not all_rules:
        print("No rules found for any accepted keys. No .windsurfrules written.")
        print(f"Accepted: {accepted_keys}")
        print(f"Rejected: {rejected_keys}")
        return
    backup_existing_rules()
    write_windsurfrules(all_rules)
    print(f".windsurfrules written for: {', '.join(accepted_keys)}.")
    print(f"Accepted: {accepted_keys} (rules per key: {accepted_rules_summary})")
    print(f"Rejected: {rejected_keys} (rejected rules per key: {rejected_rules_summary})")

if __name__ == "__main__":
    main()
