import os

def test_docs_exist():
    assert os.path.exists('AGENTS.md')
    assert os.path.getsize('AGENTS.md') > 0
