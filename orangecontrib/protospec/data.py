import json

from os import path

import h5py
import numpy as np
import pandas as pd
import Orange.data
from Orange.data import (
    ContinuousVariable,
    DiscreteVariable,
    StringVariable,
    TimeVariable,
    Domain,
    Table,
)
from Orange.data.io import FileFormat

from Orange.version import short_version as ORANGE_VERSION  # noqa N812
from orangecontrib.spectroscopy.io import HDF5MetaReader


# For testing until https://github.com/biolab/orange3/pull/6791 is resolved
class HDF5Reader(FileFormat):
    """Reader for Orange HDF5 files"""

    EXTENSIONS = ('.hdf5',)
    DESCRIPTION = 'Orange on-disk data'
    SUPPORT_COMPRESSED = False
    SUPPORT_SPARSE_DATA = False

    def read(self):
        def read_domain(sub):
            d = f['domain']
            subdomain = d[sub].asstr() if sub in d else []
            subdomain_args = (
                d[f'{sub}_args'].asstr()
                if f'{sub}_args' in d
                else ['{}'] * len(subdomain)
            )
            for attr, args in zip(subdomain, subdomain_args):
                yield attr[0], attr[1], json.loads(args)

        def make_var(name, header, args):
            var_cls = [
                var
                for var in (
                    ContinuousVariable,
                    DiscreteVariable,
                    StringVariable,
                    TimeVariable,
                )
                if header in var.TYPE_HEADERS
            ][0]
            new_var = var_cls(
                name, **{key: val for key, val in args.items() if key != "attributes"}
            )
            new_var.attributes = args.get("attributes", {})
            return new_var

        def read_hdf5(name, as_str=False):
            if name in f:
                if as_str:
                    return f[name].asstr()[:]
                return f[name]
            return None

        with h5py.File(self.filename, "r") as f:
            try:
                assert f.attrs['creator'] == "Orange"
            except KeyError:
                assert 'domain' in f

            domain = Domain(
                *[
                    [make_var(*args) for args in read_domain(subdomain)]
                    for subdomain in ['attributes', 'class_vars', 'metas']
                ]
            )

            X = read_hdf5("X")  # noqa N806
            Y = read_hdf5("Y")  # noqa N806

            if len(domain.metas) > 1:
                metas = np.hstack(
                    [
                        read_hdf5(f'metas/{i}', isinstance(attr, StringVariable))
                        for i, attr in enumerate(domain.metas)
                    ]
                )
            elif len(domain.metas) == 1:
                metas = read_hdf5(
                    'metas/0', isinstance(domain.metas[0], StringVariable)
                )
            else:
                metas = None

            table = Table.from_numpy(domain, X, Y, metas)
            if isinstance(self.filename, str):
                table.name = path.splitext(path.split(self.filename)[-1])[0]
        self.set_table_metadata(self.filename, table)
        return table

    @classmethod
    def write_file(cls, filename, data):
        def parse(attr):
            params = (attr.name, attr.TYPE_HEADERS[1], {"attributes": attr.attributes})
            if isinstance(attr, DiscreteVariable):
                params[2].update(values=attr.values)
            elif isinstance(attr, TimeVariable):
                params[2].update(have_date=attr.have_date, have_time=attr.have_time)
            elif isinstance(attr, ContinuousVariable):
                params[2].update(number_of_decimals=attr.number_of_decimals)
            return params

        with h5py.File(filename, 'w') as f:
            f.attrs['creator'] = "Orange"
            f.attrs['Orange_version'] = ORANGE_VERSION
            f.attrs['HDF5_Version'] = h5py.version.hdf5_version
            f.attrs['h5py_version'] = h5py.version.version
            str_dtype = h5py.string_dtype()
            for subdomain in ['attributes', 'class_vars', 'metas']:
                parsed = [parse(feature) for feature in getattr(data.domain, subdomain)]
                domain = np.array(
                    [[name, header] for name, header, _ in parsed], dtype=str_dtype
                )
                domain_args = np.array(
                    [json.dumps(args) for *_, args in parsed], dtype=str_dtype
                )
                f.create_dataset(f'domain/{subdomain}', data=domain)
                f.create_dataset(f'domain/{subdomain}_args', data=domain_args)
            f.create_dataset("X", data=data.X)
            if data.Y.size:
                f.create_dataset("Y", data=data.Y)
            if data.metas.size:
                for i, attr in enumerate(data.domain.metas):
                    col_type = str_dtype if isinstance(attr, StringVariable) else 'f'
                    col_data = data.metas[:, [i]].astype(col_type)
                    if col_type != 'f':
                        col_data[pd.isnull(col_data)] = ""
                    f.create_dataset(f'metas/{i}', data=col_data, dtype=col_type)
        cls.write_table_metadata(filename, data)


