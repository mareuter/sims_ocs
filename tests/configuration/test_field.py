from builtins import str
import math
import unittest

from lsst.sims.ocs.configuration.field import Field

from tests.database.topic_helpers import field_topic

class FieldTest(unittest.TestCase):

    def setUp(self):
        self.field = Field(1, 0.5, 30.0, -30.0, -45.0, 45.0, 60.0, -60.0)

    def test_basic_information_after_creation_from_constructor(self):
        self.assertEqual(self.field.fid, 1)
        self.assertEqual(self.field.fov, 0.5)
        self.assertEqual(self.field.ra, 30.0)
        self.assertEqual(self.field.dec_rad, math.radians(-30.0))
        self.assertEqual(self.field.gl_rad, math.radians(-45.0))
        self.assertEqual(self.field.gb, 45.0)
        self.assertEqual(self.field.el, 60.0)
        self.assertEqual(self.field.eb_rad, math.radians(-60.0))

    def test_basic_information_after_creation_from_topic(self):
        ft = Field.from_topic(field_topic)
        self.assertEqual(ft.fid, 1)
        self.assertEqual(ft.fov_rad, math.radians(0.5))
        self.assertEqual(ft.ra_rad, math.radians(30.0))
        self.assertEqual(ft.dec, -30.0)
        self.assertEqual(ft.gl, -45.0)
        self.assertEqual(ft.gb_rad, math.radians(45.0))
        self.assertEqual(ft.el_rad, math.radians(60.0))
        self.assertEqual(ft.eb, -60.0)

    def test_string_representation(self):
        truth_message = "Field ID: 1, FOV: 0.500 deg, RA: 30.000 deg, DEC: -30.000 deg, GalL: -45.000 deg, "\
                        "GalB: 45.000 deg, EclL: 60.000 deg, EclB: -60.000 deg"

        field_str = str(self.field).strip()
        self.assertEqual(len(field_str), len(truth_message))
        self.assertEqual(field_str, truth_message)

    def test_repr_representation(self):
        truth_repr = "Field(1, 0.5, 30.0, -30.0, -45.0, 45.0, 60.0, -60.0)"
        repr_str = repr(self.field)
        self.assertEqual(repr_str, truth_repr)
