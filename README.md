# omaccy

Maccy (an open source clipboard manager for macOS) has ruined computers for me. I literally can't use one without an equivalent now. The default clipboard manager for Omarchy is pretty good but I was missing settings and the ability to pin items. And so here we are.

**omaccy** is a [Maccy](https://github.com/p0deje/Maccy)-style clipboard history for [Omarchy](https://omarchy.org) (Hyprland). It is one Python script: a small background daemon records everything you copy, and a keyboard-driven popup lets you search it and paste straight back into the window you were in.

## Features

- **History:** text and images, 200 items by default (configurable), with duplicates merged and moved back to the top.
- **Pinned favourites:** kept at the top or the bottom of the list, never dropped from history, each with its own `Alt+letter` shortcut.
- **Search:** type to filter, with matches shown in bold.
- **Numbered shortcuts:** `Ctrl+1`–`Ctrl+9` paste the first nine history items, like Maccy's `⌘1`–`⌘9`.
- **Preview panel:** shows the full text or a larger image, where it was copied from, when it was copied and how many times.
- **Paste straight in:** Enter pastes into the previous window, terminals included.
- **Private:** content that password managers mark as sensitive is skipped.
- **Themed:** colours come from the current Omarchy theme and update live when you switch themes. Every stock theme, light and dark, stays readable.
- **Settings window:** history size, paste behaviour, pinned position, preview, and whether to save images.

## Requirements

An Omarchy install already has all of these:

- Hyprland
- Python 3.11+ with `python-gobject`
- `gtk4` and `gtk4-layer-shell`
- `wl-clipboard` (for `wl-paste` and `wl-copy`)
- `wtype` (to paste)

On plain Arch:

```sh
sudo pacman -S python-gobject gtk4 gtk4-layer-shell wl-clipboard wtype
```

## Install

```sh
git clone https://github.com/JacksonFraser/omaccy ~/repos/omaccy
ln -s ~/repos/omaccy/omaccy ~/.local/bin/omaccy
```

Then add the following to your Hyprland config.

`~/.config/hypr/bindings.lua`:

```lua
o.bind("SUPER + SHIFT + V", "Clipboard history", "omaccy toggle")
```

`~/.config/hypr/autostart.lua`:

```lua
o.launch_on_start("omaccy")
```

`~/.config/hypr/looknfeel.lua` (blurs behind the popup, but not its shadow):

```lua
hl.layer_rule({ match = { namespace = "omaccy" }, blur = true, ignore_alpha = 0.5 })
```

`~/.config/hypr/hyprland.lua` (makes the settings window float):

```lua
o.window("^dev.omaccy.Omaccy$", { float = true, center = true })
```

Run `hyprctl reload`, then start the daemon once with `omaccy` or log out and back in.

Optionally, turn off Omarchy's built-in clipboard so only one history is recorded:

```sh
omarchy plugin disable omarchy.clipboard
```

## Usage

Press `SUPER + SHIFT + V`.

| Key | Action |
|---|---|
| Type | Search |
| `↑` / `↓`, `Ctrl+J` / `Ctrl+K` | Move |
| `Enter` | Paste into the previous window |
| `Shift+Enter` | Copy only, without pasting |
| `Ctrl+1`–`Ctrl+9` | Paste that history item |
| `Alt+letter` | Paste that pinned item |
| `Alt+P` | Pin or unpin the selected item |
| `Alt+Delete` | Remove the selected item |
| `Tab` / `Shift+Tab` | Move to the Clear / Settings / Quit menu and back |
| `Ctrl+,` | Settings (`Esc` returns to the list) |
| `Ctrl+Shift+Backspace` | Clear history (pinned items are kept) |
| `Esc` or click outside | Close |

If *Paste automatically* is turned off in Settings, `Enter` and `Shift+Enter` swap roles.

### Commands

```
omaccy            start the background daemon
omaccy toggle     show or hide the popup (starts the daemon if needed)
omaccy show       show the popup
omaccy settings   open the settings window
omaccy quit       stop the daemon
```

## Files

| Path | Contents |
|---|---|
| `~/.local/share/omaccy/history.json` | History and pinned items |
| `~/.local/share/omaccy/images/` | Copied images |
| `~/.config/omaccy/config.toml` | Settings (the Settings window writes it; you can also edit it by hand) |

## Theming

omaccy reads `~/.local/state/omarchy/current/theme/colors.toml` and uses Omarchy's monospace font. It adjusts colours where a theme's own pairs would be hard to read.

To preview omaccy in another theme without switching to it, run:

```sh
OMACCY_THEME_FILE=/usr/share/omarchy/themes/catppuccin-latte/colors.toml omaccy show
```

This opens a separate copy that doesn't record the clipboard. Close it with the same command, replacing `show` with `quit`.

## Uninstall

```sh
omaccy quit
rm ~/.local/bin/omaccy
rm -r ~/.local/share/omaccy ~/.config/omaccy
```

Then remove the four Hyprland lines above. If you turned off Omarchy's clipboard, turn it back on with `omarchy plugin enable omarchy.clipboard`.

## Thanks

To [Maccy](https://github.com/p0deje/Maccy) by Alex Rodionov, the clipboard manager this imitates, and to [Omarchy](https://omarchy.org) for its clipboard capture approach.

## License

[MIT](LICENSE)
