#!/usr/bin/env python3
"""Evaluation-only setup: copy existing synthetic test fixtures outside the repository."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts' / 'tests'))
from test_atlas import AtlasContracts

fixture = AtlasContracts()
fixture.setUp()
try:
    fixture.publish_fixture()  # TEST ONLY; contains no authentic human authorization.
    target = Path(tempfile.mkdtemp(prefix='atlas-corrective-evaluation-')).resolve()
    shutil.copytree(fixture.root, target, dirs_exist_ok=True)
    shutil.copy2(ROOT / 'scripts' / 'atlas.py', target / 'scripts' / 'atlas.py')
    shutil.copy2(ROOT / '.gitignore', target / '.gitignore')
    subprocess.run(['git', '-C', str(target), 'init', '--quiet'], check=True, capture_output=True)
    subprocess.run([sys.executable, str(target / 'scripts' / 'atlas.py'), 'generate'],
                   check=True, capture_output=True)
    print(target)
finally:
    fixture.doCleanups()
