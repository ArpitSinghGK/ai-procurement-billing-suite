#!/usr/bin/env python3
"""
generate_arch_diagram.py
========================
Turn a small JSON architecture spec into an animated architecture diagram, in
two formats from a single source of truth:

  1. assets/architecture.svg  -- animated SVG (SMIL). This is TEXT, so it pushes
     cleanly through the GitHub MCP connector AND it actually animates inside a
     GitHub README when referenced as <img src="assets/architecture.svg">
     (same technique used by readme-typing-svg and friends).

  2. assets/architecture.gif  -- animated GIF via Pillow. A raster you can attach
     directly to an Upwork / Freelancer proposal message. It is a BINARY file, so
     it can only be committed via a real `git push` (the MCP file APIs corrupt
     binaries). The README embeds the SVG; the GIF is a bonus artifact.

Both show the same "flowing data packets" effect as the reference the user liked
(cclank/lanshu-animated-architecture-diagram).

Usage
-----
    python3 generate_arch_diagram.py SPEC.json --outdir REPO/assets

    # SVG only (no Pillow needed):
    python3 generate_arch_diagram.py SPEC.json --outdir REPO/assets --no-gif

Spec format
-----------
    {
      "title": "Real-Time Lakehouse Pipeline",
      "theme": "dark",                     # "dark" (default) or "light"
      "nodes": [
        {"id": "kafka", "label": "Kafka",           "col": 0, "row": 1, "color": "#f97316"},
        {"id": "spark", "label": "Spark\nStreaming", "col": 1, "row": 1, "color": "#38bdf8"},
        {"id": "delta", "label": "Delta\nLake",      "col": 2, "row": 0, "color": "#a78bfa"},
        {"id": "api",   "label": "FastAPI",          "col": 2, "row": 2, "color": "#34d399"}
      ],
      "edges": [
        {"from": "kafka", "to": "spark", "label": "events"},
        {"from": "spark", "to": "delta", "label": "upsert"},
        {"from": "spark", "to": "api",   "label": "serve"}
      ]
    }

`col` (x) and `row` (y) place nodes on a grid; canvas size is derived from the
maxima. `color` is optional (a palette is cycled if omitted). `label` may contain
"\n" for line breaks.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

# ------------------------------------------------------------------ layout ---
NODE_W = 158
NODE_H = 74
GAP_X = 118
GAP_Y = 96
MARGIN = 92
TITLE_H = 62

PALETTE = ["#38bdf8", "#f97316", "#a78bfa", "#34d399", "#f472b6",
           "#facc15", "#60a5fa", "#fb7185", "#4ade80", "#c084fc"]

THEMES = {
    "dark":  {"bg": "#0d1117", "grid": "#161b22", "node_fill": "#161b22",
              "node_text": "#e6edf3", "edge": "#30363d", "edge_label": "#8b949e",
              "title": "#e6edf3"},
    "light": {"bg": "#ffffff", "grid": "#f2f4f7", "node_fill": "#ffffff",
              "node_text": "#1f2328", "edge": "#d0d7de", "edge_label": "#57606a",
              "title": "#1f2328"},
}


def load_spec(path):
    with open(path, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    if not spec.get("nodes"):
        sys.exit("spec error: at least one node is required")
    return spec


def build_geometry(spec):
    """Return (canvas_w, canvas_h, nodes_by_id, edges) with pixel coords."""
    nodes = {}
    max_col = max(n["col"] for n in spec["nodes"])
    max_row = max(n["row"] for n in spec["nodes"])
    for i, n in enumerate(spec["nodes"]):
        cx = MARGIN + n["col"] * (NODE_W + GAP_X) + NODE_W / 2
        cy = TITLE_H + MARGIN + n["row"] * (NODE_H + GAP_Y) + NODE_H / 2
        nodes[n["id"]] = {
            "id": n["id"],
            "label": n.get("label", n["id"]),
            "color": n.get("color") or PALETTE[i % len(PALETTE)],
            "cx": cx, "cy": cy,
        }
    width = MARGIN * 2 + (max_col + 1) * NODE_W + max_col * GAP_X
    height = TITLE_H + MARGIN * 2 + (max_row + 1) * NODE_H + max_row * GAP_Y
    edges = []
    for e in spec.get("edges", []):
        a, b = nodes.get(e["from"]), nodes.get(e["to"])
        if not a or not b:
            continue
        ax, ay = _border_anchor(a, b["cx"], b["cy"])
        bx, by = _border_anchor(b, a["cx"], a["cy"])
        edges.append({"a": (ax, ay), "b": (bx, by),
                      "label": e.get("label", ""), "color": a["color"]})
    return width, height, nodes, edges


def _border_anchor(node, tx, ty):
    """Point on `node`'s rectangle border facing target (tx, ty)."""
    cx, cy = node["cx"], node["cy"]
    hw, hh = NODE_W / 2, NODE_H / 2
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    if abs(dx) * hh >= abs(dy) * hw:            # exits left / right
        x = cx + math.copysign(hw, dx)
        y = cy + dy * (hw / max(abs(dx), 1e-6))
    else:                                       # exits top / bottom
        y = cy + math.copysign(hh, dy)
        x = cx + dx * (hh / max(abs(dy), 1e-6))
    return x, y


