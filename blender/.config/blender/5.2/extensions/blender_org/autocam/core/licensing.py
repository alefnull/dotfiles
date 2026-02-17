# ##### BEGIN GPL LICENSE BLOCK #####
#
#  SPDX-License-Identifier: GPL-3.0-or-later
#
#  AutoCam - Intuitive camera tools, built for artists.
#  Copyright (C) 2025  Agniv Duarah  (RenderRides)  <support@renderrides.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

"""
AutoCam feature licensing and edition gating.

Single source of truth for:
- Which features are Pro-only
- Whether this build is Pro or Free
- Helpers for UI and operator gating

Build Strategy:
- Free build: licensing.py has EDITION = Edition.FREE
- Pro build:  licensing.py has EDITION = Edition.PRO
- Build script patches this single line when creating distributions
"""

from enum import Enum, auto


class Edition(Enum):
    FREE = auto()
    PRO = auto()


# ============================================================
# BUILD EDITION (patched by build script)
# ============================================================

EDITION = Edition.FREE  # BUILD_MARKER: patched to Edition.PRO in Pro builds

# Runtime override (set by dev toggle operator)
_runtime_override: Edition | None = None

# Dev environment detection
_DEV_MARKER_PATH: str | None = None
_IS_DEV_ENV = False

try:
    import os
    _DEV_MARKER_PATH = os.path.join(os.path.dirname(__file__), ".dev_pro")
    _IS_DEV_ENV = os.path.exists(_DEV_MARKER_PATH)
    if _IS_DEV_ENV:
        EDITION = Edition.PRO
except Exception:
    pass


def is_dev_environment() -> bool:
    """Check if running in dev environment (has .dev_pro marker nearby)."""
    return _IS_DEV_ENV


def set_runtime_edition(edition: Edition | None) -> None:
    """Set runtime override for edition (dev use only)."""
    global _runtime_override
    _runtime_override = edition


# ============================================================
# FEATURE REGISTRY
# Extensible: add new features here as development continues
# ============================================================

class Feature(Enum):
    # --- FREE FEATURES ---
    RECORD_FLY = "record_fly"
    PATH_EXTRACT = "path_extract"
    PATH_EDIT = "path_edit"
    RIG_BUILD = "rig_build"
    MODE_DYNAMIC = "mode_dynamic"
    MODE_SIMPLE = "mode_simple"
    TRACKING_MANUAL = "tracking_manual"
    TRACKING_MATCH_RECORDING = "tracking_match_recording"
    BAKE = "bake"


# Map each feature to its required edition
FEATURE_EDITION = {
    Feature.RECORD_FLY: Edition.FREE,
    Feature.PATH_EXTRACT: Edition.FREE,
    Feature.PATH_EDIT: Edition.FREE,
    Feature.RIG_BUILD: Edition.FREE,
    Feature.MODE_DYNAMIC: Edition.FREE,
    Feature.MODE_SIMPLE: Edition.FREE,
    Feature.TRACKING_MANUAL: Edition.FREE,
    Feature.TRACKING_MATCH_RECORDING: Edition.FREE,
    Feature.BAKE: Edition.FREE,
}


# ============================================================
# EDITION QUERIES
# ============================================================

def get_edition() -> Edition:
    """Return the current edition (runtime override takes precedence)."""
    if _runtime_override is not None:
        return _runtime_override
    return EDITION


def is_pro() -> bool:
    """Check if Pro features are currently enabled."""
    return get_edition() == Edition.PRO


def is_feature_available(feature: Feature) -> bool:
    """Check if a specific feature is available in this build."""
    required = FEATURE_EDITION.get(feature, Edition.PRO)
    if required == Edition.FREE:
        return True
    return is_pro()


# ============================================================
# UI HELPERS
# ============================================================

def pro_label(text: str) -> str:
    """Append (Pro) suffix to label in Free builds."""
    return text if is_pro() else f"{text} (Pro)"


def should_show_pro_teaser(feature: Feature) -> bool:
    """Check if we should show Pro teaser UI for this feature."""
    return FEATURE_EDITION.get(feature) == Edition.PRO and not is_pro()
