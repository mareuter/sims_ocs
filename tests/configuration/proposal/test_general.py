import math
import unittest

from lsst.sims.ocs.configuration.proposal import General
from SALPY_scheduler import scheduler_generalPropConfigC

from tests.configuration.proposal.basic_proposal1 import BasicProposal1
from tests.configuration.proposal.basic_proposal2 import BasicProposal2

class GeneralTest(unittest.TestCase):

    def setUp(self):
        self.ad = General()

    def test_basic_information_after_creation(self):
        self.assertIsNone(self.ad.name)
        self.assertIsNotNone(self.ad.sky_region)
        self.assertIsNotNone(self.ad.sky_exclusion)
        self.assertIsNotNone(self.ad.sky_nightly_bounds)
        self.assertIsNotNone(self.ad.sky_constraints)
        self.assertIsNone(self.ad.filters)
        self.assertIsNotNone(self.ad.scheduling)

    def test_default_set_topic(self):
        in_topic = scheduler_generalPropConfigC()
        out_topic = self.ad.set_topic(in_topic)
        self.assertEqual(out_topic.name, "None")

    def test_specific_set_topic(self):
        ad = BasicProposal1()
        in_topic = scheduler_generalPropConfigC()
        self.assertTrue(hasattr(in_topic, "max_airmass"))
        out_topic = ad.set_topic(in_topic)
        self.assertEqual(out_topic.name, "BasicProposal1")
        self.assertEqual(out_topic.max_airmass, 2.5)
        self.assertEqual(out_topic.num_region_selections, 2)
        self.assertEqual(out_topic.region_types.split(',')[1], "RA")
        self.assertTrue(math.isnan(out_topic.region_bounds[1]))
        self.assertEqual(len(out_topic.region_combiners.split(',')), 1)
        self.assertEqual(out_topic.num_exclusion_selections, 1)
        self.assertEqual(out_topic.exclusion_types.split(',')[0], "GP")
        self.assertEqual(out_topic.exclusion_bounds[0], 90.0)
        self.assertEqual(out_topic.num_filters, 6)
        self.assertEqual(len(out_topic.filter_names.split(',')), 6)

    def test_another_specific_set_topic(self):
        ad = BasicProposal2()
        in_topic = scheduler_generalPropConfigC()
        out_topic = ad.set_topic(in_topic)
        self.assertEqual(out_topic.name, "BasicProposal2")
        self.assertEqual(out_topic.num_region_selections, 2)
        self.assertEqual(out_topic.num_exclusion_selections, 0)
        self.assertEqual(out_topic.num_filters, 3)
