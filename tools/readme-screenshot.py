#!/usr/bin/env python3
"""Render the README screenshot from sample data.

Runs a throwaway omaccy instance with its own temporary history (sample items
only), draws the popup and preview straight to a PNG inside GTK — nothing is
captured from the screen — and puts it on a gradient in the theme's colours.

  tools/readme-screenshot.py [theme-name] [output.png]

Defaults: tokyo-night, docs/screenshot.png. Needs ImageMagick (`magick`).
"""

import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = sys.argv[1] if len(sys.argv) > 1 else "tokyo-night"
OUTPUT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "docs", "screenshot.png"))
SCALE = 2

LAYER_LIB = "/usr/lib/libgtk4-layer-shell.so"
if "libgtk4-layer-shell" not in os.environ.get("LD_PRELOAD", ""):
    os.environ["LD_PRELOAD"] = LAYER_LIB
    os.execv(sys.executable, [sys.executable] + sys.argv)

theme_file = next((p for p in (
    os.path.expanduser(f"~/.config/omarchy/themes/{THEME}/colors.toml"),
    f"/usr/share/omarchy/themes/{THEME}/colors.toml",
) if os.path.exists(p)), None)
if not theme_file:
    sys.exit(f"no colors.toml for theme {THEME!r}")

# Isolate everything omaccy reads or writes before importing it.
sandbox = tempfile.mkdtemp(prefix="omaccy-shot-")
os.environ["XDG_DATA_HOME"] = os.path.join(sandbox, "data")
os.environ["XDG_CONFIG_HOME"] = os.path.join(sandbox, "config")
os.environ["OMACCY_THEME_FILE"] = theme_file

from importlib.machinery import SourceFileLoader  # noqa: E402
from importlib.util import module_from_spec, spec_from_loader  # noqa: E402

loader = SourceFileLoader("omaccy", os.path.join(ROOT, "omaccy"))
omaccy = module_from_spec(spec_from_loader("omaccy", loader))
loader.exec_module(omaccy)
Gtk, GLib, Graphene = omaccy.Gtk, omaccy.GLib, omaccy.Graphene
LayerShell = omaccy.LayerShell

SNIPPET = '''def fib(n):
    """Return the nth Fibonacci number."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
'''

# (text or image, source app, minutes ago, copies); newest first.
HISTORY = [
    ("git log --oneline --graph --decorate -20", "com.mitchellh.ghostty", 1, 3),
    (SNIPPET, "code", 4, 1),
    ("IMAGE", "chromium", 9, 1),
    ("https://github.com/p0deje/Maccy", "chromium", 16, 2),
    ("omarchy theme set tokyo-night", "com.mitchellh.ghostty", 25, 1),
    ("Meeting moved to 3:30pm, same link as before", "chromium", 41, 1),
    ("#7aa2f7", "code", 58, 4),
    ("sudo pacman -Syu", "com.mitchellh.ghostty", 75, 6),
    ("~/.config/hypr/bindings.lua", "org.gnome.Nautilus", 110, 2),
    ("The quick brown fox jumps over the lazy dog", "chromium", 180, 1),
    ("docker compose up -d --build", "com.mitchellh.ghostty", 240, 5),
]
PINNED = [
    ("ssh deploy@staging.example.com", "com.mitchellh.ghostty"),
    ("Thanks! I'll take a look this afternoon and get back to you.", "chromium"),
]
SELECT = 1  # history index shown in the preview (the code snippet)


def build_history(store, palette):
    now = time.time()
    image = os.path.join(sandbox, "sample.png")
    a, b = omaccy._hex(palette["accent"]), omaccy._hex(omaccy._mix(palette["accent"], palette["bg"], 0.7))
    subprocess.run(["magick", "-size", "1000x1600", f"gradient:{a}-{b}", "-rotate", "90", image], check=True)
    for text, app, minutes, count in reversed(HISTORY):
        if text == "IMAGE":
            with open(image, "rb") as f:
                store.add_image(f.read(), "image/png", app)
        else:
            store.add_text(text, app)
        item = store.items[0]
        item.update(count=count, last=now - minutes * 60, first=now - minutes * 60 - 3600 * (count - 1))
    for n, (text, app) in enumerate(PINNED):
        store.add_text(text, app)
        store.items[0].update(first=now - 86400 * 20, last=now - 86400 * (n + 2), count=12 - n * 5)
        store.toggle_pin(store.items[0])
    store.save()


def render(app):
    popup = app.popup
    # Keep the throwaway window out of the way: under other windows, no keyboard.
    LayerShell.set_layer(popup, LayerShell.Layer.BOTTOM)
    LayerShell.set_keyboard_mode(popup, LayerShell.KeyboardMode.NONE)
    build_history(app.store, omaccy.load_palette(theme_file))
    popup.open()

    def select_and_preview():
        history = [r.item for r in popup.rows if not r.item.get("pinned")]
        popup.select(popup.rows.index(next(r for r in popup.rows if r.item is history[SELECT])))
        popup.fill_preview(history[SELECT])
        popup._set_preview_visible(True)
        GLib.timeout_add(700, snapshot)
        return False

    def snapshot():
        # The full-screen backdrop, not just the cards, so shadows aren't clipped.
        stage = popup.backdrop
        width, height = stage.get_width(), stage.get_height()
        snap = Gtk.Snapshot()
        snap.scale(SCALE, SCALE)
        Gtk.WidgetPaintable.new(stage).snapshot(snap, width, height)
        node = snap.to_node()
        texture = popup.get_renderer().render_texture(node, node.get_bounds())
        raw = os.path.join(sandbox, "raw.png")
        texture.save_to_png(raw)
        compose(raw)
        app.quit()
        return False

    GLib.timeout_add(600, select_and_preview)


def compose(raw):
    palette = omaccy.load_palette(theme_file)
    top = omaccy._hex(omaccy._mix(palette["bg"], palette["accent"], 0.35))
    bottom = omaccy._hex(palette["bg"])
    cut = os.path.join(sandbox, "cut.png")
    # Trim the empty screen around the cards (and the spacer that keeps the
    # card centred), keeping a margin so the soft shadow edges survive.
    subprocess.run(["magick", raw, "-channel", "A", "-fuzz", "1%", "-trim", "+repage", cut], check=True)
    w, h = (int(v) for v in subprocess.run(["magick", "identify", "-format", "%w %h", cut],
                                            capture_output=True, text=True, check=True).stdout.split())
    pad = 40 * SCALE
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    subprocess.run(["magick", "-size", f"{w + pad * 2}x{h + pad * 2}", f"gradient:{top}-{bottom}",
                    cut, "-gravity", "center", "-composite", "-depth", "8", "-strip", OUTPUT], check=True)
    print(OUTPUT)


class ShotApp(omaccy.App):
    def do_command_line(self, cmdline):
        render(self)
        return 0


if __name__ == "__main__":
    ShotApp().run([sys.argv[0]])
