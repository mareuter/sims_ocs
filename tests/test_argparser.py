import unittest

from lsst.sims.ocs.setup.parser import create_parser

class ArgParserTest(unittest.TestCase):

    def setUp(self):
        self.parser = create_parser()

    def test_parser_creation(self):
        self.assertIsNotNone(self.parser)

    def test_parser_help(self):
        self.assertIsNotNone(self.parser.format_help())

    def test_behavior_with_no_args(self):
        args = self.parser.parse_args([])
        self.assertEqual(args.frac_duration, 1.0 / 365.0)
        self.assertEqual(args.verbose, 0)
        self.assertEqual(args.debug, 0)
        self.assertFalse(args.no_scheduler)

    def test_verbose_flag_count(self):
        args = self.parser.parse_args(["-v", "-v", "-v"])
        self.assertEqual(args.verbose, 3)

    def test_debug_flag_count(self):
        args = self.parser.parse_args(["-d", "-d"])
        self.assertEqual(args.debug, 2)

    def test_no_sched_flag(self):
        args = self.parser.parse_args(["--no-sched"])
        self.assertTrue(args.no_scheduler)
