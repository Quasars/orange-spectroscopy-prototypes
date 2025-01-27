import numpy as np

import Orange.data

# Average Time-Resolved data by acquisition number
data = in_data.copy()

num_acqs, _ = data.get_column_view("Acquisition")
num_acqs = int(num_acqs.max()) + 1
print(f"Averaging {num_acqs} acquisitions.")
hypercube = data.X.reshape((num_acqs, int(data.X.shape[0]/num_acqs), data.X.shape[1]))
avg_hypercube = np.mean(hypercube, axis=0)

n_domain = Orange.data.Domain(data.domain.attributes, data.domain.class_vars,
                              [v for v in data.domain.metas if v.name != "Acquisition"])

table = Orange.data.Table(n_domain, avg_hypercube, Y=None, metas=data.metas[0:avg_hypercube.shape[0],:-1])
out_data = table
