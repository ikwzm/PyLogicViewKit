__version__     = "0.6.0"
__author__      = "Ichiro Kawazome"
__copyright__   = "Copyright (c) 2026 Ichiro Kawazome"
__license__     = "BSD 2-Clause"
__email__       = "ichiro_k@ca2-so-net.ne.jp"
__description__ = "GTKWave FST Package"

from .fst_reader        import FST_Reader
from .fst_wave_database import FST_Wave_DataBase
from .view_model        import View_Model
from .waveform_viewer   import WaveformViewer

__all__ = [
    "FST_Reader",
    "FST_Wave_DataBase",
    "View_Model",
    "WaveformViewer",
]
