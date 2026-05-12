import os
import unittest

class TestDocumentation(unittest.TestCase):
    def test_readme_exists(self):
        self.assertTrue(os.path.exists('README.md'))
        self.assertTrue(os.path.getsize('README.md') > 0)
