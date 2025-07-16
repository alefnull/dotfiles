import os
import qute_colors

qutewal_dynamic_loading = True

home = os.getenv('HOME')
daemon_relative = '.config/qutebrowser/qutewald.py'
colors_relative = '.config/qutebrowser/qute_colors.py'
daemon_absolute = os.path.join(home, daemon_relative)
colors_absolute = os.path.join(home, colors_relative)

background = qute_colors.background
foreground = qute_colors.foreground
cursor = qute_colors.cursor
alpha = qute_colors.alpha
black = qute_colors.color0
white = qute_colors.color7
gray = qute_colors.color8
red = qute_colors.color1
green = qute_colors.color2
yellow = qute_colors.color3
blue = qute_colors.color4
magenta = qute_colors.color5
cyan = qute_colors.color6

# Background color of the completion widget category headers.
# Type: QssColor
c.colors.completion.category.bg = background

# Bottom border color of the completion widget category headers.
# Type: QssColor
c.colors.completion.category.border.bottom = background

# Top border color of the completion widget category headers.
# Type: QssColor
c.colors.completion.category.border.top = background

# Foreground color of completion widget category headers.
# Type: QtColor
c.colors.completion.category.fg = foreground

# Background color of the completion widget for even rows.
# Type: QssColor
c.colors.completion.even.bg = background

# Background color of the completion widget for odd rows.
# Type: QssColor
c.colors.completion.odd.bg = background

# Text color of the completion widget.
# Type: QtColor
c.colors.completion.fg = foreground

# Background color of the selected completion item.
# Type: QssColor
c.colors.completion.item.selected.bg = gray

# Bottom border color of the selected completion item.
# Type: QssColor
c.colors.completion.item.selected.border.bottom = background

# Top border color of the completion widget category headers.
# Type: QssColor
c.colors.completion.item.selected.border.top = background

# Foreground color of the selected completion item.
# Type: QtColor
c.colors.completion.item.selected.fg = foreground

# Foreground color of the matched text in the completion.
# Type: QssColor
c.colors.completion.match.fg = yellow

# Color of the scrollbar in completion view
# Type: QssColor
c.colors.completion.scrollbar.bg = background

# Color of the scrollbar handle in completion view.
# Type: QssColor
c.colors.completion.scrollbar.fg = gray

# Background color for the download bar.
# Type: QssColor
c.colors.downloads.bar.bg = background

# Background color for downloads with errors.
# Type: QtColor
c.colors.downloads.error.bg = red

# Foreground color for downloads with errors.
# Type: QtColor
c.colors.downloads.error.fg = foreground

# Color gradient stop for download backgrounds.
# Type: QtColor
c.colors.downloads.stop.bg = cyan

# Color gradient interpolation system for download backgrounds.
# Type: ColorSystem
# Valid values:
#   - rgb: Interpolate in the RGB color system.
#   - hsv: Interpolate in the HSV color system.
#   - hsl: Interpolate in the HSL color system.
#   - none: Don't show a gradient.
c.colors.downloads.system.bg = 'none'

# Background color for hints. Note that you can use a `rgba(...)` value
# for transparency.
# Type: QssColor
c.colors.hints.bg = yellow

# Font color for hints.
# Type: QssColor
c.colors.hints.fg = background

# Font color for the matched part of hints.
# Type: QssColor
c.colors.hints.match.fg = blue

# Background color of the keyhint widget.
# Type: QssColor
c.colors.keyhint.bg = background

# Text color for the keyhint widget.
# Type: QssColor
c.colors.keyhint.fg = foreground

# Highlight color for keys to complete the current keychain.
# Type: QssColor
c.colors.keyhint.suffix.fg = yellow

# Background color of an error message.
# Type: QssColor
c.colors.messages.error.bg = red

# Border color of an error message.
# Type: QssColor
c.colors.messages.error.border = red

# Foreground color of an error message.
# Type: QssColor
c.colors.messages.error.fg = foreground

# Background color of an info message.
# Type: QssColor
c.colors.messages.info.bg = blue

# Border color of an info message.
# Type: QssColor
c.colors.messages.info.border = blue

