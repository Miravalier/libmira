#!/usr/bin/env python3.7
import os
import re
import subprocess
from textwrap import dedent
from collections import namedtuple
from pathlib import Path


_dedent = dedent
def dedent(text):
    return _dedent(text).rstrip()


XMLNS = "http://www.w3.org/2000/svg"
SHADOW_FILTER = dedent("""\
    <filter id="shadow" height="300%" width="300%" x="-100%" y="-100%">
        <feFlood flood-color="rgba(0, 0, 0, 1)" result="flood"></feFlood>
        <feComposite in="flood" in2="SourceGraphic" operator="atop" result="composite"></feComposite>
        <feGaussianBlur in="composite" stdDeviation="1" result="blur"></feGaussianBlur>
        <feOffset dx="5" dy="5" result="offset"></feOffset>
        <feComposite in="SourceGraphic" in2="offset" operator="over"></feComposite>
    </filter>
""")

CIRCLE = 0
SQUARE = 1

FILE_SVG = 0
FILE_PNG = 1

RADIAL = 0
LINEAR = 1

SVG_PATTERN = re.compile(
    r'.*?<\s*svg[^>]*viewBox\s*=\s*"([^"]*)"[^>]*>(.*?)<\s*/svg\s*>.*?',
    re.DOTALL | re.I
)
PATH_PATTERN = re.compile(
    r'<\s*path[^>]*\sd="([^"]*)"[^>]*/?>',
    re.DOTALL | re.I
)


def clipPath(obj):
    return dedent("""\
        <clipPath id="fg-clip">
            {}
        </clipPath>
    """).format(
        indent(str(obj))
    )


def parse_paths(src):
    # If src is a file, read the contents
    try:
        data = Path(src).expanduser().read_text()
    except:
        data = src

    # Check for <path> inside <svg>
    svg_match = SVG_PATTERN.match(data)
    if not svg_match:
        raise ValueError("Malformed or missing input SVG data")

    x, y, width, height = svg_match.group(1).split(' ')
    paths = [m.group(1) for m in PATH_PATTERN.finditer(svg_match.group(2))]

    # Return path data
    return int(float(width)), int(float(height)), paths


def indent(text, indent=1, token='    '):
    token *= indent
    return text.replace("\n", "\n" + token)


def reference_of(obj):
    if isinstance(obj, str):
        return obj
    else:
        return obj.reference


CircleFields = ('cx', 'cy', 'r', 'fill')
class Circle(namedtuple("Circle", CircleFields)):
    def __str__(self):
        return '<circle cx="{}" cy="{}" r="{}" fill="{}"></circle>'.format(
            self.cx,
            self.cy,
            self.r,
            reference_of(self.fill)
        )


RectangleFields = ('x', 'y', 'width', 'height', 'rx', 'fill')
class Rectangle(namedtuple("Rectangle", RectangleFields)):
    def __str__(self):
        return '<rect x="{}" y="{}" width="{}" height="{}" rx="{}" fill="{}"></rect>'.format(
            self.x,
            self.y,
            self.width,
            self.height,
            self.rx,
            reference_of(self.fill)
        )


GradientFields = ('start', 'stop', 'shape', 'id')
class Gradient(namedtuple("Gradient", GradientFields)):
    def __str__(self):
        return dedent("""\
        {}
            {}
        {}
        """).format(
            self.xml_open,
            indent(self.xml_body),
            self.xml_close
        )

    @property
    def reference(self):
        return "url(#{})".format(self.id)

    @property
    def xml_open(self):
        if self.shape == RADIAL:
            return '<radialGradient id="{}">'.format(self.id)
        elif self.shape == LINEAR:
            return '<linearGradient id="{}">'.format(self.id)
        else:
            raise ValueError("Invalid gradient shape")

    @property
    def xml_body(self):
        return dedent("""\
            <stop offset="0%" stop-color="{}" stop-opacity="1"></stop>
            <stop offset="100%" stop-color="{}" stop-opacity="1"></stop>
        """).format(
            self.start,
            self.stop
        )

    @property
    def xml_close(self):
        if self.shape == RADIAL:
            return '</radialGradient>'
        elif self.shape == LINEAR:
            return '</linearGradient>'
        else:
            raise ValueError("Invalid gradient shape")