class IRisF1HDF5Reader(FileFormat):
    """Reader for IRsweep IRis-F1 HDF5 _processed_data files"""

    EXTENSIONS = ('.h5',)
    DESCRIPTION = 'IRsweep IRis-F1 _processed_data'

    TRANSMISSION = "Transmission"
    NORMALIZATION_VECTOR = "Normalization Vector"

    @property
    def valid(self):
        with h5py.File(self.filename, "r") as f:
            try:
                f['info'].attrs['SoftwareVersion'][0]
            except KeyError:
                try:
                    f['info'].attrs['Version'][0]
                except KeyError:
                    return False
                else:
                    return True
            else:
                return True

    @property
    def sheets(self):
        if self.valid:
            return [self.TRANSMISSION, self.NORMALIZATION_VECTOR]

    def read_spectra(self):
        from heterodyne_postprocessing.processing.postProcessorHDF5 import (
            PostProcessorHDF5Loader,
        )

        proc = PostProcessorHDF5Loader()
        proc.load_configuration(self.filename)
        proc.load_transmission()

        energy = proc.data['wnAxis']

        if self.sheet == self.NORMALIZATION_VECTOR:
            data = proc.data['normalizationVector'].T

            import_attrs = [
                'stdPeak',
                'peakMeanAmp',
            ]
            var_attr_d = {k: proc.data[k] for k in import_attrs if k in proc.data}

            return (energy, data, None, var_attr_d)

        elif proc.is_timeresolved():
            data = proc.data['transientTrans']
            time_axis = proc.data['timeAxis']

            import_attrs = [
                'peakMeanAmp',
            ]
            var_attr_d = {k: proc.data[k] for k in import_attrs if k in proc.data}

            return (
                *self._spectra_from_time_resolved(data, energy, time_axis),
                var_attr_d,
            )

        else:
            data = proc.data['transmission'].T

            import_attrs = [
                'stdPeak',
                'peakMeanAmp',
            ]
            var_attr_d = {k: proc.data[k] for k in import_attrs if k in proc.data}

            # Time stamps
            time_stamp = np.atleast_2d(proc.data['timeStamp']).T
            add_dom = Orange.data.Domain(
                [], None, metas=[Orange.data.ContinuousVariable.make("Time")]
            )
            add_table = Orange.data.Table.from_numpy(
                add_dom,
                X=np.zeros((len(data), 0)),
                metas=np.asarray(time_stamp, dtype=object),
            )

            return (energy, data, add_table, var_attr_d)

    # same as SpectralFileFormat but accepts and uses variable attributes
    def read(self):
        domvals, data, additional_table, var_attr_d = self.read_spectra()
        data = np.asarray(data, dtype=np.float64)  # Orange assumes X to be float64
        features = []
        for i, f in enumerate(domvals):
            var = Orange.data.ContinuousVariable.make("%f" % f)
            for k, v in var_attr_d.items():
                var.attributes[k] = v[i]
            features.append(var)
        if additional_table is None:
            domain = Orange.data.Domain(features, None)
            return Orange.data.Table(domain, data)
        else:
            domain = Domain(
                features,
                class_vars=additional_table.domain.class_vars,
                metas=additional_table.domain.metas,
            )
            ret_data = Table.from_numpy(
                domain, X=data, Y=additional_table.Y, metas=additional_table.metas
            )
            return ret_data

    # based on _spectra_from_image
    @staticmethod
    def _spectra_from_time_resolved(X, features, time_axis):  # noqa N803
        """
        Create a spectral format (returned by SpectralFileFormat.read_spectra)
        from 3D data organized [ time, wavelengths, acquisitions ]
        """
        X = np.asarray(X)  # noqa N806
        # rearrange axes: [ acquisitions, time, wavelengths ]
        X = X.transpose((2, 0, 1))  # noqa N806
        time_axis = np.asarray(time_axis)
        acq_nums = np.arange(X.shape[1])

        # each spectrum has its own row
        spectra = X.reshape((X.shape[0] * X.shape[1], X.shape[2]))

        # locations
        acq_num = np.repeat(np.arange(X.shape[0]), X.shape[1])
        time = np.tile(np.arange(X.shape[1]), X.shape[0])
        metas = np.array([time_axis[time], acq_nums[acq_num]]).T

        domain = Orange.data.Domain(
            [],
            None,
            metas=[
                Orange.data.ContinuousVariable.make("Time"),
                Orange.data.ContinuousVariable.make("Acquisition"),
            ],
        )
        data = Orange.data.Table.from_numpy(
            domain, X=np.zeros((len(spectra), 0)), metas=np.asarray(metas, dtype=object)
        )
        return features, spectra, data


# Required with new .h5 SOLEIL ROCK reader
class HDF5MetaMetaReader(FileFormat):
    """Meta-meta-reader to select appropriate HDF5 reader for .h5 extension."""

    EXTENSIONS = ('.h5',)
    DESCRIPTION = 'HDF5 Meta-meta-reader'
    PRIORITY = HDF5MetaReader.PRIORITY - 1

    @property
    def sheets(self) -> list:
        reader = IRisF1HDF5Reader(self.filename)
        if reader.valid:
            return reader.sheets
        else:
            return HDF5MetaReader(self.filename).sheets

    def read(self):
        irisf1_reader = IRisF1HDF5Reader(filename=self.filename)
        if irisf1_reader.valid:
            return irisf1_reader.read()
        else:
            return HDF5MetaReader(filename=self.filename).read()