# Foreground color an info message.
# Type: QssColor
c.colors.messages.info.fg = foreground

# Background color of a warning message.
# Type: QssColor
c.colors.messages.warning.bg = red

# Border color of a warning message.
# Type: QssColor
c.colors.messages.warning.border = red

# Foreground color a warning message.
# Type: QssColor
c.colors.messages.warning.fg = foreground

# Background color for prompts.
# Type: QssColor
c.colors.prompts.bg = background

# # Border used around UI elements in prompts.
# # Type: String
c.colors.prompts.border = '1px solid ' + background

# Foreground color for prompts.
# Type: QssColor
c.colors.prompts.fg = foreground

# Background color for the selected item in filename prompts.
# Type: QssColor
c.colors.prompts.selected.bg = magenta

# Background color of the statusbar in caret mode.
# Type: QssColor
c.colors.statusbar.caret.bg = cyan

# Foreground color of the statusbar in caret mode.
# Type: QssColor
c.colors.statusbar.caret.fg = cursor

# Background color of the statusbar in caret mode with a selection.
# Type: QssColor
c.colors.statusbar.caret.selection.bg = cyan

# Foreground color of the statusbar in caret mode with a selection.
# Type: QssColor
c.colors.statusbar.caret.selection.fg = foreground

# Background color of the statusbar in command mode.
# Type: QssColor
c.colors.statusbar.command.bg = background

# Foreground color of the statusbar in command mode.
# Type: QssColor
c.colors.statusbar.command.fg = foreground

# Background color of the statusbar in private browsing + command mode.
# Type: QssColor
c.colors.statusbar.command.private.bg = background

# Foreground color of the statusbar in private browsing + command mode.
# Type: QssColor
c.colors.statusbar.command.private.fg = foreground

# Background color of the statusbar in insert mode.
# Type: QssColor
c.colors.statusbar.insert.bg = green

# Foreground color of the statusbar in insert mode.
# Type: QssColor
c.colors.statusbar.insert.fg = background

# Background color of the statusbar.
# Type: QssColor
c.colors.statusbar.normal.bg = background

# Foreground color of the statusbar.
# Type: QssColor
c.colors.statusbar.normal.fg = foreground

# Background color of the statusbar in passthrough mode.
# Type: QssColor
c.colors.statusbar.passthrough.bg = blue

# Foreground color of the statusbar in passthrough mode.
# Type: QssColor
c.colors.statusbar.passthrough.fg = foreground

# Background color of the statusbar in private browsing mode.
# Type: QssColor
c.colors.statusbar.private.bg = background

# Foreground color of the statusbar in private browsing mode.
# Type: QssColor
c.colors.statusbar.private.fg = foreground

# Background color of the progress bar.
# Type: QssColor
c.colors.statusbar.progress.bg = foreground

# Foreground color of the URL in the statusbar on error.
# Type: QssColor
c.colors.statusbar.url.error.fg = red

# Default foreground color of the URL in the statusbar.
# Type: QssColor
c.colors.statusbar.url.fg = foreground

# Foreground color of the URL in the statusbar for hovered links.
# Type: QssColor
c.colors.statusbar.url.hover.fg = blue

# Foreground color of the URL in the statusbar on successful load
# (http).
# Type: QssColor
c.colors.statusbar.url.success.http.fg = foreground

# Foreground color of the URL in the statusbar on successful load
# (https).
# Type: QssColor
c.colors.statusbar.url.success.https.fg = gray

# Foreground color of the URL in the statusbar when there's a warning.
# Type: QssColor
c.colors.statusbar.url.warn.fg = red

# Background color of the tab bar.
# Type: QtColor
c.colors.tabs.bar.bg = background

# Background color of unselected even tabs.
# Type: QtColor
c.colors.tabs.even.bg = background

# Foreground color of unselected even tabs.
# Type: QtColor
c.colors.tabs.even.fg = foreground

# Color for the tab indicator on errors.
# Type: QtColor
c.colors.tabs.indicator.error = red

# Color gradient start for the tab indicator.
# Type: QtColor
# c.colors.tabs.indicator.start = magenta

