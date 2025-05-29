import os
import subprocess

def test_generate_windsurfrules_gradle():
    # Remove .windsurfrules if exists for a clean test
    ws_path = os.path.join(os.path.dirname(__file__), '.windsurfrules')
    if os.path.isfile(ws_path):
        os.remove(ws_path)

    # Run the script
    import sys
    result = subprocess.run(['python3', 'generate_windsurfrules.py'], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    assert result.returncode == 0, 'Script did not exit cleanly.'

    # Check .windsurfrules exists
    assert os.path.isfile(ws_path), '.windsurfrules was not created.'

    # Check for expected keys in output and file
    with open(ws_path, 'r', encoding='utf-8') as f:
        rules_content = f.read().lower()
    for key in ['java', 'react']:
        assert key in rules_content or key.replace('.', '' ) in rules_content, f"Expected key '{key}' not found in .windsurfrules."
    print('All expected keys found in .windsurfrules.')

if __name__ == '__main__':
    test_generate_windsurfrules_gradle()
