"""
AutoCam - module constants.

Defines identifiers shared across the add-on:
- ROOT_ID: computed add-on root package id for cross-module lookups.
- MASTER_COLL: name of the master collection that holds AutoCam rigs.

"""


ROOT_ID = __package__.rsplit(".", 1)[0]
MASTER_COLL = "AutoCamRigs"
