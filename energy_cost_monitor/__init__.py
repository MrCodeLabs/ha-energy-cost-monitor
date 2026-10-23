"""Standalone core import facade; importing it does not load Home Assistant.

The canonical core ships inside the custom component so installation requires
no unpublished dependency and no duplicate source tree.
"""

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent.parent / "custom_components"
                / "energy_cost_monitor" / "_core")]