# Color gradient end for the tab indicator.
# Type: QtColor
# c.colors.tabs.indicator.stop = red

# Color gradient interpolation system for the tab indicator.
# Type: ColorSystem
# Valid values:
#   - rgb: Interpolate in the RGB color system.
#   - hsv: Interpolate in the HSV color system.
#   - hsl: Interpolate in the HSL color system.
#   - none: Don't show a gradient.
c.colors.tabs.indicator.system = 'none'

# Background color of unselected odd tabs.
# Type: QtColor
c.colors.tabs.odd.bg = background

# Foreground color of unselected odd tabs.
# Type: QtColor
c.colors.tabs.odd.fg = foreground

# Background color of selected even tabs.
# Type: QtColor
c.colors.tabs.selected.even.bg = gray

# Foreground color of selected even tabs.
# Type: QtColor
c.colors.tabs.selected.even.fg = foreground

# Background color of selected odd tabs.
# Type: QtColor
c.colors.tabs.selected.odd.bg = gray

# Foreground color of selected odd tabs.
# Type: QtColor
c.colors.tabs.selected.odd.fg = foreground

# Background color for webpages if unset (or empty to use the theme's
# color)
# Type: QtColor
c.colors.webpage.bg = foreground

if qutewal_dynamic_loading or bool(os.getenv('QUTEWAL_DYNAMIC_LOADING')):
    import signal
    import subprocess
    import prctl

    # start iqutefy to refresh colors on the fly
    qutewald = subprocess.Popen(
        [daemon_absolute, colors_absolute],
        preexec_fn=lambda: prctl.set_pdeathsig(signal.SIGTERM))

# Autogenerated config.py
#
# NOTE: config.py is intended for advanced users who are comfortable
# with manually migrating the config file on qutebrowser upgrades. If
# you prefer, you can also configure qutebrowser using the
# :set/:bind/:config-* commands without having to write a config.py
# file.
#
# Documentation:
#   qute://help/configuring.html
#   qute://help/settings.html

# Change the argument to True to still load settings configured via autoconfig.yml
config.load_autoconfig(True)

# Always restore open sites when qutebrowser is reopened. Without this
# option set, `:wq` (`:quit --save`) needs to be used to save open tabs
# (and restore them), while quitting qutebrowser in any other way will
# not save/restore the session. By default, this will save to the
# session which was last loaded. This behavior can be customized via the
# `session.default_name` setting.
# Type: Bool
c.auto_save.session = True

# Automatically start playing `<video>` elements.
# Type: Bool
c.content.autoplay = False

# Which cookies to accept. With QtWebEngine, this setting also controls
# other features with tracking capabilities similar to those of cookies;
# including IndexedDB, DOM storage, filesystem API, service workers, and
# AppCache. Note that with QtWebKit, only `all` and `never` are
# supported as per-domain values. Setting `no-3rdparty` or `no-
# unknown-3rdparty` per-domain on QtWebKit will have the same effect as
# `all`. If this setting is used with URL patterns, the pattern gets
# applied to the origin/first party URL of the page making the request,
# not the request URL. With QtWebEngine 5.15.0+, paths will be stripped
# from URLs, so URL patterns using paths will not match. With
# QtWebEngine 5.15.2+, subdomains are additionally stripped as well, so
# you will typically need to set this setting for `example.com` when the
# cookie is set on `somesubdomain.example.com` for it to work properly.
# To debug issues with this setting, start qutebrowser with `--debug
# --logfilter network --debug-flag log-cookies` which will show all
# cookies being set.
# Type: String
# Valid values:
#   - all: Accept all cookies.
#   - no-3rdparty: Accept cookies from the same origin only. This is known to break some sites, such as GMail.
#   - no-unknown-3rdparty: Accept cookies from the same origin only, unless a cookie is already set for the domain. On QtWebEngine, this is the same as no-3rdparty.
#   - never: Don't accept cookies at all.
config.set('content.cookies.accept', 'all', 'chrome-devtools://*')

