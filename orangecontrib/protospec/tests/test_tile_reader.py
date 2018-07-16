import os.path
import unittest

import Orange
from Orange.data.io import FileFormat

from orangecontrib.spectroscopy import get_sample_datasets_dir
from orangecontrib.spectroscopy.tests.test_preprocess import PREPROCESSORS_INDEPENDENT_SAMPLES

AGILENT_TILE = "agilent/5_mosaic_agg1024.dmt"

class TestTileReaders(unittest.TestCase):

    def test_tile_load(self):
        Orange.data.Table(AGILENT_TILE)

    def test_tile_reader(self):
        # Can be removed once the get_reader interface is no logner required.
        path = os.path.join(get_sample_datasets_dir(), AGILENT_TILE)
        reader = FileFormat.get_reader(path)
        reader.read()


class TestTilePreprocessors(unittest.TestCase):

    def test_single_preproc(self):
        # TODO problematic interface design: should be able to use Orange.data.Table directly
        path = os.path.join(get_sample_datasets_dir(), AGILENT_TILE)
        reader = FileFormat.get_reader(path)
        for p in PREPROCESSORS_INDEPENDENT_SAMPLES:
            reader.set_preprocessor(p)
            try:
                reader.read()
            except AssertionError as e:
                print("Domain error:", p, e)
            else:
                print("OK", p)