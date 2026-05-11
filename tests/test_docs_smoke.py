import os

def test_pre_commit_config_exists():
    assert os.path.exists('.pre-commit-config.yaml')
    assert os.path.getsize('.pre-commit-config.yaml') > 0
