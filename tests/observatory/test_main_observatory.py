import logging
import math
import unittest

from SALPY_scheduler import scheduler_observationC

from lsst.sims.ocs.configuration import Observatory, ObservingSite
from lsst.sims.ocs.kernel import TimeHandler
from lsst.sims.ocs.observatory import MainObservatory

from tests.database import topic_helpers

class MainObservatoryTest(unittest.TestCase):

    def setUp(self):
        self.truth_slew_time = 56.45919674628731
        logging.getLogger().setLevel(logging.WARN)
        self.observatory = MainObservatory(ObservingSite())

    def observatory_configure(self):
        self.observatory.configure(Observatory())

    def observatory_variational_model_configure(self):
        self.observatory.variational_model.config.obs_var.apply_variation = True
        self.observatory.variational_model.config.obs_var.telescope_change = 80.0
        self.observatory.variational_model.config.obs_var.dome_change = 80.0
        self.observatory.start_night(2281, 3650)

    def test_object_has_no_attribute(self):
        with self.assertRaises(AttributeError):
            self.observatory.no_find

    def test_basic_information_after_creation(self):
        self.assertIsNotNone(self.observatory.log)
        self.assertIsNone(self.observatory.config)
        self.assertEqual(len(self.observatory.param_dict), 0)
        self.assertEqual(self.observatory.model.location.latitude_rad, math.radians(-30.2444))
        self.assertFalse(self.observatory.model.park_state.tracking)
        self.assertEqual(len(self.observatory.model.current_state.mountedfilters), 5)
        self.assertEqual(self.observatory.exposures_made, 0)
        self.assertIsNone(self.observatory.target_exposure_list)
        self.assertIsNone(self.observatory.observation_exposure_list)
        self.assertIsNone(self.observatory.slew_history)
        self.assertIsNone(self.observatory.slew_final_state)
        self.assertIsNone(self.observatory.slew_initial_state)
        self.assertIsNone(self.observatory.slew_activities_list)
        self.assertEqual(self.observatory.slew_activities_done, 0)
        self.assertIsNone(self.observatory.slew_maxspeeds)
        self.assertIsNone(self.observatory.variational_model)

    def test_information_after_configuration(self):
        self.observatory_configure()
        self.assertEqual(len(self.observatory.param_dict), 9)
        self.assertEqual(self.observatory.model.params.telaz_maxspeed_rad, math.radians(7.0))
        self.assertEqual(self.observatory.model.park_state.alt_rad, math.radians(86.5))
        self.assertFalse(self.observatory.model.params.rotator_followsky)
        self.assertEqual(len(self.observatory.model.params.prerequisites["telsettle"]), 2)
        self.assertIsNotNone(self.observatory.variational_model)

    def test_slew(self):
        self.observatory_configure()
        target = topic_helpers.target
        self.assertEqual(self.observatory.slew_count, 0)
        slew_time = self.observatory.slew(target)
        self.assertEqual(slew_time[0], self.truth_slew_time)
        self.assertEqual(self.observatory.slew_count, 1)
        self.assertEqual(self.observatory.slew_history.slewCount, 1)
        self.assertEqual(self.observatory.slew_history.ObsHistory_observationId, 0)
        self.assertEqual(self.observatory.slew_history.slewDistance, 3.1621331347877555)
        self.assertEqual(len(self.observatory.slew_activities_list), 9)
        self.assertEqual(self.observatory.slew_activities_done, 9)
        slew_activities_list = [x.activity for x in self.observatory.slew_activities_list]
        self.assertTrue("telopticsclosedloop" in slew_activities_list)
        self.assertEqual(self.observatory.slew_maxspeeds.domeAltSpeed, -1.75)
        self.assertEqual(self.observatory.slew_maxspeeds.telAzSpeed, -7.0)

    def test_observe(self):
        self.observatory_configure()
        target = topic_helpers.target
        observation = scheduler_observationC()
        # Make it so initial timestamp is 0
        time_handler = TimeHandler("1970-01-01")
        slew_info, exposures = self.observatory.observe(time_handler, target, observation)
        self.assertEqual(observation.observationId, 1)
        self.assertEqual(observation.exposure_times[1], 15.0)
        self.assertAlmostEqual(observation.observation_start_time, self.truth_slew_time, delta=1e-4)
        self.assertEqual(len(slew_info), 5)
        self.assertIsNotNone(slew_info["slew_history"])
        self.assertIsNotNone(slew_info["slew_final_state"])
        self.assertIsNotNone(slew_info["slew_initial_state"])
        self.assertIsNotNone(slew_info["slew_activities"])
        self.assertIsNotNone(slew_info["slew_maxspeeds"])
        self.assertEqual(self.observatory.exposures_made, 2)
        self.assertEqual(len(exposures), 2)
        self.assertEqual(len(exposures["target_exposures"]), 2)
        self.assertEqual(len(exposures["observation_exposures"]), 2)

    def test_visit_time(self):
        self.observatory_configure()
        target = topic_helpers.target
        # Make it so initial timestamp is 0
        time_handler = TimeHandler("1970-01-01")
        visit_time = self.observatory.calculate_visit_time(target, time_handler)
        self.assertEqual(visit_time[0], 34.0)

    def test_get_slew_state(self):
        self.observatory_configure()
        current_state = self.observatory.model.current_state
        ss = self.observatory.get_slew_state(current_state)
        self.assertEqual(ss.slewStateId, 0)
        self.assertEqual(ss.telAlt, 86.5)
        self.assertEqual(ss.domeAlt, 90.0)
        self.assertEqual(ss.filter, 'z')

    def test_get_slew_activites(self):
        self.observatory_configure()
        self.observatory.get_slew_activities()
        # No slew performed
        self.assertEquals(len(self.observatory.slew_activities_list), 0)

    def test_start_night(self):
        self.observatory_configure()
        self.observatory_variational_model_configure()
        self.assertAlmostEqual(math.degrees(self.observatory.model.params.telaz_maxspeed_rad), 3.5,
                               delta=1.0e-3)

    def test_slew_with_variational_model(self):
        self.observatory_configure()
        self.observatory_variational_model_configure()
        target = topic_helpers.target
        slew_time = self.observatory.slew(target)
        self.assertAlmostEqual(slew_time[0], 89.91106077358576, delta=1.0e-3)

    def test_swap_filter(self):
        self.observatory_configure()
        current_mounted_filters = ['g', 'r', 'i', 'z', 'y']
        current_unmounted_filters = ['u']
        self.assertListEqual(self.observatory.current_state.mountedfilters, current_mounted_filters)
        self.assertListEqual(self.observatory.current_state.unmountedfilters, current_unmounted_filters)
        swapped_mounted_filters = ['g', 'r', 'i', 'z', 'u']
        swapped_unmounted_filters = ['y']
        self.observatory.swap_filter('y')
        self.assertListEqual(self.observatory.current_state.mountedfilters, swapped_mounted_filters)
        self.assertListEqual(self.observatory.current_state.unmountedfilters, swapped_unmounted_filters)
