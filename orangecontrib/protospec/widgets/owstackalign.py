import sys
import time

import numpy as np

import Orange.data
from Orange.widgets.widget import OWWidget, Msg, Input, Output
from Orange.widgets import gui, settings
#from Orange.widgets.utils.annotated_data import get_next_name
from orangecontrib.spectroscopy.widgets.gui import lineEditFloatOrNone
from orangecontrib.spectroscopy.widgets.owhyper import index_values, values_to_linspace, location_values
from orangecontrib.spectroscopy.data import _spectra_from_image, getx
import matplotlib.pyplot as plt  # remove later

from scipy.ndimage.interpolation import shift
from scipy.ndimage.filters import gaussian_filter, sobel

from skimage.feature import register_translation
from skimage.filters import threshold_otsu

from AnyQt.QtWidgets import QWidget, QFormLayout


# stack alignment code originally from: https://github.com/jpacold/STXM_live
def calculate_shift(img_a, img_b, pxwidth):
    """Uses the registration algorithm from scikit-image
    to calculate alignment to within 0.01 pixels or 1 nm,
    whichever is coarser."""

    sigma = 0.15 / pxwidth
    filt_a = gaussian_filter(img_a, min(sigma, 3.0))
    filt_b = gaussian_filter(img_b, min(sigma, 3.0))

    thr = threshold_otsu(filt_b)
    edgecheck = 1 * (filt_b < thr)

    # Check whether the object lies along a boundary of the image,
    # and if so apply a Sobel filter to use edges to align
    (a, b) = edgecheck.shape
    edgects = [np.sum(edgecheck[0]) / float(b), np.sum(edgecheck[-1]) / float(b),
               np.sum(edgecheck[:, 0]) / float(a), np.sum(edgecheck[:, -1]) / float(a)]
    if max(edgects) > 0.4:
        filt_a = sobel(filt_a)
        filt_b = sobel(filt_b)

    shift = register_translation(filt_a, filt_b, upsample_factor=min(1000.0, 100.0 / pxwidth))
    return [-shift[0][1], shift[0][0]]


def alignoneimage(img, sh):
    """Given an image and x,y shifts in pixels, returns a
    shifted image in which pixels beyond the boundaries of
    the original image have their values set to -1.
    """
    aligned = shift(img, [sh[1], -sh[0]], mode='nearest')

    (u, v) = img.shape

    if sh[1] >= 0.5:
        irange = range(int(sh[1]) + 1)
    elif sh[1] <= -0.5:
        irange = range(u - int(-sh[1]), u)
    else:
        irange = []
    for i in irange:
        for j in range(v):
            aligned[i][j] = np.nan

    if sh[0] >= 0.5:
        jrange = range(v - int(sh[0]), v)
    elif sh[0] <= -0.5:
        jrange = range(int(-sh[0]) + 1)
    else:
        jrange = []
    for i in range(u):
        for j in jrange:
            aligned[i][j] = np.nan

    return aligned


def alignstack(raw, pxwidth):
    """Given a stack of images and the width of each pixel (in
    microns), calculates the shifts needed to align all images
    with the highest-contrast image in the stack.

    Returns the list of shifts and a stack of aligned images.
    Pixels beyond the boundaries of the original images have
    their values set to -1.
    """

    shifts = np.array([[0.0, 0.0] for k in range(len(raw))])
    aligned = [np.zeros_like(raw[0]) for k in range(len(raw))]
    aligned[0] = raw[0][::]

    for k in range(1, len(raw)):
        shtmp = calculate_shift(raw[0], raw[k], pxwidth)
        shifts[k] += np.array(shtmp)
        aligned[k] = alignoneimage(raw[k], shifts[k])

    return [shifts, aligned]