# --------------------------------------------------------------------- SVG ---
def render_svg(spec, path):
    t = THEMES.get(spec.get("theme", "dark"), THEMES["dark"])
    w, h, nodes, edges = build_geometry(spec)
    title = spec.get("title", "Architecture")
    P = []
    P.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'xmlns:xlink="http://www.w3.org/1999/xlink" '
             f'viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
             f'font-family="Segoe UI, Helvetica, Arial, sans-serif">')
    P.append('<defs><filter id="glow" x="-40%" y="-40%" width="180%" height="180%">'
             '<feGaussianBlur stdDeviation="3.2" result="b"/>'
             '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/>'
             '</feMerge></filter></defs>')
    P.append(f'<rect width="{w}" height="{h}" fill="{t["bg"]}"/>')
    P.append(f'<text x="{w/2:.0f}" y="38" fill="{t["title"]}" font-size="26" '
             f'font-weight="700" text-anchor="middle">{_esc(title)}</text>')

    # edges: dim base + flowing dashed overlay + gliding packets
    for i, e in enumerate(edges):
        (ax, ay), (bx, by) = e["a"], e["b"]
        d = f"M {ax:.1f} {ay:.1f} L {bx:.1f} {by:.1f}"
        pid = f"edge{i}"
        P.append(f'<path id="{pid}" d="{d}" fill="none" '
                 f'stroke="{t["edge"]}" stroke-width="2.4"/>')
        P.append(f'<path d="{d}" fill="none" stroke="{e["color"]}" '
                 f'stroke-width="2.4" stroke-linecap="round" '
                 f'stroke-dasharray="9 15" opacity="0.9">'
                 f'<animate attributeName="stroke-dashoffset" from="0" to="-24" '
                 f'dur="0.85s" repeatCount="indefinite"/></path>')
        P.append(_arrowhead(ax, ay, bx, by, e["color"]))
        for k in range(3):                       # 3 staggered packets per edge
            begin = f"{k * 0.5:.2f}s"
            P.append(f'<circle r="4.2" fill="{e["color"]}" filter="url(#glow)">'
                     f'<animateMotion dur="1.5s" begin="{begin}" '
                     f'repeatCount="indefinite" rotate="auto">'
                     f'<mpath xlink:href="#{pid}"/></animateMotion></circle>')
        if e["label"]:
            mx, my = (ax + bx) / 2, (ay + by) / 2
            P.append(f'<rect x="{mx-len(e["label"])*3.6-6:.1f}" y="{my-11:.1f}" '
                     f'width="{len(e["label"])*7.2+12:.1f}" height="18" rx="6" '
                     f'fill="{t["bg"]}" opacity="0.85"/>')
            P.append(f'<text x="{mx:.1f}" y="{my+3:.1f}" fill="{t["edge_label"]}" '
                     f'font-size="12" text-anchor="middle">{_esc(e["label"])}</text>')

    # nodes: rounded card + colored top accent + pulsing halo + label
    for n in nodes.values():
        x = n["cx"] - NODE_W / 2
        y = n["cy"] - NODE_H / 2
        P.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{NODE_W}" height="{NODE_H}" '
                 f'rx="14" fill="{t["node_fill"]}" stroke="{n["color"]}" '
                 f'stroke-width="2">'
                 f'<animate attributeName="stroke-width" values="2;3.4;2" '
                 f'dur="2.4s" repeatCount="indefinite"/></rect>')
        P.append(f'<rect x="{x+14:.1f}" y="{y-2:.1f}" width="{NODE_W-28}" height="4" '
                 f'rx="2" fill="{n["color"]}"/>')
        lines = str(n["label"]).split("\\n") if "\\n" in str(n["label"]) \
            else str(n["label"]).split("\n")
        n_lines = len(lines)
        for li, line in enumerate(lines):
            ly = n["cy"] + (li - (n_lines - 1) / 2) * 17 + 5
            P.append(f'<text x="{n["cx"]:.1f}" y="{ly:.1f}" fill="{t["node_text"]}" '
                     f'font-size="14.5" font-weight="600" '
                     f'text-anchor="middle">{_esc(line)}</text>')

    P.append('</svg>')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(P))
    return path


def _arrowhead(ax, ay, bx, by, color):
    ang = math.atan2(by - ay, bx - ax)
    size = 9
    p1 = (bx - size * math.cos(ang - 0.5), by - size * math.sin(ang - 0.5))
    p2 = (bx - size * math.cos(ang + 0.5), by - size * math.sin(ang + 0.5))
    return (f'<polygon points="{bx:.1f},{by:.1f} {p1[0]:.1f},{p1[1]:.1f} '
            f'{p2[0]:.1f},{p2[1]:.1f}" fill="{color}"/>')


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