# Which cookies to accept. With QtWebEngine, this setting also controls
# other features with tracking capabilities similar to those of cookies;
# including IndexedDB, DOM storage, filesystem API, service workers, and
# AppCache. Note that with QtWebKit, only `all` and `never` are
# supported as per-domain values. Setting `no-3rdparty` or `no-
# unknown-3rdparty` per-domain on QtWebKit will have the same effect as
# `all`. If this setting is used with URL patterns, the pattern gets
# applied to the origin/first party URL of the page making the request,
# not the request URL. With QtWebEngine 5.15.0+, paths will be stripped
# from URLs, so URL patterns using paths will not match. With
# QtWebEngine 5.15.2+, subdomains are additionally stripped as well, so
# you will typically need to set this setting for `example.com` when the
# cookie is set on `somesubdomain.example.com` for it to work properly.
# To debug issues with this setting, start qutebrowser with `--debug
# --logfilter network --debug-flag log-cookies` which will show all
# cookies being set.
# Type: String
# Valid values:
#   - all: Accept all cookies.
#   - no-3rdparty: Accept cookies from the same origin only. This is known to break some sites, such as GMail.
#   - no-unknown-3rdparty: Accept cookies from the same origin only, unless a cookie is already set for the domain. On QtWebEngine, this is the same as no-3rdparty.
#   - never: Don't accept cookies at all.
config.set('content.cookies.accept', 'all', 'devtools://*')

# Default encoding to use for websites. The encoding must be a string
# describing an encoding such as _utf-8_, _iso-8859-1_, etc.
# Type: String
c.content.default_encoding = 'utf-8'

# Limit fullscreen to the browser window (does not expand to fill the
# screen).
# Type: Bool
c.content.fullscreen.window = True

# Request websites to minimize non-essentials animations and motion.
# This results in the `prefers-reduced-motion` CSS media query to
# evaluate to `reduce` (rather than `no-preference`). On Windows, if
# this setting is set to False, the system-wide animation setting is
# considered.
# Type: Bool
c.content.prefers_reduced_motion = True

# Value to send in the `Accept-Language` header. Note that the value
# read from JavaScript is always the global value.
# Type: String
config.set('content.headers.accept_language', '', 'https://matchmaker.krunker.io/*')

# User agent to send.  The following placeholders are defined:  *
# `{os_info}`: Something like "X11; Linux x86_64". * `{webkit_version}`:
# The underlying WebKit version (set to a fixed value   with
# QtWebEngine). * `{qt_key}`: "Qt" for QtWebKit, "QtWebEngine" for
# QtWebEngine. * `{qt_version}`: The underlying Qt version. *
# `{upstream_browser_key}`: "Version" for QtWebKit, "Chrome" for
# QtWebEngine. * `{upstream_browser_version}`: The corresponding
# Safari/Chrome version. * `{upstream_browser_version_short}`: The
# corresponding Safari/Chrome   version, but only with its major
# version. * `{qutebrowser_version}`: The currently running qutebrowser
# version.  The default value is equal to the default user agent of
# QtWebKit/QtWebEngine, but with the `QtWebEngine/...` part removed for
# increased compatibility.  Note that the value read from JavaScript is
# always the global value.
# Type: FormatString
#config.set('content.headers.user_agent', 'Mozilla/5.0 ({os_info}; rv:136.0) Gecko/20100101 Firefox/139.0', 'https://accounts.google.com/*')

# Load images automatically in web pages.
# Type: Bool
config.set('content.images', True, 'chrome-devtools://*')

# Load images automatically in web pages.
# Type: Bool
config.set('content.images', True, 'devtools://*')

# Enable JavaScript.
# Type: Bool
config.set('content.javascript.enabled', True, 'chrome-devtools://*')

# Enable JavaScript.
# Type: Bool
config.set('content.javascript.enabled', True, 'devtools://*')

# Enable JavaScript.
# Type: Bool
config.set('content.javascript.enabled', True, 'chrome://*/*')

# Enable JavaScript.
# Type: Bool
config.set('content.javascript.enabled', True, 'qute://*/*')

