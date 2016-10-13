from __future__ import division
from datetime import datetime
import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from lsst.sims.ocs.configuration.sim_config import SimulationConfig
from lsst.sims.ocs.kernel.simulator import Simulator
import SALPY_scheduler

from tests.database.topic_helpers import exposure_coll1, exposure_coll2, exposure_coll3, exposure_coll4
from tests.database.topic_helpers import slew_activity_coll
from tests.helpers import CONFIG_AREA_DIST_PROPS, CONFIG_COMM_PUT_CALLS

class SimulatorTest(unittest.TestCase):

    def setUp(self):
        self.time_tolerance = 1e-6
        self.starting_timestamp = 1640995200.0

        patcher1 = mock.patch("lsst.sims.ocs.sal.sal_manager.SalManager.set_publish_topic")
        self.addCleanup(patcher1.stop)
        self.mock_salmanager_pub_topic = patcher1.start()
        patcher2 = mock.patch("lsst.sims.ocs.sal.sal_manager.SalManager.set_subscribe_topic")
        self.addCleanup(patcher2.stop)
        self.mock_salmanager_sub_topic = patcher2.start()
        patcher3 = mock.patch("lsst.sims.ocs.database.socs_db.SocsDatabase", spec=True)
        self.addCleanup(patcher3.stop)
        self.mock_socs_db = patcher3.start()
        patcher4 = mock.patch("lsst.sims.ocs.kernel.sequencer.AstronomicalSkyModel", spec=True)
        self.addCleanup(patcher4.stop)
        self.mock_astro_sky = patcher4.start()

        import collections

        self.options = collections.namedtuple("options", ["frac_duration", "no_scheduler"])
        self.options.frac_duration = 0.5
        self.options.no_scheduler = True

        self.configuration = SimulationConfig()
        self.configuration.load_proposals()

        self.sim = Simulator(self.options, self.configuration, self.mock_socs_db)

    def update_timestamp(self, timestamp):
        self.sim.time_handler.current_dt = datetime.utcfromtimestamp(timestamp)

    def topic_get(self, *args):
        topic = getattr(SALPY_scheduler, "scheduler_{}C".format(args[0]))
        return topic()

    def test_basic_information_after_creation(self):
        self.assertEqual(self.sim.duration, 183.0)
        self.assertEqual(self.sim.time_handler.initial_timestamp, self.starting_timestamp)
        self.assertIsNotNone(self.sim.obs_site_info)

    def test_fraction_overwrite(self):
        self.sim.fractional_duration = 1 / 365
        self.assertEqual(self.sim.duration, 1.0)

    def test_no_override_from_options(self):
        self.options.frac_duration = -1
        sim = Simulator(self.options, self.configuration, self.mock_socs_db)
        self.assertEquals(sim.duration, 365.0)

    @mock.patch("lsst.sims.ocs.kernel.sequencer.Sequencer.initialize")
    def test_initialization(self, mock_sequencer_init):
        self.mock_socs_db.session_id = 1001
        self.sim.initialize()
        self.assertEqual(self.mock_salmanager_pub_topic.call_count, 3 + CONFIG_COMM_PUT_CALLS)
        self.assertEqual(self.mock_salmanager_sub_topic.call_count, 4)
        self.assertEqual(mock_sequencer_init.call_count, 1)

    @mock.patch("lsst.sims.ocs.sal.sal_manager.SalManager.finalize")
    def test_finalization(self, mock_salmanager_final):
        self.sim.finalize()
        self.assertEqual(mock_salmanager_final.call_count, 1)

    def short_run(self, wait_for_sched):
        self.mock_salmanager_pub_topic.side_effect = self.topic_get
        self.mock_salmanager_sub_topic.side_effect = self.topic_get
        self.mock_socs_db.session_id = 1001
        mock_dateprofile = mock.MagicMock(mjd=59280.1)
        mas = self.mock_astro_sky.return_value
        mas.date_profile = mock_dateprofile
        mas.get_sky_brightness.return_value = {'u': [16.0], 'g': [17.0], 'r': [18.0],
                                               'i': [19.0], 'z': [20.0], 'y': [21.0]}
        mas.get_target_information.return_value = {'airmass': [1.1], 'alts': [0.5], 'azs': [0.5]}
        mas.get_moon_sun_info.return_value = {'moonRA': 30.0, 'moonDec': 10.0, 'moonAlt': -2.0,
                                              'moonAz': 135.0, 'moonPhase': 0.3, 'moonDist': 80.0,
                                              'sunRA': 310.0, 'sunDec': 5.0, 'sunAlt': -24.0, 'sunAz': 285.0,
                                              'solarElong': 150.0}

        # Setup for 1 night and 9 visits
        self.num_nights = 1
        self.num_visits = 9
        # Timestamp, cloud, seeing, observatory state and observation per visit
        # Timestamp per day
        self.put_calls = 5 * self.num_visits + self.num_nights
        self.config_comm_put_calls = 1
        self.put_calls += CONFIG_COMM_PUT_CALLS
        self.put_calls += CONFIG_AREA_DIST_PROPS
        self.sim.fractional_duration = 1 / 365
        self.sim.wait_for_scheduler = wait_for_sched
        self.mock_astro_sky.return_value.get_night_boundaries.return_value = \
            (self.starting_timestamp, self.starting_timestamp + 360.0)
        self.sim.seq.observatory_model.slew = mock.Mock(return_value=((6.0, "seconds")))
        self.sim.seq.observatory_model.calculate_visit_time = mock.Mock(return_value=((34.0, "seconds")))
        self.sim.seq.observatory_model.target_exposure_list = [exposure_coll1, exposure_coll2]
        self.sim.seq.observatory_model.observation_exposure_list = [exposure_coll3, exposure_coll4]
        self.sim.seq.observatory_model.slew_activities_list = [slew_activity_coll]
        self.sim.dh.write_downtime_to_db = mock.Mock()
        self.sim.cloud_model.write_to_db = mock.Mock()
        self.sim.seeing_model.write_to_db = mock.Mock()

        self.assertEqual(self.sim.duration, 1.0)

    @mock.patch("lsst.sims.ocs.sal.sal_manager.SalManager.put")
    def xtest_run_no_scheduler(self, mock_salmanager_put):
        self.short_run(False)

        self.sim.initialize()
        self.sim.run()

        self.assertEqual(mock_salmanager_put.call_count, self.put_calls)
        self.assertEqual(self.sim.seq.targets_received, self.num_visits)
        self.assertEqual(self.sim.seq.observations_made, self.num_visits)

    @mock.patch("SALPY_scheduler.SAL_scheduler")
    @mock.patch("lsst.sims.ocs.sal.sal_manager.SalManager.put")
    def test_run_with_scheduler(self, mock_salmanager_put, mock_salscheduler):
        self.short_run(True)
        get_calls = 1 * self.num_visits

        self.sim.initialize()
        # Need to make Scheduler wait break conditions work.
        mock_ss = mock_salscheduler()
        # Fields
        mock_ss.getNextSample_field = mock.MagicMock(return_value=0)
        self.sim.field.ID = -1
        # Targets
        mock_ss.getNextSample_target = mock.MagicMock(return_value=0)
        self.sim.target.num_exposures = 2
        self.sim.target.filter = 'r'
        # Filter Swap
        mock_ss.getNextSample_filterSwap = mock.MagicMock(return_value=0)
        # Interested Proposal
        mock_ss.getNextSample_interestedProposal = mock.MagicMock(return_value=0)
        self.sim.interested_proposal.observationId = 10

        def filter_swap_side_effect(*args):
            topic = self.topic_get(*args)
            if isinstance(topic, SALPY_scheduler.scheduler_filterSwapC):
                topic.filter_to_unmount = 'z'
            return topic

        self.sim.sal.get_topic = mock.MagicMock(side_effect=filter_swap_side_effect)

        # TargetHistory, ObsHistory, SlewHistory, SlewActivity, SlewInitialState, SlewFinalState
        # 2 * TargetExposures, 2 * ObsExposures, ProposalHistory
        DATABASE_APPEND_DATA_CALLS = 11

        self.sim.run()

        self.assertEqual(mock_salmanager_put.call_count, self.put_calls)
        self.assertEqual(mock_ss.getNextSample_field.call_count, 2)
        self.assertEqual(mock_ss.getNextSample_target.call_count, get_calls)
        self.assertEqual(mock_ss.getNextSample_filterSwap.call_count, 1)
        self.assertEqual(self.sim.seq.targets_received, self.num_visits)
        self.assertEqual(self.sim.seq.observations_made, self.num_visits)
        self.assertEqual(self.mock_socs_db.clear_data.call_count, self.num_nights)
        self.assertEqual(self.mock_socs_db.append_data.call_count,
                         self.num_visits * DATABASE_APPEND_DATA_CALLS)
        self.assertEqual(self.mock_socs_db.write.call_count, self.num_nights)

    @mock.patch("SALPY_scheduler.SAL_scheduler")
    @mock.patch("lsst.sims.ocs.sal.sal_manager.SalManager.put")
    def test_run_with_scheduler_and_filter_swap(self, mock_salmanager_put, mock_salscheduler):
        self.short_run(True)

        self.sim.initialize()
        # Need to make Scheduler wait break conditions work.
        mock_ss = mock_salscheduler()
        # Fields
        mock_ss.getNextSample_field = mock.MagicMock(return_value=0)
        self.sim.field.ID = -1
        # Targets
        mock_ss.getNextSample_target = mock.MagicMock(return_value=0)
        self.sim.target.num_exposures = 2
        self.sim.target.filter = 'r'
        # Filter Swap
        mock_ss.getNextSample_filterSwap = mock.MagicMock(return_value=0)
        # Interested Proposal
        mock_ss.getNextSample_interestedProposal = mock.MagicMock(return_value=0)
        self.sim.interested_proposal.observationId = 10

        def filter_swap_side_effect(*args):
            topic = self.topic_get(*args)
            if isinstance(topic, SALPY_scheduler.scheduler_filterSwapC):
                topic.need_swap = True
                topic.filter_to_unmount = 'z'
            return topic

        self.sim.sal.get_topic = mock.MagicMock(side_effect=filter_swap_side_effect)

        self.sim.seq.start_day = mock.MagicMock(return_value=None)

        self.sim.run()

        self.assertTrue(mock_ss.getNextSample_filterSwap.called)
        self.assertTrue(self.sim.seq.start_day.called)

    @mock.patch("SALPY_scheduler.SAL_scheduler")
    @mock.patch("lsst.sims.ocs.sal.sal_manager.SalManager.put")
    def test_run_with_scheduler_and_downtime(self, mock_salmanager_put, mock_salscheduler):
        self.short_run(True)

        self.sim.initialize()
        # Need to make Scheduler wait break conditions work.
        mock_ss = mock_salscheduler()
        # Fields
        mock_ss.getNextSample_field = mock.MagicMock(return_value=0)
        self.sim.field.ID = -1
        # Targets
        mock_ss.getNextSample_target = mock.MagicMock(return_value=0)
        self.sim.target.num_exposures = 2
        self.sim.target.filter = 'r'
        # Filter swap
        mock_ss.getNextSample_filterSwap = mock.MagicMock(return_value=0)
        # Interested Proposal
        mock_ss.getNextSample_interestedProposal = mock.MagicMock(return_value=0)
        self.sim.interested_proposal.observationId = 10

        def filter_swap_side_effect(*args):
            topic = self.topic_get(*args)
            if isinstance(topic, SALPY_scheduler.scheduler_filterSwapC):
                topic.need_swap = False
                topic.filter_to_unmount = 'z'
            return topic

        self.sim.sal.get_topic = mock.MagicMock(side_effect=filter_swap_side_effect)

        self.sim.dh.get_downtime = mock.Mock(return_value=1)
        self.sim.seq.start_day = mock.MagicMock(return_value=None)

        self.sim.run()

        self.assertEqual(self.sim.dh.get_downtime.call_count, self.num_nights)
        self.assertEqual(mock_ss.getNextSample_target.call_count, 0)
        self.assertEqual(self.sim.seq.start_day.call_count, 1)
