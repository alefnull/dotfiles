===============================================================================
AutoCam 2.0 - Intuitive Camera Tools for Blender
===============================================================================

Built for artists, AutoCam simplifies cinematic camera animation in Blender.
Record natural movements, generate clean editable paths, and drive robust rigs,
without interrupting your creative flow.


-------------------------------------------------------------------------------
CORE FEATURES
-------------------------------------------------------------------------------

• POV Camera Recording:
  Capture smooth viewport moves in real time like playing a video game.

• Camera Path Extraction:
  Instantly convert camera path into editable Bezier/Poly/NURBS curves.

• One-Click Camera Rigs:
  Build a full rig with intuitive, animator-friendly controls.

• Keyframable Speed (forward / pause / reverse): 
  Positive, zero, or negative values to time your dolly precisely.

• Easy Cleanup:
  Remove AutoCam data and restore camera state when you’re done.


-------------------------------------------------------------------------------
WHAT'S NEW IN 2.0
-------------------------------------------------------------------------------

• One-Click Baking:
  Convert AutoCam rigs into plain keyframes for rendering, exporting, etc.

• Rig Mode Switch:
  Use Simple for dependable results, or Dynamic for flexible speed control. 

• Tracking Settings:
  Aim cameras more easily with cleaner, less manual adjustment.

• UI Overhaul:
  Context-aware panels, clear tooltips, and smart defaults for a smooth workflow.

• Improved Stability:
  Significant bug fixes and reliability improvements overall.


-------------------------------------------------------------------------------
REQUIREMENTS
-------------------------------------------------------------------------------

- Blender 4.0 or newer  (when installed as an Addon)
- Blender 4.2 or newer (when installed as an Extension)


-------------------------------------------------------------------------------
INSTALLATION  (Blender 4.x Extensions)
-------------------------------------------------------------------------------

1. Download  AutoCam_2-0-6.zip   (do NOT unzip).
2. In Blender: Edit  >  Preferences  >  Add-ons  >  Install
3. Select the ZIP, then enable the "AutoCam" extension.
4. (Optional) Tweak default preferences.
5. Find AutoCam in the 3D View *N-panel* under the "AutoCam" tab.

Updating? Disable and remove the older AutoCam extension, restart Blender, 
then install the new ZIP.


-------------------------------------------------------------------------------
QUICK START  (about 60 seconds)
-------------------------------------------------------------------------------

 1) Add a camera
    (Shift + A > Camera)

 2) Record  
    AutoCam panel > "Start Recording"
    (Fly with WASDQE + mouse; press Esc or Mouse Click to stop)

 3) Generate Curve  
    Select Animated Camera > Click "Generate Curve". 
    • Switch between Bezier, Poly, or NURBS curve types.
    • Use Edit Mode to update the path, then click "Apply Path Settings".
    • Simplify curve with "Tolerance" value.

 4) Generate Rig  
    Click "Generate Rig", then press Play. 
    • Switch Rig Mode: Simple for compatibility. Dynamic for realtime speed control.
    • Adjust Tracking: Switch between Manual and Match Recording (free).
    • Use multiple rigs in the same scene with independent timing.

 5) Bake to Keyframes  
    "Bake" to convert AutoCam motion into plain keyframes for final tweaks,
    rendering or exporting to other DCCs.


-------------------------------------------------------------------------------
DOCUMENTATION & SUPPORT
-------------------------------------------------------------------------------

  • Documentation:
    https://renderrides.gitbook.io/autocam
  • Email:
    support@renderrides.com
  • Website:
    https://www.renderrides.com

  Socials & community
  ───────────────────
  YouTube: https://youtube.com/@RenderRides
  Instagram: https://instagram.com/renderrides
  X / Twitter: https://x.com/RenderRides
  Patreon: https://patreon.com/renderrides
  Gumroad: https://gumroad.com/renderrides
  BlenderMarket: https://blendermarket.com/creators/renderrides
  Discord: https://discord.gg/XHAAbvm


-------------------------------------------------------------------------------
CHANGELOG
-------------------------------------------------------------------------------

2.0.6 — 2026-01-03
Fixed:
• Path Extraction: Camera animation detection now works reliably with Blender
  5.x layered actions and NLA-based animation.

