#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

import sys
import runpy
import argparse

from .view_model       import View_Model
from .waveform_viewer  import WaveformViewer
from PySide6.QtWidgets import QApplication


class FST_Wave_Viewer:

    APPLICATION_INFO = {
        "Version"           : "0.6.0",
        "Author"            : "Ichiro Kawazome",
        "Author_Email"      : "ichiro_k@ca2-so-net.ne.jp",
        "License"           : "BSD 2-Clause",
        "Description"       : "FST Waveform Viewer",
    }
    def __init__(self):
        self.parser = argparse.ArgumentParser(description=self.APPLICATION_INFO["Description"])
        self.parser.add_argument("-m", "--model"     , metavar="FILE" , help="View Model File")
        self.parser.add_argument("-i", "--input"     , metavar="FILE" , help="Input FST file" )
        self.parser.add_argument("-S", "--start-time", metavar="TIME", default=None,
            help="Start Time (default: Simulation timestamp at the beginning of the FST data)")
        self.parser.add_argument("-E", "--end-time"  , metavar="TIME", default=None,
            help="End Time (default: Simulation time at the end of the FST data)")
    
    def load_view_model(self, view_model_file, file_name):
        namespace = {
            "View_Model"         : View_Model,
            "file_name"          : file_name ,
        }
        namespace  = runpy.run_path(view_model_file, init_globals=namespace)
        view_model = namespace["view_model"]

        if view_model is None:
            raise RuntimeError(f"{view_model_file} does not define 'view_model'")
        return view_model

    def main(self):
        args            = self.parser.parse_args()
        fst_file_name   = args.input
        view_model_file = args.model
        self.view_model = self.load_view_model(view_model_file, fst_file_name)

        if args.start_time is not None:
            start_time = self.view_model.parse_time(args.start_time)
            self.view_model.set_start_time(start_time)

        if args.end_time is not None:
            end_time   = self.view_model.parse_time(args.end_time)
            self.view_model.set_end_time(end_time)

        self.view_model.rebuild()
        self.view_model.load_wave()

        self.app = QApplication(sys.argv)

        self.waveform_viwer = WaveformViewer(self.view_model)
        self.waveform_viwer.show()

        return self.app.exec()

if __name__ == "__main__":
    fst_wave_viewer = FST_Wave_Viewer()
    sys.exit(fst_wave_viewer.main())
