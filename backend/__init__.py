"""
ResQ Web - Backend Package Initialization
Ensures seamless path resolution for backend submodules and the agent supervisor.
"""

import sys
import os

_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