# --------------------------------------------------------------------- GIF ---
def render_gif(spec, path, frames=42, duration=60):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  ! Pillow not installed -> skipping GIF "
              "(pip install pillow to enable). SVG still generated.",
              file=sys.stderr)
        return None

    t = THEMES.get(spec.get("theme", "dark"), THEMES["dark"])
    w, h, nodes, edges = build_geometry(spec)
    scale = 2                                    # supersample for crisp output
    W, H = w * scale, h * scale
    font = _load_font(int(14.5 * scale), ImageFont)
    font_title = _load_font(int(24 * scale), ImageFont)
    font_lbl = _load_font(int(12 * scale), ImageFont)

    imgs = []
    for f in range(frames):
        phase = f / frames
        im = Image.new("RGB", (W, H), t["bg"])
        d = ImageDraw.Draw(im)
        d.text((W / 2, 32 * scale), spec.get("title", "Architecture"),
               fill=t["title"], font=font_title, anchor="mm")

        for e in edges:
            (ax, ay), (bx, by) = e["a"], e["b"]
            ax, ay, bx, by = ax*scale, ay*scale, bx*scale, by*scale
            d.line([(ax, ay), (bx, by)], fill=t["edge"], width=int(2.4*scale))
            _draw_flow_dashes(d, ax, ay, bx, by, e["color"], phase, scale)
            _draw_arrow(d, ax, ay, bx, by, e["color"], scale)
            for k in range(3):                   # gliding packets
                p = (phase + k / 3.0) % 1.0
                px, py = ax + (bx - ax) * p, ay + (by - ay) * p
                r = 4.6 * scale
                d.ellipse([px-r, py-r, px+r, py+r], fill=e["color"])
            if e["label"]:
                mx, my = (ax + bx) / 2, (ay + by) / 2
                d.text((mx, my), e["label"], fill=t["edge_label"],
                       font=font_lbl, anchor="mm")

        for n in nodes.values():
            cx, cy = n["cx"]*scale, n["cy"]*scale
            hw, hh = (NODE_W/2)*scale, (NODE_H/2)*scale
            pulse = int((math.sin(phase * 2 * math.pi) * 0.5 + 0.5) * 1.4*scale)
            _rounded(d, cx-hw, cy-hh, cx+hw, cy+hh, 14*scale,
                     fill=t["node_fill"], outline=n["color"],
                     width=int(2*scale) + pulse)
            d.rectangle([cx-hw+14*scale, cy-hh-2*scale,
                         cx+hw-14*scale, cy-hh+2*scale], fill=n["color"])
            lines = str(n["label"]).replace("\\n", "\n").split("\n")
            for li, line in enumerate(lines):
                ly = cy + (li - (len(lines)-1)/2) * 17*scale
                d.text((cx, ly), line, fill=t["node_text"], font=font, anchor="mm")

        imgs.append(im.resize((w, h), Image.LANCZOS))

    imgs[0].save(path, save_all=True, append_images=imgs[1:], loop=0,
                 duration=duration, disposal=2, optimize=True)
    return path


def _draw_flow_dashes(d, ax, ay, bx, by, color, phase, scale):
    length = math.hypot(bx - ax, by - ay)
    if length < 1:
        return
    ux, uy = (bx - ax) / length, (by - ay) / length
    period = 24 * scale
    dash = 9 * scale
    off = -(phase * period)
    s = off
    while s < length:
        a = max(s, 0)
        b = min(s + dash, length)
        if b > 0:
            d.line([(ax + ux*a, ay + uy*a), (ax + ux*b, ay + uy*b)],
                   fill=color, width=int(2.4*scale))
        s += period


def _draw_arrow(d, ax, ay, bx, by, color, scale):
    ang = math.atan2(by - ay, bx - ax)
    size = 9 * scale
    p1 = (bx - size*math.cos(ang-0.5), by - size*math.sin(ang-0.5))
    p2 = (bx - size*math.cos(ang+0.5), by - size*math.sin(ang+0.5))
    d.polygon([(bx, by), p1, p2], fill=color)


def _rounded(d, x0, y0, x1, y1, r, fill, outline, width):
    try:
        d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill,
                            outline=outline, width=width)
    except AttributeError:                       # very old Pillow
        d.rectangle([x0, y0, x1, y1], fill=fill, outline=outline, width=width)


def _load_font(size, ImageFont):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf",
              "/System/Library/Fonts/Helvetica.ttc",
              "/Library/Fonts/Arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


# -------------------------------------------------------------------- main ---
def main():
    ap = argparse.ArgumentParser(description="Animated architecture diagram (SVG + GIF)")
    ap.add_argument("spec", help="path to architecture spec JSON")
    ap.add_argument("--outdir", default="assets", help="output directory")
    ap.add_argument("--no-gif", action="store_true", help="skip GIF (SVG only)")
    ap.add_argument("--name", default="architecture", help="base filename")
    args = ap.parse_args()

    spec = load_spec(args.spec)
    os.makedirs(args.outdir, exist_ok=True)
    svg = render_svg(spec, os.path.join(args.outdir, f"{args.name}.svg"))
    print(f"  + wrote {svg}")
    if not args.no_gif:
        gif = render_gif(spec, os.path.join(args.outdir, f"{args.name}.gif"))
        if gif:
            print(f"  + wrote {gif}")


if __name__ == "__main__":
    main()