def process_stack(data, pxwidth):
    # TODO: make sure that the variable names are handled dynamically for future data readers
    xat = data.domain["map_x"]
    yat = data.domain["map_y"]

    ndom = Orange.data.Domain([xat, yat])
    datam = Orange.data.Table(ndom, data)
    coorx = datam.X[:, 0]
    coory = datam.X[:, 1]

    data_points = datam.X
    lsx = values_to_linspace(coorx)
    lsy = values_to_linspace(coory)
    lsz = data.X.shape[1]

    print('aligning')
    # set data
    hypercube = np.ones((lsy[2], lsx[2], lsz)) * np.nan

    xindex = index_values(coorx, lsx)
    yindex = index_values(coory, lsy)
    hypercube[yindex, xindex] = data.X

    # TODO: the transpose should be taken out and the actual alignment code should work on the native structure
    [shifts, aligned_stack] = alignstack(hypercube.T, pxwidth)

    # TODO: calculate the cropping here and return the selection vector to the commit function to use it later for cropping
    xmin, ymin = shifts[:, 1].min(), shifts[:, 0].min()
    xmax, ymax = shifts[:, 1].max(), shifts[:, 0].max()
    xmin, xmax = int(xmin), int(xmax)
    ymin, ymax = int(ymin), int(ymax)

    shape = hypercube.shape
    cropped = np.array(aligned_stack).T[-ymin:(shape[0]-ymax), xmax:(shape[1]+xmin)]

    # transform numpy array back to Orange.data.Table
    features, spectra, data = _spectra_from_image(cropped,
                                                  getx(data),
                                                  np.linspace(*lsx)[xmax:(shape[1]+xmin)],
                                                  np.linspace(*lsy)[-ymin:(shape[0]-ymax)])

    # TODO: make it nice. Reused code from: data.py / SpectralFileFormat.read()
    newfeatures = [Orange.data.ContinuousVariable.make("%f" % f) for f in features]
    newdomain = Orange.data.Domain(newfeatures,
                                   class_vars=data.domain.class_vars,
                                   metas=data.domain.metas)
    newdata = data.transform(newdomain)
    newdata.X = spectra

    return newdata


class OWStackAlign(OWWidget):
    # Widget's name as displayed in the canvas
    name = "Align Stack"

    # Short widget description
    # TODO
    description = (
        "Builds or modifies the shape of the input dataset to create 2D maps "
        "from series data or change the dimensions of existing 2D datasets.")

    icon = "icons/category.svg"

    # Define inputs and outputs
    class Inputs:
        data = Input("Stack of images", Orange.data.Table, default=True)

    class Outputs:
        newstack = Output("Aligned image stack", Orange.data.Table, default=True)

    autocommit = settings.Setting(True)

    want_main_area = False
    resizing_enabled = False

    pxwidth = settings.Setting(None)
    isaligned = False
    new_stack = None

    class Warning(OWWidget.Warning):
        nodata = Msg("No useful data on input!")

    def __init__(self):
        super().__init__()

        box = gui.widgetBox(self.controlArea, "Parameters")

        form = QWidget()
        formlayout = QFormLayout()
        form.setLayout(formlayout)
        box.layout().addWidget(form)

        # TODO:
        # implement options
        #   [x] pixel width
        #   [ ] feedback for how well the images are aligned
        self.le1 = lineEditFloatOrNone(box, self, "pxwidth", callback=self.le1_changed)
        formlayout.addRow("Pixel Width", self.le1)

        self.data = None
        self.set_data(self.data)

        gui.auto_commit(self.controlArea, self, "autocommit", "Send Data")

    @Inputs.data
    def set_data(self, dataset):
        if dataset is not None:
            self.Warning.nodata.clear()

            self.isaligned = False
            self.new_stack = None

            self.data = dataset
        else:
            self.Warning.nodata()
        self.commit()

    def le1_changed(self):
        self.isaligned = False
        self.commit()

    def commit(self):
        new_stack = None

        if self.data and self.pxwidth is not None and not self.isaligned:
            self.new_stack = process_stack(self.data, self.pxwidth)
            self.isaligned = True

        self.Outputs.newstack.send(self.new_stack)

    def send_report(self):
        # TODO
        # there is a js error:
        # js: Uncaught TypeError: Cannot read property 'id' of undefined
        if self.pxwidth is not None:
            self.report_items((
                ("Image stack was aligned. Pixel width", self.pxwidth),
            ))
        else:
            return


def main(argv=sys.argv):
    from AnyQt.QtWidgets import QApplication
    app = QApplication(list(argv))
    ow = OWStackAlign()
    ow.show()
    ow.raise_()
    # TODO make a small file with test data that can be uploaded with the code
    dataset = Orange.data.Table("/Users/marko/STXM_align_stack/Sample_Stack_2016-04-20_136_2.hdf5")
    ow.set_data(dataset)
    app.exec_()
    return 0


if __name__ == "__main__":
    sys.exit(main())
