#!/usr/bin/env python

import os
from os import walk, path
import subprocess
import sys

from setuptools import setup, find_packages, Command

PACKAGES = find_packages()

PACKAGE_DATA = {}

README_FILE = os.path.join(os.path.dirname(__file__), 'README.pypi')
LONG_DESCRIPTION = open(README_FILE).read()

DATA_FILES = [
    # Data files that will be installed outside site-packages folder
]

ENTRY_POINTS = {
    # Entry points that marks this package as an orange add-on. If set, addon will
    # be shown in the add-ons manager even if not published on PyPi.
    'orange3.addon': (
        'protospec = orangecontrib.protospec',
    ),

    # Entry point used to specify packages containing tutorials accessible
    # from welcome screen. Tutorials are saved Orange Workflows (.ows files).
    'orange.widgets.tutorials': (
        # Syntax: any_text = path.to.package.containing.tutorials
        'protospec_tutorials = orangecontrib.protospec.tutorials',
    ),

    # Entry point used to specify packages containing widgets.
    'orange.widgets': (
        # Syntax: category name = path.to.package.containing.widgets
        # Widget category specification can be seen in
        #    orangecontrib/example/widgets/__init__.py
        'Spectroscopy Prototypes = orangecontrib.protospec.widgets',
    ),

    # Register widget help
    "orange.canvas.help": (
        'html-index = orangecontrib.protospec.widgets:WIDGET_HELP_PATH',)

}

KEYWORDS = [
    # [PyPi](https://pypi.python.org) packages with keyword "orange3 add-on"
    # can be installed using the Orange Add-on Manager
    'orange3 add-on',
    'spectroscopy',
    'infrared',
    'prototypes'
]


class CoverageCommand(Command):
    """A setup.py coverage subcommand developers can run locally."""
    description = "run code coverage"
    user_options = []
    initialize_options = finalize_options = lambda self: None

    def run(self):
        """Check coverage on current workdir"""
        sys.exit(subprocess.call(r'''
        coverage run --source=orangecontrib.protospec -m unittest
        echo; echo
        coverage report --omit="*/tests/*"
        coverage html --omit="*/tests/*" &&
            { echo; echo "See also: file://$(pwd)/htmlcov/index.html"; echo; }
        ''', shell=True, cwd=os.path.dirname(os.path.abspath(__file__))))


class LintCommand(Command):
    """A setup.py lint subcommand developers can run locally."""
    description = "run code linter(s)"
    user_options = []
    initialize_options = finalize_options = lambda self: None

    def run(self):
        """Lint current branch compared to a reasonable master branch"""
        sys.exit(subprocess.call(r'''
        set -eu
        upstream="$(git remote -v |
                    awk '/[@\/]github.com[:\/]Quasars\/orange-protospec[\. ]/{ print $1; exit }')"
        git fetch -q $upstream master
        best_ancestor=$(git merge-base HEAD refs/remotes/$upstream/master)
        .travis/check_pylint_diff $best_ancestor
        ''', shell=True, cwd=os.path.dirname(os.path.abspath(__file__))))


TEST_SUITE = "orangecontrib.protospec.tests.suite"


def include_documentation(local_dir, install_dir):
    global DATA_FILES
    if 'bdist_wheel' in sys.argv and not path.exists(local_dir):
        print("Directory '{}' does not exist. "
              "Please build documentation before running bdist_wheel."
              .format(path.abspath(local_dir)))
        sys.exit(0)

    doc_files = []
    for dirpath, _, files in walk(local_dir):
        doc_files.append((dirpath.replace(local_dir, install_dir),
                          [path.join(dirpath, f) for f in files]))
    DATA_FILES.extend(doc_files)


if __name__ == '__main__':

    cmdclass = {
        'coverage': CoverageCommand,
        'lint': LintCommand,
    }

    include_documentation('doc/build/html', 'help/orange-protospec')

    setup(
        name="Orange-Spectroscopy-Prototypes",
        description='Prototype widgets for orange-spectroscopy add-on',
        long_description=LONG_DESCRIPTION,
        author='Canadian Light Source, Biolab UL, Soleil, Elettra',
        author_email='stuart.read@lightsource.ca',
        version="0.1.2",
        packages=PACKAGES,
        package_data=PACKAGE_DATA,
        data_files=DATA_FILES,
        install_requires=[
            'orange-spectroscopy>=0.3.7',
        ],
        entry_points=ENTRY_POINTS,
        keywords=KEYWORDS,
        namespace_packages=['orangecontrib'],
        test_suite=TEST_SUITE,
        include_package_data=True,
        zip_safe=False,
        url="https://github.com/stuart-cls/orange-spectroscopy-prototypes",
        cmdclass=cmdclass,
    )
