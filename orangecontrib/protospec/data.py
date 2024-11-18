import json

from os import path

import h5py
import numpy as np
import pandas as pd
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
