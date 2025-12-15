"""CLI argument parsing tests."""

import sys
import unittest
from unittest.mock import patch

from cloud_cert_renewer.cli import parse_args


class TestCliArgs(unittest.TestCase):
    def test_parse_args_defaults(self):
        """Test default arguments"""
        with patch.object(sys, "argv", ["prog"]):
            args = parse_args()
            self.assertFalse(args.verbose)
            self.assertFalse(args.quiet)
            self.assertFalse(args.dry_run)

    def test_parse_args_verbose(self):
        """Test --verbose argument"""
        with patch.object(sys, "argv", ["prog", "--verbose"]):
            args = parse_args()
            self.assertTrue(args.verbose)
            self.assertFalse(args.quiet)

        with patch.object(sys, "argv", ["prog", "-v"]):
            args = parse_args()
            self.assertTrue(args.verbose)

    def test_parse_args_quiet(self):
        """Test --quiet argument"""
        with patch.object(sys, "argv", ["prog", "--quiet"]):
            args = parse_args()
            self.assertTrue(args.quiet)
            self.assertFalse(args.verbose)

        with patch.object(sys, "argv", ["prog", "-q"]):
            args = parse_args()
            self.assertTrue(args.quiet)

    def test_parse_args_dry_run(self):
        """Test --dry-run argument"""
        with patch.object(sys, "argv", ["prog", "--dry-run"]):
            args = parse_args()
            self.assertTrue(args.dry_run)

    def test_version(self):
        """Test --version argument"""
        with patch.object(sys, "argv", ["prog", "--version"]):
            with self.assertRaises(SystemExit):
                parse_args()
