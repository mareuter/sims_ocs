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
        self.assertEqual(args.frac_duration, -1)
        self.assertEqual(args.verbose, 0)
        self.assertFalse(args.no_scheduler)
        self.assertIsNone(args.config)
        self.assertFalse(args.save_config)
        self.assertEqual(args.config_save_path, '$PWD')
        self.assertFalse(args.track_session)
        self.assertIsNone(args.tracking_db)
        self.assertEqual(args.startup_comment, "No comment was entered.")
        self.assertEqual(args.session_code, "science")
        self.assertIsNone(args.sqlite_save_dir)
        self.assertIsNone(args.sqlite_session_save_dir)
        self.assertIsNone(args.session_id_start)
        self.assertFalse(args.profile)
        self.assertEqual(args.scheduler_timeout, 60)

    def test_fractional_duration_flag(self):
        args = self.parser.parse_args(["--frac-duration", "0.0027397260273972603"])
        self.assertEquals(args.frac_duration, 1.0 / 365.0)

    def test_verbose_flag_count(self):
        args = self.parser.parse_args(["-v", "-v", "-v"])
        self.assertEqual(args.verbose, 3)

    def test_no_sched_flag(self):
        args = self.parser.parse_args(["--no-sched"])
        self.assertTrue(args.no_scheduler)

    def test_config_as_file_list(self):
        args = self.parser.parse_args(["--config", "conf1.py", "conf2.py", "conf3.py"])
        self.assertEqual(len(args.config), 3)

    def test_config_files_with_other_option(self):
        args = self.parser.parse_args(["--config", "conf1.py", "conf2.py", "-v"])
        self.assertEqual(len(args.config), 2)

    def test_save_config_flag(self):
        args = self.parser.parse_args(["--save-config"])
        self.assertTrue(args.save_config)

    def test_track_session(self):
        args = self.parser.parse_args(["-t"])
        self.assertTrue(args.track_session)

    def test_tracking_db(self):
        tracking_url = "http://mytracking.db"
        args = self.parser.parse_args(["--tracking-db", tracking_url])
        self.assertEqual(args.tracking_db, tracking_url)

    def test_startup_comment(self):
        session_comment = "This is a cool run!"
        args = self.parser.parse_args(["--startup-comment", session_comment])
        self.assertEqual(args.startup_comment, [session_comment])

    def test_startup_comment_with_other_options(self):
        session_comment = "This is a cool run!"
        args = self.parser.parse_args(["--frac-duration", "1.0", "--startup-comment", session_comment, "-v"])
        self.assertEqual(args.startup_comment, [session_comment])

    def test_session_code(self):
        session_code = "code_dev"
        args = self.parser.parse_args(["--session-code", session_code])
        self.assertEqual(args.session_code, session_code)

    def test_sqlite_save_dir(self):
        save_dir = "/path/to/save"
        args = self.parser.parse_args(["--save-dir", save_dir])
        self.assertEqual(args.sqlite_save_dir, save_dir)

    def test_session_id_start(self):
        args = self.parser.parse_args(["-s", "1100"])
        self.assertEqual(args.session_id_start, "1100")

    def test_profile(self):
        args = self.parser.parse_args(["--profile"])
        self.assertTrue(args.profile)

    def test_sqlite_session_save_dir(self):
        save_dir = "/path/to/save"
        args = self.parser.parse_args(["--session-save-dir", save_dir])
        self.assertEqual(args.sqlite_session_save_dir, save_dir)

    def test_scheduler_timeout(self):
        timeout = 180
        args = self.parser.parse_args(["--scheduler-timeout", str(timeout)])
        self.assertEqual(args.scheduler_timeout, timeout)
