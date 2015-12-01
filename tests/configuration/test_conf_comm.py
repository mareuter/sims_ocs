import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from lsst.sims.ocs.configuration.conf_comm import ConfigurationCommunicator
from lsst.sims.ocs.configuration.sim_config import SimulationConfig
from lsst.sims.ocs.sal.sal_manager import SalManager

class ConfigurationCommunicatorTest(unittest.TestCase):

    def setUp(self):
        self.conf_comm = ConfigurationCommunicator()
        self.sal = SalManager()
        self.sal.initialize()
        self.config = SimulationConfig()

    def test_initial_creation(self):
        self.assertIsNone(self.conf_comm.sal)
        self.assertIsNone(self.conf_comm.config)

    def test_initialize(self):
        self.conf_comm.initialize(self.sal, self.config)
        self.assertIsNotNone(self.conf_comm.sal)
        self.assertIsNotNone(self.conf_comm.config)

    @mock.patch("lsst.sims.ocs.sal.sal_manager.SalManager.put")
    @mock.patch("SALPY_scheduler.SAL_scheduler.salTelemetryPub")
    def test_run(self, mock_sal_telemetry_pub, mock_salmanager_put):
        expected_calls = 1
        self.conf_comm.initialize(self.sal, self.config)
        self.conf_comm.run()
        self.assertEqual(mock_sal_telemetry_pub.call_count, expected_calls)
        self.assertEqual(mock_salmanager_put.call_count, expected_calls)