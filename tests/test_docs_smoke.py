import os

def test_readme_exists():
    assert os.path.exists('README.md') and os.path.getsize('README.md') > 0