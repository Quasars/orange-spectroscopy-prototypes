orange-spectroscopy-prototypes
==============================

Prototype widgets / code for the [orange-spectroscopy](https://github.com/Quasars/orange-spectroscopy)
add-on for [Orange3](http://orange.biolab.si) / [Quasar](https://quasar.codes/).

⚠️ No guarantees of forward/backward compatibility: workflows based on this add-on may break in the future!

Installation
------------

To use this add-on, first download and install the current version of
[Quasar](https://quasar.codes/). Then

1. Open Quasar/Orange, choose "Options" from the menu and then "Add-ons".
2. A new window will open. There, press the "Add more..." button.
3. Enter "orange-spectroscopy-prototypes" in the dialog
4. Tick the checkbox in front of "Spectroscopy Prototypes" and confirm.
3. Restart Quasar/Orange.

Usage
-----

After the installation, the widgets from this add-on are registered with
Orange. The new widgets will appear in Orange Canvas, in the toolbox bar
under the section "Spectroscopy Prototypes".

Example workflows can be found under the "Help / Examples" menu.

For developers
--------------

If you would like to install from cloned git repository, run

    pip install .[doc,test,dev]

To register this add-on with Orange, but keep the code in the development
directory (do not copy it to Python's site-packages directory), run

    pip install -e .[doc,test,dev]

The repository has [pre-commit](https://pre-commit.com/) hooks configured, you
can set them up with

    pre-commit install

Further details can be found in orange-spectroscopy [CONTRIBUTING.md](https://github.com/Quasars/orange-spectroscopy/blob/master/CONTRIBUTING.md)