class SVG:
    def __init__(self, src, *,
                bg_shape=None,
                bg_fill=Gradient("#969696", "#646464", RADIAL, "gradient-bg"),
                fg_fill="#FFFFFF",
                shadow=True, clip=True,
            ):
        self.width, self.height, self.paths = parse_paths(src)
        self.bg_shape = bg_shape
        self.bg_fill = bg_fill
        self.fg_fill = fg_fill
        self.shadow = shadow
        self.clip = clip

    def __repr__(self):
        return "{}(fg={}, bg_shape={}, shadow={}, clip={})".format(
            type(self).__name__,
            repr(self.fg),
            repr(self.bg_shape),
            repr(self.shadow),
            repr(self.clip)
        )

    def __str__(self):
        template = dedent("""\
        {}
            {}
            {}
        {}
        """)
        return template.format(
            self.xml_open,
            indent(self.xml_header),
            indent(self.xml_body),
            self.xml_close
        )

    @property
    def xml_open(self):
        return '<svg xmlns="{}" viewBox="0 0 {} {}">'.format(
            XMLNS,
            self.width,
            self.height
        )

    @property
    def xml_header(self):
        defs = set()
        if self.clip:
            if self.bg_shape == SQUARE:
                defs.add(
                    clipPath(
                        Rectangle(4, 4, self.width - 8, self.height - 8, 0, "#FFFFFF")
                    )
                )
            elif self.bg_shape == CIRCLE:
                defs.add(
                    clipPath(
                        Circle(self.width // 2, self.height // 2, self.width // 2 - 8, "#FFFFFF")
                    )
                )
        if self.shadow:
            defs.add(SHADOW_FILTER)
        if isinstance(self.fg_fill, Gradient):
            defs.add(str(self.fg_fill))
        if isinstance(self.bg_fill, Gradient):
            defs.add(str(self.bg_fill))
        if defs:
            return dedent("""\
                <defs>
                    {}
                </defs>
            """).format(indent("\n".join(defs)))
        else:
            return "<defs></defs>"

    @property
    def xml_body(self):
        body = []

        # Add background
        if self.bg_shape == SQUARE:
            body.append(str(
                Rectangle(0, 0, self.width, self.height, 0, "#000000")
            ))
            body.append(str(
                Rectangle(4, 4, self.width - 8, self.height - 8, 0, reference_of(self.bg_fill))
            ))
        elif self.bg_shape == CIRCLE:
            body.append(str(
                Circle(
                    self.width // 2,
                    self.height // 2,
                    self.width // 2,
                    "#000000"
                )
            ))
            body.append(str(
                Circle(
                    self.width // 2,
                    self.height // 2,
                    self.width // 2 - 8,
                    reference_of(self.bg_fill)
                )
            ))

        # Add paths
        fg_attributes = ""
        if self.clip:
            fg_attributes += ' clip-path="url(#fg-clip)"'
        if self.shadow:
            fg_attributes += ' filter="url(#shadow)"'

        for path in self.paths:
            body.append('<path d="{}" fill="{}" fill-opacity="1"{}></path>'.format(
                path, reference_of(self.fg_fill), fg_attributes
            ))

        # Return body
        if body:
            return dedent("""\
                <g class="fg">
                    {}
                </g>
            """).format(indent("\n".join(body)))
        else:
            return '<g class="fg"></g>'

    @property
    def xml_close(self):
        return '</svg>'

    def output(self, path, filetype=None):
        path = Path(path).expanduser()
        if filetype is None:
            if path.suffix == ".png":
                filetype = FILE_PNG
            else:
                filetype = FILE_SVG

        if filetype == FILE_SVG:
            with open(path.with_suffix('.svg'), "w") as img:
                img.write(str(self))
        elif filetype == FILE_PNG:
            with open(path.with_suffix('.tmp'), "w") as svg:
                svg.write(str(self))
            subprocess.run([
                "convert",
                "svg:" + str(path.with_suffix(".tmp")),
                "png:" + str(path.with_suffix(".png"))
            ])
            path.with_suffix('.tmp').unlink()
        else:
            raise ValueError("Unknown file type")


if __name__ == '__main__':
    GRADIENT_PATTERN = re.compile("#?([0-9a-f]+):#?([0-9a-f]+)", re.I)
    COLOR_PATTERN = re.compile("#?([0-9a-f]+)", re.I)
    GID = 0
    def ArgumentColor(text):
        global GID
        GID += 1
        try:
            match = GRADIENT_PATTERN.match(text)
            return Gradient(
                match.group(1), match.group(2), RADIAL, "gradient-{}".format(GID)
            )
        except:
            return "#" + COLOR_PATTERN.match(text).group(1)


    ArgumentShapes = {
        's': SQUARE,
        'sq': SQUARE,
        'square': SQUARE,
        'r': SQUARE,
        'rect': SQUARE,
        'rectangle': SQUARE,
        'c': CIRCLE,
        'circle': CIRCLE,
        'n': None,
        'none': None,
        'stamp': None,
        '': None,
        'entity': CIRCLE,
        'ability': SQUARE
    }
    def ArgumentShape(text):
        return ArgumentShapes[text]

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('--fg', type=ArgumentColor, default='#FFFFFF')
    parser.add_argument('--bg', type=ArgumentColor, default='#969696:#646464')
    parser.add_argument('--shape', type=ArgumentShape, default=None)
    args = parser.parse_args()

    svg = SVG(
        args.input,
        fg_fill=args.fg,
        bg_fill=args.bg,
        bg_shape=args.shape
    )
    svg.output(args.output)