Improved:
• UI Cleanup: Removed placeholder Pro feature items for a cleaner, more
  focused Free experience.
• Bake Settings: Made the popup more compact without losing functionality.

2.0.5 — 2025-11-24
Compatibility:
• Now supports Blender 5.0 while maintaining backwards compatibility back to
  Blender 4.2.

Fixed:
• Recording Cursor: The mouse cursor no longer gets stuck or hits a boundary
  while recording.
• Recording Exit: You can now cleanly finish recording by pressing Escape,
  Left Click, or Right Click.

Improved:
• Match Recording: Settings are now more responsive and intuitive to use.

2.0.4 — 2025-10-15
Changed:
• Dynamic rigs now read speed as distance-per-second, so timing stays consistent
  when the curve is extended/retracted.
• Simple and Dynamic rigs now keep independent speed values, so keying one mode
  no longer indicates the other's Speed slider as animated.
Fixed:
• Simple mode path follow preserves its keyframes when you rebuild or toggle
  modes; animation data is serialized and restored automatically.
• Dynamic mode now supports auto-keying, allowing users to quickly prototype
  camera animations in realtime.

2.0.3 — 2025-09-25
Changed:
• Standardized every operator, panel, and helper prefix to AUTOCAM_, updating
  bpy.ops identifiers and helper utilities to the autocam namespace for clearer
  branding.
Fixed:
• Fly Record no longer traps the cursor when canceling; removing the GRAB_CURSOR
  flag lets the pointer return immediately after dismissing confirmation.

2.0.2 — 2025-09-16
Fixed:
• Dynamic rigs no longer freeze after reopening a .blend. The rig builder now
  stamps a persistent ID on new rigs so Dynamic mode resumes correctly on load.
Note:
• If you built a rig in 2.0.1 or earlier and it still freezes after reopening,
  rebuild once with "Generate Rig" to stamp the ID. After that, reloads will be stable.

2.0.1 — 2025-09-04
Fixed:
• Aim preset “Recorded Rotations” renamed to “Match Recording.”
• Rig builder now seeds arc table, sets start frame, and refreshes view layer.
• Match Recording starts at frame 1, refreshes view layer, and runs a safe try/except.

2.0.0 — 2025-09-02
Added:
• One-Click Baking to convert rigs into plain keyframes for rendering, exporting, etc.
• Rig Mode Switch between native Blender constraints & AutoCam constraints.
• Tracking Settings to aim cameras more easily with cleaner, less manual adjustment.
• Context-aware panels, clear tooltips, and smart defaults for a smooth workflow.
Changed:
• Curve generation now auto-applies path settings (incl. default tolerance).
• Labels, menu order, and tooltips simplified for clarity.
Fixed:
• Reduced stutter on newly generated rigs.
• More robust enable/disable and registration; multiple minor stability fixes.
Compatibility:
• Blender 4.0+ supported; Extension install path available on 4.2+.
• Scenes from 1.x should continue to load; if not, regenerate the rig.

1.1.2 – 2025-06-18
  • Consolidated object properties into a single PropertyGroup.
  • Preferences registration fixed for 4.x extension installs.

1.1.1 – 2025-06-15
  • Re-packaged as a proper Blender 4.x Extension.
  • Internal code clean-up.
  • No new end-user features; a maintenance release focused on stability.

1.1.0 – 2025-05-14
  • Key-framable negative & zero speed (reverse / pause).
  • Removal of "Interpolation" dropdown. 
  • Removal of "Sync Speed to Keyframe" button.
  • Supports multiple rigs per scene (independent handlers).
  • Arc-length cache for smooth, constant motion on any spline type.
  • Stable reload: handler guard, hard speed limits, duplicate-helper cleanup.

1.0.0 – 2025-05-06
  • First public release.


-------------------------------------------------------------------------------
LICENSE
-------------------------------------------------------------------------------

AutoCam is free software, licensed under the GNU General Public License (GPL)
version 3 or later. You may use, modify, and redistribute it under those terms.
See GPL-3.0.txt for the full license.

Copyright © 2025 Agniv Duarah (RenderRides)
