import gc
import sys

from AnyQt.QtWidgets import QApplication
import Orange.data

from orangecontrib.spectroscopy.widgets.owhyper import OWHyper
import orangecontrib.spectroscopy # datasets
import orangecontrib.protospec

def main(argv=None):
    if argv is None:
        argv = sys.argv
    argv = list(argv)
    app = QApplication(argv)

    data = Orange.data.Table("agilent/5_mosaic_agg1024.dmt")
    # data = Orange.data.Table("var/2017-11-10 4X-25X/2017-11-10 4X-25X.dmt")
    # data = Orange.data.Table("C:\\Users\\reads\\tmp\\aff-testdata\\2017-11-24 USAF after FPA pumpdown\\USAF 25X Mosaic\\USAF 25X Mosaic.dmt")

    w = OWHyper()
    w.show()
    w.set_data(data)
    w.handleNewSignals()
    rval = app.exec_()
    w.set_data(None)
    w.handleNewSignals()
    w.deleteLater()
    del w
    app.processEvents()
    gc.collect()
    return rval

if __name__ == "__main__":
    import sys
    sys.exit(main())
