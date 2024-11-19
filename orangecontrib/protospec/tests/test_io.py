import numpy as np

from Orange.data.tests.test_io import TestWriters
from Orange.tests import named_file

from orangecontrib.protospec.data import HDF5Reader


class TestHDF5(TestWriters):
    def test_roundtrip_hdf5(self):
        with named_file('', suffix='.hdf5') as fn:
            HDF5Reader.write(fn, self.data)
            data = HDF5Reader(fn).read()
            np.testing.assert_equal(data.X, self.data.X)
            np.testing.assert_equal(data.Y, self.data.Y)
            np.testing.assert_equal(data.metas[:2], self.data.metas[:2])
            self.assertEqual(data.metas[2, 0], "")
            np.testing.assert_equal(data.domain, self.data.domain)
