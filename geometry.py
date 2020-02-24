#!/usr/bin/env python3.7
from collections import namedtuple
from math import radians, atan, sin, cos, pi

WIDTH_CONSTANT = pi / 360


class Point(namedtuple('Point', ('x','y'))):
    pass


class Cone:
    def __init__(self, width, length, rotation=0):
        self.width = width
        self.length = length
        self.rotation = rotation

    def __contains__(self, point):
        return (
            self.minimum <= atan(
                (point.x * self.sin_theta + point.y * self.cos_theta)
                /
                abs(point.x * self.cos_theta - point.y * self.sin_theta)
            )
            and
            self.radius_squared >= (
                point.x * point.x + point.y * point.y
            )
        )

    def __repr__(self):
        return "{}(width={}, length={}, rotation={})".format(
            self.__class__.__name__,
            self._width, self._length, self._rotation
        )

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, rotation):
        rotation %= 360
        self._rotation = rotation
        radian_rotation = radians(rotation)
        self.sin_theta = sin(radian_rotation)
        self.cos_theta = cos(radian_rotation)

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, width):
        width = min(width, 360)
        width = max(width, 0)
        self._width = width
        self.minimum = (180 - width) * WIDTH_CONSTANT

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, length):
        length = max(length, 0)
        self._length = length
        self.radius_squared = length * length

    def rotate(self, degrees):
        self.rotation += degrees


def main():
    import sys
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("width", type=float)
    parser.add_argument("length", type=float)
    parser.add_argument("rotation", type=float)
    parser.add_argument("x", type=float)
    parser.add_argument("y", type=float)
    args = parser.parse_args()

    cone = Cone(args.width, args.length, args.rotation)
    point = Point(args.x, args.y)
    if point in cone:
        print("[\x1B[32mTRUE\x1B[0m] {} is in {}".format(point, cone))
    else:
        print("[\x1B[31mFALSE\x1B[0m] {} is not in {}".format(point, cone))


if __name__ == '__main__':
    main()
