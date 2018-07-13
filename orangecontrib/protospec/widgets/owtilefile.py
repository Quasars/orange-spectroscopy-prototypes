from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QApplication

from Orange.data.io import FileFormat, UrlReader, class_from_qualified_name
from Orange.preprocess.preprocess import Preprocess
from Orange.widgets import gui
from Orange.widgets.data import owfile
from Orange.widgets.settings import Setting
from Orange.widgets.utils.filedialogs import RecentPath
from Orange.widgets.widget import Input


class OWTilefile(owfile.OWFile):
    name = "Tile File"
    id = "orangecontrib.protospec.widgets.tilefile"
    icon = "icons/tilefile.svg"
    description = "Read data tile-by-tile from input files, " \
                  "preprocess, and send a data table to the output."
    priority = 10000

    # Overload RecentPathsWidgetMixin.recent_paths to set defaults
    recent_paths = Setting([
        RecentPath("", "sample-datasets", "agilent/5_mosaic_agg1024.dmt"),
    ])

    class Inputs:
        preprocessor = Input("Preprocessor", Preprocess)

    def __init__(self):
        self.preprocessor = None
        super().__init__()

        box = gui.vBox(self.controlArea, "Preprocessor")
        self.info_preproc = gui.widgetLabel(box, 'No preprocessor on input.')


    @Inputs.preprocessor
    def update_preprocessor(self, preproc):
        if preproc is None:
            self.info_preproc.setText("No preprocessor on input.")
        elif self.preprocessor is not preproc:
            self.info_preproc.setText("New preprocessor, reload file to use.\n{0}".format(preproc))
        self.preprocessor = preproc

    def _get_reader(self):
        """
        Returns
        -------
        FileFormat
        """
        # from AnyQt.QtCore import pyqtRemoveInputHook
        # pyqtRemoveInputHook()
        # import pdb; pdb.set_trace()
        if self.source == self.LOCAL_FILE:
            path = self.last_path()
            if self.recent_paths and self.recent_paths[0].file_format:
                qname = self.recent_paths[0].file_format
                reader_class = class_from_qualified_name(qname)
                reader = reader_class(path)
            else:
                reader = FileFormat.get_reader(path)
            if self.recent_paths and self.recent_paths[0].sheet:
                reader.select_sheet(self.recent_paths[0].sheet)
            # set preprocessor here
            if self.preprocessor is not None and hasattr(reader, "read_tile"):
                reader.set_preprocessor(self.preprocessor)
                self.info_preproc.setText(str(self.preprocessor))
            return reader
        elif self.source == self.URL:
            url = self.url_combo.currentText().strip()
            if url:
                return UrlReader(url)


def _get_reader(rp):
    if rp.file_format:
        reader_class = class_from_qualified_name(rp.file_format)
        return reader_class(rp.abspath)
    else:
        return FileFormat.get_reader(rp.abspath)


if __name__ == "__main__":
    import sys
    from orangecontrib.spectroscopy.preprocess import Cut
    import orangecontrib.protospec #load readers
    a = QApplication(sys.argv)
    preproc = Cut(lowlim=2000, highlim=2006)
    ow = OWTilefile()
    ow.update_preprocessor(preproc)
    ow.show()
    a.exec_()
    ow.saveSettings()