# Allow locally loaded documents to access remote URLs.
# Type: Bool
config.set('content.local_content_can_access_remote_urls', True, 'file:///home/alef/.local/share/qutebrowser/userscripts/*')

# Allow locally loaded documents to access other local URLs.
# Type: Bool
config.set('content.local_content_can_access_file_urls', False, 'file:///home/alef/.local/share/qutebrowser/userscripts/*')

# What notification presenter to use for web notifications. Note that
# not all implementations support all features of notifications: - The
# `qt` and `systray` options only support showing one notification at
# the time   and ignore the `tag` option to replace existing
# notifications. - The `herbe` option only supports showing one
# notification at the time and doesn't   show icons. - The `messages`
# option doesn't show icons and doesn't support the `click` and
# `close` events.
# Type: String
# Valid values:
#   - auto: Tries `libnotify`, `systray` and `messages`, uses the first one available without showing error messages.
#   - qt: Use Qt's native notification presenter, based on a system tray icon. Switching from or to this value requires a restart of qutebrowser.
#   - libnotify: Shows messages via DBus in a libnotify-compatible way. If DBus isn't available, falls back to `systray` or `messages`, but shows an error message.
#   - systray: Use a notification presenter based on a systray icon. Falls back to `libnotify` or `messages` if not systray is available. This is a reimplementation of the `qt` setting value, but with the possibility to switch to it at runtime.
#   - messages: Show notifications as qutebrowser messages. Most notification features aren't available.
#   - herbe: (experimental!) Show notifications using herbe (github.com/dudik/herbe). Most notification features aren't available.
c.content.notifications.presenter = 'libnotify'

# Allow websites to request persistent storage quota via
# `navigator.webkitPersistentStorage.requestQuota`.
# Type: BoolAsk
# Valid values:
#   - true
#   - false
#   - ask
c.content.persistent_storage = 'ask'

# Enable plugins in Web pages.
# Type: Bool
c.content.plugins = True

# Which interfaces to expose via WebRTC.
# Type: String
# Valid values:
#   - all-interfaces: WebRTC has the right to enumerate all interfaces and bind them to discover public interfaces.
#   - default-public-and-private-interfaces: WebRTC should only use the default route used by http. This also exposes the associated default private address. Default route is the route chosen by the OS on a multi-homed endpoint.
#   - default-public-interface-only: WebRTC should only use the default route used by http. This doesn't expose any local addresses.
#   - disable-non-proxied-udp: WebRTC should only use TCP to contact peers or servers unless the proxy server supports UDP. This doesn't expose any local addresses either.
c.content.webrtc_ip_handling_policy = 'default-public-interface-only'

# Height (in pixels or as percentage of the window) of the completion.
# Type: PercOrInt
c.completion.height = '33%'

# When to show the autocompletion window.
# Type: String
# Valid values:
#   - always: Whenever a completion is available.
#   - auto: Whenever a completion is requested.
#   - never: Never.
c.completion.show = 'always'

# Shrink the completion to be smaller than the configured size if there
# are no scrollbars.
# Type: Bool
c.completion.shrink = True

# Prompt the user for the download location. If set to false,
# `downloads.location.directory` will be used.
# Type: Bool
c.downloads.location.prompt = False

# What to display in the download filename input.
# Type: String
# Valid values:
#   - path: Show only the download path.
#   - filename: Show only download filename.
#   - both: Show download path and filename.
c.downloads.location.suggestion = 'both'

# Editor (and arguments) to use for the `edit-*` commands. The following
# placeholders are defined:  * `{file}`: Filename of the file to be
# edited. * `{line}`: Line in which the caret is found in the text. *
# `{column}`: Column in which the caret is found in the text. *
# `{line0}`: Same as `{line}`, but starting from index 0. * `{column0}`:
# Same as `{column}`, but starting from index 0.
# Type: ShellCommand
c.editor.command = ['alacritty', '-e', 'nvim', '{file}', '-c', 'normal {line}G{column0}l']

# Command (and arguments) to use for selecting a single file in forms.
# The command should write the selected file path to the specified file
# or stdout. The following placeholders are defined: * `{}`: Filename of
# the file to be written to. If not contained in any argument, the
# standard output of the command is read instead.
# Type: ShellCommand
c.fileselect.single_file.command = ['alacritty', '-e', 'ranger', '--choosefile={}']

