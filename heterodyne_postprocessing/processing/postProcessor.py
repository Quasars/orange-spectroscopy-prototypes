# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from heterodyne_postprocessing.processing.postProcessorPlottingUtilities import PostProcessorPlottingUtilities


class PostProcessor(PostProcessorPlottingUtilities):
    def __init__(self):
        super().__init__()