import sys

import numpy as np

import Orange.data
from Orange.data.filter import Values
from Orange.widgets.utils.annotated_data import create_annotated_table
from Orange.widgets.visualize import owboxplot
from Orange.widgets.widget import Output


class OWBoxPlotOutput(owboxplot.OWBoxPlot):
    """
    BoxPlot, but with output of simple stats.
    """
    name = "Simple Stats"
    id = "orangecontrib.protospec.widgets.owboxplotout.OWBoxPlotOutput"
    description = "Visualize and output simple statistics."

    class Outputs(owboxplot.OWBoxPlot.Outputs):
        stats = Output("Statistics", Orange.data.Table, default=True)

    def __init__(self):
        super().__init__()

    def build_stats_table(self):
        attrs = []
        class_vars = []
        metas = []
        stats = ["mean", "var"]
        attr_orig = self.attribute
        domain = self.dataset.domain
        for attr in self.attrs:
            #TODO what to do with discrete variables here and below
            if attr is self.group_var:
                class_vars.append(attr)
            elif attr in domain.attributes:
                attrs.extend([type(attr).make(attr.name + "_" + stat) for stat in stats])
            elif attr in domain.class_vars:
                class_vars.extend([type(attr).make(attr.name + "_" + stat) for stat in stats])
            elif attr in domain.metas:
                metas.extend([type(attr).make(attr.name + "_" + stat) for stat in stats])
        ndom = Orange.data.Domain(attrs, class_vars, metas)
        nrows = len(self.group_var.values) if self.group_var else 1
        table = Orange.data.Table.from_domain(ndom, n_rows=nrows)
        for attr in self.attrs:
            self.attribute = attr
            self.compute_box_data()
            if attr is self.group_var:
                if table.domain.class_var:
                    table.Y[:] = range(len(table))
                else:
                    table.Y[:,table.domain.class_vars.index(attr)] = range(len(table))
            elif attr.is_continuous:
                for stat in stats:
                    newattr = type(attr).make(attr.name + "_" + stat)
                    newvals = [getattr(box, stat) for box in self.stats]
                    if newattr in table.domain.attributes:
                        table[:, newattr].X[:,0] = newvals
                    elif newattr in table.domain.class_vars:
                        table[:, newattr].Y[:] = newvals
                    elif newattr in table.domain.metas:
                        #TODO can't set values in metas (object array) for some reason
                        #table[:, newattr].metas[:,0] = newvals
                        table.metas[:,table.domain.metas.index(newattr)] = newvals




        self.attribute = attr_orig
        return table

    def commit(self):
        self.conditions = [item.filter for item in
                           self.box_scene.selectedItems() if item.filter]
        selected, selection = None, []
        if self.conditions:
            selected = Values(self.conditions, conjunction=False)(self.dataset)
            selection = np.in1d(
                self.dataset.ids, selected.ids, assume_unique=True).nonzero()[0]
        self.Outputs.selected_data.send(selected)
        self.Outputs.annotated_data.send(
            create_annotated_table(self.dataset, selection))
        if self.dataset:
            self.Outputs.stats.send(self.build_stats_table())


def main(argv=None):
    from AnyQt.QtWidgets import QApplication
    if argv is None:
        argv = sys.argv
    argv = list(argv)
    app = QApplication(argv)
    if len(argv) > 1:
        filename = argv[1]
    else:
        filename = "collagen"

    data = Orange.data.Table(filename)
    w = OWBoxPlotOutput()
    w.show()
    w.raise_()
    w.set_data(data)
    w.handleNewSignals()
    rval = app.exec_()
    w.set_data(None)
    w.handleNewSignals()
    w.saveSettings()
    return rval

if __name__ == "__main__":
    sys.exit(main())