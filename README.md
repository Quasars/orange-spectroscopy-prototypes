[![DOI](https://zenodo.org/badge/53335377.svg)](https://zenodo.org/badge/latestdoi/53335377)

orange-spectroscopy-prototypes
==============================

Prototype widgets / code for the [orange-spectroscopy](https://github.com/Quasars/orange-spectroscopy)
add-on for [Orange3](http://orange.biolab.si) for the analysis of spectral data.

Installation
------------

To use this add-on, first download and install the current version of
[Orange3](http://orange.biolab.si). Next, install the orange-spectroscopy add-on:

1. Open Orange Canvas, choose "Options" from the menu and then "Add-ons".
2. A new window will open. There, tick the checkbox in front of "Spectroscopy" and confirm.
3. Restart Orange.

Finally, install the prototypes add-on as in [For developers](#For developers).

Usage
-----

After the installation, the widgets from this add-on are registered with
Orange. The new widgets will appear in Orange Canvas, in the toolbox bar
under the section Spectroscopy-Prototypes.

For developers
--------------

If you would like to install from cloned git repository, run

    pip install .

To register this add-on with Orange, but keep the code in the development
directory (do not copy it to Python's site-packages directory), run

    pip install -e .

Further details can be found in orange-spectroscopy [CONTRIBUTING.md](https://github.com/Quasars/orange-spectroscopy/blob/master/CONTRIBUTING.md)