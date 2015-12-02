import unittest

from lsst.sims.ocs.configuration.observatory import Observatory

class ObservatoryTest(unittest.TestCase):

    def setUp(self):
        self.observatory = Observatory()

    def test_basic_information_from_creation(self):
        self.assertIsNotNone(self.observatory.telescope)
        self.assertIsNotNone(self.observatory.dome)
        self.assertIsNotNone(self.observatory.rotator)
        self.assertIsNotNone(self.observatory.camera)
        self.assertIsNotNone(self.observatory.slew)
