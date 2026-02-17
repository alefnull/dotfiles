# Node Tree Screenshot

Blender extension for creating screenshots of large node trees.

Large node trees in Blender often don't fit inside a single screen, or require zooming out to the point where labels become unreadable. This extension provides an operator that takes several screenshots of different sections of a node tree and then stitches them together into a single image.

## Usage

1. In a node editor, select the _View > Node Editor Screenshot_ menu entry.
2. Select the output image file in the file selector.

The operator will take a number of screenshots of every visible part of the node tree and write the combined image to the output file.

## Known Issues

* Hide Toolbar/Properties bar:
  The addon takes screenshots that include the toolbar and/or properties bar, which can get in the way of a clean screenshot. These areas cannot effectively be hidden by an operator using the Blender API. Make sure to hide these areas to get clean screenshots!
* It can be useful to make the node editor full-screen first. This results in fewer image tiles and can speed up the operator.
* Long node connections are faded out in the middle when the view is far from the start/end points. This can leave visual gaps in the middle of node connections, which cannot be prevented by the addon.


## Installing

Install the Python Image Library (PIL) module.

```python
cd <extension_folder>
pip download pillow --dest ./wheels --only-binary=:all: --python-version=3.11
```

When building the extension for distribution binary files for all platforms should be downloaded:

```python
pip download pillow --dest ./wheels --only-binary=:all: --python-version=3.11 --platform=macosx_11_0_arm64
pip download pillow --dest ./wheels --only-binary=:all: --python-version=3.11 --platform=manylinux_2_28_x86_64
pip download pillow --dest ./wheels --only-binary=:all: --python-version=3.11 --platform=win_amd64
```

For more information on building and installing Blender extensions see
https://docs.blender.org/manual/en/dev/advanced/extensions/getting_started.html#
