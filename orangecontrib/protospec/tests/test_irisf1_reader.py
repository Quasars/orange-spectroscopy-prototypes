import importlib.resources
import os.path
import unittest

import Orange

IRISF1_FILE_3_2_3 = "temp-testdata/ATR_neatMOP_Si-2019-01-22-16-57-03_processed_data.h5"
IRISF1_FILE_3_3_0 = (
    "temp-testdata/12_6_2019_DMAP_D2O_echem-2019-12-06-17-15-42-_processed_data.h5"
)
IRISF1_FILE_4_0_0 = "temp-testdata/empty-2020-09-09-16-29-22-_processed_data.h5"
IRISF1_FILE_4_1_4 = "temp-testdata/broke-purge-2020-09-11-14-24-04-_processed_data.h5"
IRISF1_FILE_5_0_0 = "temp-testdata/Calibr-2021-01-26-18-35-52-_processed_data.h5"
IRISF1_FILE_7_0_0 = "temp-testdata/H2O-2022-03-17-13-30-00-_processed_data.h5"
IRISF1_FILE_7_0_0_truncated = str(
    importlib.resources.files('orangecontrib.protospec.datasets')
    / "irisf1_v7_0_0_processed_data.h5"
)


class TestIRisF1Reader(unittest.TestCase):
    @unittest.skipIf(not os.path.exists(IRISF1_FILE_3_2_3), "Missing IRISF1_FILE_3_2_3")
    def test_iris_load_3_2_3(self):
        Orange.data.Table(IRISF1_FILE_3_2_3)

    @unittest.skipIf(not os.path.exists(IRISF1_FILE_3_3_0), "Missing IRISF1_FILE_3_3_0")
    def test_iris_load_3_3_0(self):
        Orange.data.Table(IRISF1_FILE_3_3_0)

    @unittest.skipIf(not os.path.exists(IRISF1_FILE_4_0_0), "Missing IRISF1_FILE_4_0_0")
    def test_iris_load_4_0_0(self):
        Orange.data.Table(IRISF1_FILE_4_0_0)

    @unittest.skipIf(not os.path.exists(IRISF1_FILE_4_1_4), "Missing IRISF1_FILE_4_1_4")
    def test_iris_load_4_1_4(self):
        Orange.data.Table(IRISF1_FILE_4_1_4)

    @unittest.skipIf(not os.path.exists(IRISF1_FILE_5_0_0), "Missing IRISF1_FILE_5_0_0")
    def test_iris_load_5_0_0(self):
        Orange.data.Table(IRISF1_FILE_5_0_0)

    @unittest.skipIf(not os.path.exists(IRISF1_FILE_7_0_0), "Missing IRISF1_FILE_7_0_0")
    def test_iris_load_7_0_0(self):
        Orange.data.Table(IRISF1_FILE_7_0_0)

    def test_iris_load_7_0_0_truncated(self):
        Orange.data.Table(IRISF1_FILE_7_0_0_truncated)
