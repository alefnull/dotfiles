# Sidebar Tab Search (Blender Add-on)

Quickly search and switch between Sidebar (N-Panel) tabs in Blender's 3D Viewport.

![Screenshot](sidebar-tab-search_ico_256px.png)

## Why Two Search Modes? (Popup vs Popover)

This add-on features two distinct search engines tailored to different needs:

### 1. Quick Search Popup (Shift + Alt + T)

- **Keyboard-First Workflow**: Designed for maximum speed without taking your hands off the keyboard.
- **Instant Interaction**: Open, type, Enter. The popup closes automatically as soon as a tab is selected.
- **Efficiency**: Best for users who know exactly where they want to go and want to get there in a fraction of a second.

### 2. Management Popover (Ctrl + Shift + Alt + T)

- **The Central Manager**: A persistent interface launched from the header icon or shortcut.
- **Complex Tasks**: Ideal for operations that the "Quick" popup cannot support, such as:
  - Managing **Favorites** and checking **History** visually.
  - Setting and editing **Custom Aliases**.
  - Accessing the **Right-Click context menu** (Quickly jumping to addon preferences or folder).
- **Persistent View**: Stays open while you work, allowing you to switch between multiple tabs or explore the sidebar structure without repeatedly reopening the search.

## Core Features

- **Deep Search**: Not just tabs! Find any internal panel or tool within the sidebar.
- **Instant Tab Switching**: Clicking a result automatically opens the sidebar and switches to the correct tab.
- **Custom Aliases**: Right-click any result to set a custom nickname. Search works for both original names and aliases!
- **Adjustable UI Width**: Change the popover width directly in preferences (10-40 units) with real-time updates.
- **Quick Favorites**: Toggle favorites with a single click using the discrete star icons in search results.
- **Header Integration**: Minimalist magnifying glass icon in the 3D View header for easy access.
- **Search History**: Automatically prioritizes your recent interactions (when "Recent" sort is active).
- **Favorites Backup**: Export your favorite list to JSON and import it back in the preferences.
- **Context Menu Utilities (4.2+)**: Right-click any result for advanced management:
  - **Add/Remove Favorites**.
  - **Set/Edit Custom Alias**.
  - **Open in Preferences**: Jump straight to that addon's settings.
  - **Open in Explorer**: Open the source folder of the addon.

## Usage

1. **Invoke**: Click the magnifying glass icon or use the shortcuts mentioned above.
2. **Search**: Start typing (minimum 2 characters).
3. **Switch**: Click on any result to instantly navigate to that sidebar tab.
4. **Manage**: Use the Right-Click menu for advanced options.

## Compatibility

- **Blender 4.2+ - 5.0+** (Fully compatible with legacy and Extension-based installations).
- Universal support for search and tab switching across all versions.

> [!IMPORTANT]
> **Blender 5.0+ Note**: Starting with version 5.0, Blender changed the default behavior of menus and popovers—they no longer close automatically when the mouse leaves.
> To restore the classic behavior (auto-closing on mouse leave), go to **Edit > Preferences > Interface > Menus** and enable **"Close Menus on Leave"**.

## Installation

1. Download the `sidebar_tab_search.zip`.
2. In Blender: **Edit > Preferences > Get Extensions**.
3. Click the gear/arrow icon and select **Install from Disk...**.
4. Select the `.zip` file.
