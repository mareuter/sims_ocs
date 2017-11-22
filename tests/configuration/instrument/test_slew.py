import unittest

from lsst.sims.ocs.configuration.instrument import Slew
import SALPY_scheduler

class SlewTest(unittest.TestCase):

    def setUp(self):
        self.slew = Slew()
        self.slew_conf = SALPY_scheduler.scheduler_slewConfigC()

    def test_basic_information_from_creation(self):
        self.assertEqual(len(self.slew.prereq_telopticsclosedloop), 7)
        self.assertEqual(len(self.slew.prereq_readout), 0)

    def test_string_setting(self):
        self.slew_conf.prereq_telsettle = self.slew.get_string_rep("prereq_telsettle")
        self.assertEqual(self.slew_conf.prereq_telsettle, "telalt,telaz")
