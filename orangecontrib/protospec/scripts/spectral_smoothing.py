import numpy as np

SPECTRALHALFWIDTH = 5
TIME_RESOLVED = False

def spectral_smoothing(data, spectralHalfWidth, stdPeak):
    """
    Function to spectrally average the transmission. It's a window average
    with weights corresponding to the inverse of the standard deviation of
    each peaks : i-spectralHalfWidth:i+spectralHalfWidth+1 -> i.
    The data is saved under proc.data_name+'SpectralAvgOfFiles'

    Input   :   spectralHalfWidth(int) half of the size of the window to
                average points together. Usually set to 5.
                plotOn(bool) boolean to plot or not the data before/after
    """
    old_avg = np.copy(data)
    new_avg = np.copy(data)

    spectralHalfWidth = int(spectralHalfWidth)
    std_inv_sq = 1/stdPeak**2

    for i in np.arange(0,old_avg.shape[-1]):
        start = np.max([0,i-spectralHalfWidth])
        stop = np.min([i+spectralHalfWidth+1,old_avg.shape[-1]])
        new_avg[:,i] = np.mean(old_avg[:,start:stop]*weights(start,stop, std_inv_sq)*(stop-start),axis=-1)

    return new_avg


def weights(start, stop, std_inv_sq):
    """
    Function to generate the moving average weights from 1/stdPeak**2

    Input   :   start(int) the first peak where to compute the weight
                stop(int) the last peak where tocompute the weight
    """
    weight = std_inv_sq[start:stop]
    weight = weight/np.sum(weight)
    return weight


def getStdAxis(data, time_zero):
    """
    Function that gives you the standard deviation of a time resolved
    measurement

    """

    # for empty_TR-2019-02-11-21-48-38-_processed_data.h5
    # pretriggerslice comes out to 64, which is close to but not equal to time=0.
    # TODO ask IRsweep which to trust more: time 0 or this number
    # preTriggerSlice = int(np.floor(self.config.preTriggerSamples/self.config.sampleRate/self.config.interleaveTimeStep))
    preTriggerSlice = time_zero
    return np.std(data[0:preTriggerSlice,:],axis=0)


data = in_data.copy()
if not TIME_RESOLVED:
    stdPeak = np.array([v.attributes['stdPeak'] for v in data.domain.attributes])
    time_zero = None
else:
    time = data.get_column([v for v in data.domain.metas if v.name=="Time"][0])
    time_zero = int(np.nonzero(time == 0)[0])
    stdPeak = getStdAxis(data.X, time_zero)
data.X = np.atleast_2d(spectral_smoothing(data.X, SPECTRALHALFWIDTH, stdPeak))
out_data = data

# Output stdPeak
if stdPeak is not None:
    out_object = in_data.copy()
    out_object.X = np.atleast_2d(stdPeak)