# Command (and arguments) to use for selecting multiple files in forms.
# The command should write the selected file paths to the specified file
# or to stdout, separated by newlines. The following placeholders are
# defined: * `{}`: Filename of the file to be written to. If not
# contained in any argument, the   standard output of the command is
# read instead.
# Type: ShellCommand
c.fileselect.multiple_files.command = ['alacritty', '-e', 'ranger', '--choosefiles={}']

# Command (and arguments) to use for selecting a single folder in forms.
# The command should write the selected folder path to the specified
# file or stdout. The following placeholders are defined: * `{}`:
# Filename of the file to be written to. If not contained in any
# argument, the   standard output of the command is read instead.
# Type: ShellCommand
c.fileselect.folder.command = ['alacritty', '-e', 'ranger', '--choosedir={}']

# Enable smooth scrolling for web pages. Note smooth scrolling does not
# work with the `:scroll-px` command.
# Type: Bool
c.scrolling.smooth = True

# List of widgets displayed in the statusbar.
# Type: List of StatusbarWidget
# Valid values:
#   - url: Current page URL.
#   - scroll: Percentage of the current page position like `10%`.
#   - scroll_raw: Raw percentage of the current page position like `10`.
#   - history: Display an arrow when possible to go back/forward in history.
#   - search_match: A match count when searching, e.g. `Match [2/10]`.
#   - tabs: Current active tab, e.g. `2`.
#   - keypress: Display pressed keys when composing a vi command.
#   - progress: Progress bar for the current page loading.
#   - text:foo: Display the static text after the colon, `foo` in the example.
#   - clock: Display current time. The format can be changed by adding a format string via `clock:...`. For supported format strings, see https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes[the Python datetime documentation].
c.statusbar.widgets = ['keypress', 'search_match', 'url', 'scroll', 'history', 'tabs', 'progress']

# When to show the tab bar.
# Type: String
# Valid values:
#   - always: Always show the tab bar.
#   - never: Always hide the tab bar.
#   - multiple: Hide the tab bar if only one tab is open.
#   - switching: Show the tab bar when switching tabs.
c.tabs.show = 'always'

# Alignment of the text inside of tabs.
# Type: TextAlignment
# Valid values:
#   - left
#   - right
#   - center
c.tabs.title.alignment = 'left'

# Format to use for the tab title. The following placeholders are
# defined:  * `{perc}`: Percentage as a string like `[10%]`. *
# `{perc_raw}`: Raw percentage, e.g. `10`. * `{current_title}`: Title of
# the current web page. * `{title_sep}`: The string `" - "` if a title
# is set, empty otherwise. * `{index}`: Index of this tab. *
# `{aligned_index}`: Index of this tab padded with spaces to have the
# same   width. * `{relative_index}`: Index of this tab relative to the
# current tab. * `{id}`: Internal tab ID of this tab. * `{scroll_pos}`:
# Page scroll position. * `{host}`: Host of the current web page. *
# `{backend}`: Either `webkit` or `webengine` * `{private}`: Indicates
# when private mode is enabled. * `{current_url}`: URL of the current
# web page. * `{protocol}`: Protocol (http/https/...) of the current web
# page. * `{audio}`: Indicator for audio/mute status.
# Type: FormatString
c.tabs.title.format = '{audio}{current_title}'

# Hide the window decoration.  This setting requires a restart on
# Wayland.
# Type: Bool
c.window.hide_decoration = True

# Format to use for the window title. The same placeholders like for
# `tabs.title.format` are defined.
# Type: FormatString
c.window.title_format = '{current_title}'

# Background color of the statusbar in insert mode.
# Type: QssColor
c.colors.statusbar.insert.bg = 'darkgreen'

# Background color for webpages if unset (or empty to use the theme's
# color).
# Type: QtColor
c.colors.webpage.bg = None

