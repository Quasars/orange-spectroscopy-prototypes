import unittest

import numpy as np
from Orange.data import (
    Domain,
    DiscreteVariable,
    ContinuousVariable,
    StringVariable,
    Table,
)

from Orange.tests import named_file

from orangecontrib.protospec.data import HDF5Reader


class TestHDF5(unittest.TestCase):
    # From Orange.data.test.test_io.TestWriters
    def setUp(self):
        self.domain = Domain(
            [
                DiscreteVariable("a", values=tuple("xyz")),
                ContinuousVariable("b", number_of_decimals=3),
            ],
            ContinuousVariable("c", number_of_decimals=0),
            [StringVariable("d")],
        )
        self.data = Table.from_numpy(
            self.domain,
            np.array([[1, 0.5], [2, np.nan], [np.nan, 1.0625]]),
            np.array([3, 1, 7]),
            np.array([["foo", "bar", np.nan]], dtype=object).T,
        )

    def test_roundtrip_hdf5(self):
        with named_file('', suffix='.hdf5') as fn:
            HDF5Reader.write(fn, self.data)
            data = HDF5Reader(fn).read()
            np.testing.assert_equal(data.X, self.data.X)
            np.testing.assert_equal(data.Y, self.data.Y)
            np.testing.assert_equal(data.metas[:2], self.data.metas[:2])
            self.assertEqual(data.metas[2, 0], "")
            np.testing.assert_equal(data.domain, self.data.domain)
