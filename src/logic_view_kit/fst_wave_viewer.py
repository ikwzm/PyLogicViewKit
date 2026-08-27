#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

import sys
import runpy
import argparse

from .view_model       import View_Model
from .waveform_viewer  import WaveformViewer
from PySide6.QtWidgets import QApplication

APPLICATION_INFO = {
    "Version"           : "0.6.0",
    "Author"            : "Ichiro Kawazome",
    "Author_Email"      : "ichiro_k@ca2-so-net.ne.jp",
    "License"           : "BSD 2-Clause",
    "Description"       : "FST Waveform Viewer",
}

def load_view_model(view_model_file, file_name):
    namespace = {
        "View_Model"         : View_Model,
        "file_name"          : file_name ,
    }

    namespace = runpy.run_path(view_model_file, init_globals=namespace)

    view_model = namespace["view_model"]

    if view_model is None:
        raise RuntimeError(f"{view_model_file} does not define 'view_model'")

    return view_model

def main():
    parser = argparse.ArgumentParser(description=APPLICATION_INFO["Description"])
    parser.add_argument("file_name"         , metavar="FILE" , help="Input FST file" )
    parser.add_argument("-C", "--config"    , metavar="FILE" , help="Configuration File")
    parser.add_argument("-S", "--start-time", metavar="TIME", default=None,
                        help="Start Time (default: Simulation timestamp at the beginning of the FST data)")
    parser.add_argument("-E", "--end-time"  , metavar="TIME", default=None,
                        help="End Time (default: Simulation time at the end of the FST data)")

    args = parser.parse_args()

    file_name       = args.file_name
    view_model_file = args.config

    view_model = load_view_model(view_model_file, file_name)

    if args.start_time is not None:
        start_time = view_model.parse_time(args.start_time)
        view_model.set_start_time(start_time)

    if args.end_time is not None:
        end_time   = view_model.parse_time(args.end_time)
        view_model.set_end_time(end_time)

    view_model.rebuild()
    view_model.load_wave()

    app = QApplication(sys.argv)

    waveform_viwer = WaveformViewer(view_model)
    waveform_viwer.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
