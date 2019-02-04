import os.path
import unittest

import Orange
from Orange.data.io import FileFormat
from Orange.preprocess.preprocess import PreprocessorList
from Orange.widgets.tests.base import WidgetTest

from orangecontrib.spectroscopy import get_sample_datasets_dir
from orangecontrib.spectroscopy.tests.test_preprocess import PREPROCESSORS_INDEPENDENT_SAMPLES
from orangecontrib.spectroscopy.widgets.owpreprocess import OWPreprocess, PREPROCESSORS

from orangecontrib.protospec.widgets.owtilefile import OWTilefile

AGILENT_TILE = "agilent/5_mosaic_agg1024.dmt"

# EMSC test fails on this dataset with
# "ValueError: On entry to DLASCL parameter number 4 had an illegal value"
PREPROCESSORS_INDEPENDENT_SAMPLES_NO_EMSC = [
    p for p in PREPROCESSORS_INDEPENDENT_SAMPLES if type(p).__name__ != "EMSC"]

class TestTileReaders(unittest.TestCase):

    def test_tile_load(self):
        Orange.data.Table(AGILENT_TILE)

    def test_tile_reader(self):
        # Can be removed once the get_reader interface is no logner required.
        path = os.path.join(get_sample_datasets_dir(), AGILENT_TILE)
        reader = OWTilefile.get_tile_reader(path)
        reader.read()


class TestTilePreprocessors(unittest.TestCase):

    def test_single_preproc(self):
        # TODO problematic interface design: should be able to use Orange.data.Table directly
        path = os.path.join(get_sample_datasets_dir(), AGILENT_TILE)
        reader = OWTilefile.get_tile_reader(path)
        for p in PREPROCESSORS_INDEPENDENT_SAMPLES_NO_EMSC:
            reader.set_preprocessor(p)
            reader.read()

    def test_preprocessor_list(self):
        # TODO problematic interface design: should be able to use Orange.data.Table directly
        path = os.path.join(get_sample_datasets_dir(), AGILENT_TILE)
        reader = OWTilefile.get_tile_reader(path)
        pp = PreprocessorList(PREPROCESSORS_INDEPENDENT_SAMPLES[0:7])
        reader.set_preprocessor(pp)
        t = reader.read()
        assert len(t.domain.attributes) == 3


class TestTileReaderWidget(WidgetTest):

    def setUp(self):
        self.widget = self.create_widget(OWTilefile)

    def test_load(self):
        path = os.path.join(get_sample_datasets_dir(), AGILENT_TILE)
        self.widget.add_path(path)
        self.widget.source = self.widget.LOCAL_FILE
        self.widget.load_data()
        self.wait_until_stop_blocking()
        self.assertNotEqual(self.get_output("Data"), None)

    def test_preproc_load(self):
        """ Test that loading a preprocessor signal in the widget works """
        # OWPreprocess test setup from test_owpreprocess.test_allpreproc_indv
        self.preproc_widget = self.create_widget(OWPreprocess)
        pp = PREPROCESSORS[0]
        # v0.3.13:
        # self.preproc_widget.add_preprocessor(0)
        self.preproc_widget.add_preprocessor(pp)
        self.preproc_widget.show_preview()
        self.preproc_widget.apply()
        self.commit_and_wait(widget=self.preproc_widget)
        pp_out = self.get_output("Preprocessor", widget=self.preproc_widget)
        self.send_signal("Preprocessor", pp_out, widget=self.widget)
        self.assertEqual(self.widget.preprocessor, pp_out)
        pp_from_model = self.preproc_widget._create_preprocessor(
            self.preproc_widget.preprocessormodel.item(0), None)
        # v0.3.13
        # self.assertIsInstance(self.widget.preprocessor, type(self.preproc_widget.buildpreproc()))
        self.assertIsInstance(self.widget.preprocessor, type(pp_from_model))
