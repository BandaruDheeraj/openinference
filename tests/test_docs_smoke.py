import os

def test_docs_exist():
    assert os.path.exists('AGENTS.md') and os.path.getsize('AGENTS.md') > 0