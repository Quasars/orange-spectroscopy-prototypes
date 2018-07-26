import numpy as np

import Orange.data
from Orange.data.io import FileFormat

from orangecontrib.spectroscopy.data import _spectra_from_image
from orangecontrib.spectroscopy.preprocess import Cut

from .agilent import agilentMosaicTiles


class TileFileFormat:

    def read_tile(self):
        """ Read file in chunks (tiles) to allow preprocessing before combining
        into one large Table.

        Return a generator of Tables, where each Table is a chunk of the total.
        Tables should already have appropriate meta-data (i.e. map_x/map_y)
        """
        pass

    def read(self):
        ret_table = None
        for tile_table in self.read_tile():
            if ret_table is None:
                ret_table = self.preprocess(tile_table)
            else:
                tile_table_pp = tile_table.transform(ret_table.domain)
                ret_table.extend(tile_table_pp)

        return ret_table


class agilentMosaicTileReader(FileFormat, TileFileFormat):
    """ Tile-by-tile reader for Agilent FPA mosaic image files"""
    EXTENSIONS = ('.dmt',)
    DESCRIPTION = 'Agilent Mosaic Tile-by-tile'

    def __init__(self, filename):
        super().__init__(filename)
        self.preprocessor = None

    def set_preprocessor(self, preprocessor):
        self.preprocessor = preprocessor

    def preprocess(self, table):
        if self.preprocessor is not None:
            return self.preprocessor(table)
        else:
            return table


    def read_tile(self):
        ret_table = None
        am = agilentMosaicTiles(self.filename)
        info = am.info
        tiles = am.tiles
        ytiles = am.tiles.shape[0]
        xtiles = am.tiles.shape[1]

        try:
            features = info['wavenumbers']
        except KeyError:
            #just start counting from 0 when nothing is known
            features = np.arange(X.shape[-1])

        attrs = [Orange.data.ContinuousVariable.make("%f" % f) for f in features]
        domain = Orange.data.Domain(attrs, None,
                                    metas=[Orange.data.ContinuousVariable.make("map_x"),
                                           Orange.data.ContinuousVariable.make("map_y")]
                                    )

        try:
            px_size = info['FPA Pixel Size'] * info['PixelAggregationSize']
        except KeyError:
            # Use pixel units if FPA Pixel Size is not known
            px_size = 1

        for (x, y) in np.ndindex(tiles.shape):
            tile = tiles[x, y]()
            x_size, y_size = tile.shape[1], tile.shape[0]
            x_locs = np.linspace(x*x_size*px_size, (x+1)*x_size*px_size, num=x_size, endpoint=False)
            y_locs = np.linspace((ytiles-y-1)*y_size*px_size, (ytiles-y)*y_size*px_size, num=y_size, endpoint=False)

            _, data, additional_table = _spectra_from_image(tile, None, x_locs, y_locs)
            data = np.asarray(data, dtype=np.float64)  # Orange assumes X to be float64
            tile_table = Orange.data.Table.from_numpy(domain, X=data, metas=additional_table.metas)
            yield tile_table