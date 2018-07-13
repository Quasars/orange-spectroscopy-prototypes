from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QApplication

from Orange.preprocess.preprocess import Preprocess
from Orange.widgets.data import owfile
from Orange.widgets.widget import Input


class OWTilefile(owfile.OWFile):
    name = "Tile File"
    id = "orangecontrib.protospec.widgets.tilefile"
    icon = "icons/tilefile.svg"
    description = "Read data tile-by-tile from input files, " \
                  "preprocess, and send a data table to the output."
    priority = 10000

    class Inputs:
        preprocessor = Input("Preprocessor", Preprocess)

    @Inputs.preprocessor
    def update_preprocessor(self, preproc=None):
        self.preprocessor = preproc



def _get_reader(rp):
    if rp.file_format:
        reader_class = class_from_qualified_name(rp.file_format)
        return reader_class(rp.abspath)
    else:
        return FileFormat.get_reader(rp.abspath)


if __name__ == "__main__":
    import sys
    from orangecontrib.spectroscopy.preprocess import Cut
    a = QApplication(sys.argv)
    preproc = Cut(lowlim=2000, highlim=2006)
    ow = OWTilefile()
    ow.Inputs.preprocessor = preproc
    ow.show()
    a.exec_()
    ow.saveSettings()