# Value to use for `prefers-color-scheme:` for websites. The "light"
# value is only available with QtWebEngine 5.15.2+. On older versions,
# it is the same as "auto". The "auto" value is broken on QtWebEngine
# 5.15.2 due to a Qt bug. There, it will fall back to "light"
# unconditionally.
# Type: String
# Valid values:
#   - auto: Use the system-wide color scheme setting.
#   - light: Force a light theme.
#   - dark: Force a dark theme.
c.colors.webpage.preferred_color_scheme = 'dark'

# Render all web contents using a dark theme. On QtWebEngine < 6.7, this
# setting requires a restart and does not support URL patterns, only the
# global setting is applied. Example configurations from Chromium's
# `chrome://flags`: - "With simple HSL/CIELAB/RGB-based inversion": Set
# `colors.webpage.darkmode.algorithm` accordingly, and   set
# `colors.webpage.darkmode.policy.images` to `never`.  - "With selective
# image inversion": qutebrowser default settings.
# Type: Bool
c.colors.webpage.darkmode.enabled = True

# Which algorithm to use for modifying how colors are rendered with dark
# mode. The `lightness-cielab` value was added with QtWebEngine 5.14 and
# is treated like `lightness-hsl` with older QtWebEngine versions.
# Type: String
# Valid values:
#   - lightness-cielab: Modify colors by converting them to CIELAB color space and inverting the L value. Not available with Qt < 5.14.
#   - lightness-hsl: Modify colors by converting them to the HSL color space and inverting the lightness (i.e. the "L" in HSL).
#   - brightness-rgb: Modify colors by subtracting each of r, g, and b from their maximum value.
c.colors.webpage.darkmode.algorithm = 'lightness-cielab'

# Contrast for dark mode. This only has an effect when
# `colors.webpage.darkmode.algorithm` is set to `lightness-hsl` or
# `brightness-rgb`.
# Type: Float
c.colors.webpage.darkmode.contrast = 0.0

# Which images to apply dark mode to.
# Type: String
# Valid values:
#   - always: Apply dark mode filter to all images.
#   - never: Never apply dark mode filter to any images.
#   - smart: Apply dark mode based on image content. Not available with Qt 5.15.0.
#   - smart-simple: On QtWebEngine 6.6, use a simpler algorithm for smart mode (based on numbers of colors and transparency), rather than an ML-based model. Same as 'smart' on older QtWebEnigne versions.
c.colors.webpage.darkmode.policy.images = 'never'

# Default font families to use. Whenever "default_family" is used in a
# font setting, it's replaced with the fonts listed here. If set to an
# empty value, a system-specific monospace default is used.
# Type: List of Font, or Font
c.fonts.default_family = ['NotoMono Nerd Font']

# Default font size to use. Whenever "default_size" is used in a font
# setting, it's replaced with the size listed here. Valid values are
# either a float value with a "pt" suffix, or an integer value with a
# "px" suffix.
# Type: String
c.fonts.default_size = '12pt'

# Map keys to other keys, so that they are equivalent in all modes. When
# the key used as dictionary-key is pressed, the binding for the key
# used as dictionary-value is invoked instead. This is useful for global
# remappings of keys, for example to map <Ctrl-[> to <Escape>. NOTE:
# This should only be used if two keys should always be equivalent, i.e.
# for things like <Enter> (keypad) and <Return> (non-keypad). For normal
# command bindings, qutebrowser works differently to vim: You always
# bind keys to commands, usually via `:bind` or `config.bind()`. Instead
# of using this setting, consider finding the command a key is bound to
# (e.g. via `:bind gg`) and then binding the same command to the desired
# key. Note that when a key is bound (via `bindings.default` or
# `bindings.commands`), the mapping is ignored.
# Type: Dict
c.bindings.key_mappings = {'<Ctrl+6>': '<Ctrl+^>', '<Ctrl+Enter>': '<Ctrl+Return>', '<Ctrl+i>': '<Tab>', '<Ctrl+j>': '<Return>', '<Ctrl+m>': '<Return>', '<Ctrl+[>': '<Escape>', '<Enter>': '<Return>', '<Shift+Enter>': '<Return>', '<Shift+Return>': '<Return>'}
