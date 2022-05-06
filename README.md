pvalannot
======

### What is it?
A Python package to add p-value annotations on plots generated with Seaborn. Inspired by the magnificent package [statannotations](https://github.com/trevismd/statannotations). The major feature of pvalannot is the support of user-input statistical function (default is Wilcoxon ranksum test) and user-defined p-value text format.

### Installation

1. Clone the [GitHub repo](https://github.com/mourisl/pvalannot), e.g. with `git clone https://github.com/mourisl/pvalannot`.
2. Copy "pvalannot" folder to your project folder.

I will try to add pvalannot to PyPi in future.

### Usage
Here is a minimal example:

```python
import matplotlib.pyplot as plt
import seaborn as sns
from pvalannot import pvalannot

df = sns.load_dataset("tips")
x = "day"
y = "total_bill"
order = ['Sun', 'Thur', 'Fri', 'Sat']

fig = plt.figure(figsize=(5, 5))
ax = sns.boxplot(data=df, x=x, y=y, order=order)
pairs=[("Thur", "Fri"), ("Thur", "Sat"), ("Fri", "Sun")]

pvalannot.AddPvalAnnot(x=x, y=y, data=df, order=order, pairs=pairs, ax=ax, fig=fig)
```

AddPvalAnnot takes arguments like for user-defined features:

+ func: User-defined statistical function. The function takes two arguments arrays x, y. The function should return two numbers, first is statistical number (positive: x>y, negative: x<y) and test p-value. Default func=scipy.stats.ranksums() .
+ fmt: The format of p-value to show. This follows Python format string convention, for example fmt="%.2e" will output p-values in two digits scientific notation. 

See more examples in [dev.ipynb](https://github.com/mourisl/pvalannot/blob/main/dev.ipynb).

### Requirements
+Python >= 3.6
+seaborn >= 0.9
+matplotlib >= 2.2.2
+scipy >= 1.1.0
