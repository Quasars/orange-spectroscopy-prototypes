import numpy as np

from orangecontrib.spectroscopy.data import getx, build_spec_table

def add_lag_measurement(data, calibration_data):# calibrated_wn, peakMeanAmpCalib, flipped):
    """
    Compares the peak mean amp of the current measurement with the calibration
    one and deduce a lag which is introduced in the wnAxisCalib to create
    the correct wnAxis
    """

    noLines = len(data.domain.attributes)
    calibrated_wn = getx(calibration_data)
    try:
        assert noLines == len(calibrated_wn)
    except AssertionError:
        print(f"Calibration dataset doesn't match: {noLines} != {len(calibrated_wn)}")

    first_wn = np.min(calibrated_wn)
    wn_spacing_calibrated = np.abs(np.mean(np.gradient(calibrated_wn)))

    peakMeanAmp = np.array([v.attributes['peakMeanAmp'] for v in data.domain.attributes])
    peakMeanAmpCalib = calibration_data[0]

    corr = np.correlate(peakMeanAmpCalib, peakMeanAmp,'full')

    lag = float(np.argmax(corr))-noLines+1
    new_wn = np.arange(0, noLines)*wn_spacing_calibrated
    new_wn = new_wn + first_wn + lag*wn_spacing_calibrated
    if calibration_data.attributes['flipped']:
        new_wn = np.flip(new_wn,axis=0)

    return new_wn


if in_data and in_object:
    data = in_data.copy()
    calibration_data = in_object.copy()

    new_wn_axis = add_lag_measurement(data, calibration_data)
    assert len(new_wn_axis) == len(in_data.domain.attributes)

    corrected_table = build_spec_table(new_wn_axis, in_data.X, in_data)
    out_data = corrected_table
else:
    print("Connect data to input / calibration data to object.")
    out_data = None
