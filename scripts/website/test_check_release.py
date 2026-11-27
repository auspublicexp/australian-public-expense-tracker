"""Ensure a sitemap/release crawl cannot require a PHP file outside its root."""
from pathlib import Path
import unittest
from unittest.mock import patch

from check_release import render


class RenderPathTests(unittest.TestCase):
    def test_directory_index_resolving_outside_root_is_rejected(self):
        root = Path(__file__).resolve().parent / 'test-site'
        directory = root / 'section'
        outside = root.parent / 'other-site' / 'index.php'
        actual_is_dir, actual_resolve = Path.is_dir, Path.resolve

        def is_dir(path):
            return path == directory or actual_is_dir(path)

        def resolve(path, *args, **kwargs):
            if path == directory / 'index.php':
                return outside
            return actual_resolve(path, *args, **kwargs)

        # Emulate filesystem resolution without relying on Windows symlink privileges.
        with patch.object(Path, 'is_dir', is_dir), patch.object(Path, 'resolve', resolve), \
                patch('check_release.subprocess.run') as launch_php:
            launch_php.return_value.returncode = 0
            launch_php.return_value.stderr = ''
            launch_php.return_value.stdout = ''
            with self.assertRaisesRegex(RuntimeError, 'outside the website root'):
                render(root, '/section/', ['php'])
            launch_php.assert_not_called()


if __name__ == '__main__':
    unittest.main()
