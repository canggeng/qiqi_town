"""程序化低多边形几何体工具。

所有模型都由顶点色几何体拼成，不依赖外部模型或贴图。
"""

from __future__ import annotations

import math

from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    LineSegs,
    NodePath,
    TransparencyAttrib,
)

Color = tuple[float, float, float, float] | tuple[float, float, float]


def _rgba(color: Color, alpha: float = 1.0) -> tuple[float, float, float, float]:
    if len(color) == 4:
        return (float(color[0]), float(color[1]), float(color[2]), float(color[3]))
    return (float(color[0]), float(color[1]), float(color[2]), alpha)


def _new_writers(name: str, parent: NodePath) -> tuple[NodePath, GeomVertexData, GeomVertexWriter]:
    vdata = GeomVertexData(name, GeomVertexFormat.getV3n3c4(), Geom.UHStatic)
    vdata.setNumRows(0)
    vertex = GeomVertexWriter(vdata, "vertex")
    node = GeomNode(name)
    np = parent.attachNewNode(node)
    return np, vdata, vertex


def add_box(
    parent: NodePath,
    name: str,
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    color: Color,
    *,
    alpha: float = 1.0,
) -> NodePath:
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    cx, cy, cz = center
    faces = [
        ((1, 0, 0), [(hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz), (hx, -hy, hz)]),
        ((-1, 0, 0), [(-hx, hy, -hz), (-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz)]),
        ((0, 1, 0), [(hx, hy, -hz), (-hx, hy, -hz), (-hx, hy, hz), (hx, hy, hz)]),
        ((0, -1, 0), [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz)]),
        ((0, 0, 1), [(-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]),
        ((0, 0, -1), [(-hx, hy, -hz), (hx, hy, -hz), (hx, -hy, -hz), (-hx, -hy, -hz)]),
    ]
    np, vdata, vertex = _new_writers(name, parent)
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")
    prim = GeomTriangles(Geom.UHStatic)
    rgba = _rgba(color, alpha)
    index = 0
    for face_normal, corners in faces:
        for x, y, z in corners:
            vertex.addData3(cx + x, cy + y, cz + z)
            normal.addData3(*face_normal)
            color_w.addData4(*rgba)
        prim.addVertices(index, index + 1, index + 2)
        prim.addVertices(index, index + 2, index + 3)
        index += 4
    geom = Geom(vdata)
    geom.addPrimitive(prim)
    np.node().addGeom(geom)
    if alpha < 1.0 or rgba[3] < 1.0:
        np.setTransparency(TransparencyAttrib.MAlpha)
    return np


def add_sphere(
    parent: NodePath,
    name: str,
    center: tuple[float, float, float],
    radius: float,
    color: Color,
    *,
    rings: int = 12,
    segments: int = 18,
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
    alpha: float = 1.0,
) -> NodePath:
    np, vdata, vertex = _new_writers(name, parent)
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")
    prim = GeomTriangles(Geom.UHStatic)
    rgba = _rgba(color, alpha)
    sx, sy, sz = scale

    def point(theta: float, phi: float) -> tuple[float, float, float]:
        x = math.sin(theta) * math.cos(phi)
        y = math.sin(theta) * math.sin(phi)
        z = math.cos(theta)
        return (x * sx, y * sy, z * sz)

    index = 0
    grid: list[list[int]] = []
    for r in range(rings + 1):
        theta = math.pi * r / rings
        row: list[int] = []
        for s in range(segments + 1):
            phi = 2 * math.pi * s / segments
            nx, ny, nz = point(theta, phi)
            vertex.addData3(center[0] + nx * radius, center[1] + ny * radius, center[2] + nz * radius)
            normal.addData3(nx, ny, nz)
            color_w.addData4(*rgba)
            row.append(index)
            index += 1
        grid.append(row)

    for r in range(rings):
        for s in range(segments):
            a = grid[r][s]
            b = grid[r][s + 1]
            c = grid[r + 1][s + 1]
            d = grid[r + 1][s]
            if r != 0:
                prim.addVertices(a, d, b)
            if r != rings - 1:
                prim.addVertices(b, d, c)
    geom = Geom(vdata)
    geom.addPrimitive(prim)
    np.node().addGeom(geom)
    if alpha < 1.0 or rgba[3] < 1.0:
        np.setTransparency(TransparencyAttrib.MAlpha)
    return np


def add_cylinder(
    parent: NodePath,
    name: str,
    base_center: tuple[float, float, float],
    radius_bottom: float,
    radius_top: float,
    height: float,
    color: Color,
    *,
    segments: int = 16,
    alpha: float = 1.0,
) -> NodePath:
    np, vdata, vertex = _new_writers(name, parent)
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")
    prim = GeomTriangles(Geom.UHStatic)
    rgba = _rgba(color, alpha)
    cx, cy, cz = base_center
    index = 0

    ring_bottom: list[int] = []
    ring_top: list[int] = []
    for s in range(segments):
        phi = 2 * math.pi * s / segments
        nx, ny = math.cos(phi), math.sin(phi)
        vertex.addData3(cx + nx * radius_bottom, cy + ny * radius_bottom, cz)
        normal.addData3(nx, ny, 0.0)
        color_w.addData4(*rgba)
        ring_bottom.append(index)
        index += 1
        vertex.addData3(cx + nx * radius_top, cy + ny * radius_top, cz + height)
        normal.addData3(nx, ny, 0.0)
        color_w.addData4(*rgba)
        ring_top.append(index)
        index += 1

    for s in range(segments):
        s2 = (s + 1) % segments
        b0, t0 = ring_bottom[s], ring_top[s]
        b1, t1 = ring_bottom[s2], ring_top[s2]
        prim.addVertices(b0, b1, t1)
        prim.addVertices(b0, t1, t0)

    # 顶盖
    if radius_top > 0:
        center_idx = index
        vertex.addData3(cx, cy, cz + height)
        normal.addData3(0, 0, 1)
        color_w.addData4(*rgba)
        index += 1
        for s in range(segments):
            s2 = (s + 1) % segments
            prim.addVertices(center_idx, ring_top[s], ring_top[s2])
    # 底盖
    if radius_bottom > 0:
        center_idx = index
        vertex.addData3(cx, cy, cz)
        normal.addData3(0, 0, -1)
        color_w.addData4(*rgba)
        index += 1
        for s in range(segments):
            s2 = (s + 1) % segments
            prim.addVertices(center_idx, ring_bottom[s2], ring_bottom[s])

    geom = Geom(vdata)
    geom.addPrimitive(prim)
    np.node().addGeom(geom)
    if alpha < 1.0 or rgba[3] < 1.0:
        np.setTransparency(TransparencyAttrib.MAlpha)
    return np


def add_disc(
    parent: NodePath,
    name: str,
    center: tuple[float, float, float],
    radius: float,
    color: Color,
    *,
    segments: int = 24,
    alpha: float = 1.0,
) -> NodePath:
    np, vdata, vertex = _new_writers(name, parent)
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")
    prim = GeomTriangles(Geom.UHStatic)
    rgba = _rgba(color, alpha)
    cx, cy, cz = center
    vertex.addData3(cx, cy, cz)
    normal.addData3(0, 0, 1)
    color_w.addData4(*rgba)
    for s in range(segments + 1):
        phi = 2 * math.pi * s / segments
        vertex.addData3(cx + math.cos(phi) * radius, cy + math.sin(phi) * radius, cz)
        normal.addData3(0, 0, 1)
        color_w.addData4(*rgba)
    for s in range(segments):
        prim.addVertices(0, s + 1, s + 2)
    geom = Geom(vdata)
    geom.addPrimitive(prim)
    np.node().addGeom(geom)
    if alpha < 1.0 or rgba[3] < 1.0:
        np.setTransparency(TransparencyAttrib.MAlpha)
    return np


def add_pyramid(
    parent: NodePath,
    name: str,
    center: tuple[float, float, float],
    base_size: tuple[float, float],
    height: float,
    color: Color,
    *,
    alpha: float = 1.0,
) -> NodePath:
    cx, cy, cz = center
    hx, hy = base_size[0] / 2, base_size[1] / 2
    apex = (cx, cy, cz + height)
    base = [(cx - hx, cy - hy, cz), (cx + hx, cy - hy, cz), (cx + hx, cy + hy, cz), (cx - hx, cy + hy, cz)]
    faces = [
        (base[0], base[1], apex, (0, -1, 0)),
        (base[1], base[2], apex, (1, 0, 0)),
        (base[2], base[3], apex, (0, 1, 0)),
        (base[3], base[0], apex, (-1, 0, 0)),
    ]
    np, vdata, vertex = _new_writers(name, parent)
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")
    prim = GeomTriangles(Geom.UHStatic)
    rgba = _rgba(color, alpha)
    index = 0
    for a, b, c, n in faces:
        for p in (a, b, c):
            vertex.addData3(*p)
            normal.addData3(*n)
            color_w.addData4(*rgba)
        prim.addVertices(index, index + 1, index + 2)
        index += 3
    # 底面
    for p in (base[3], base[2], base[1], base[0]):
        vertex.addData3(*p)
        normal.addData3(0, 0, -1)
        color_w.addData4(*rgba)
    prim.addVertices(index, index + 1, index + 2)
    prim.addVertices(index, index + 2, index + 3)
    geom = Geom(vdata)
    geom.addPrimitive(prim)
    np.node().addGeom(geom)
    if alpha < 1.0 or rgba[3] < 1.0:
        np.setTransparency(TransparencyAttrib.MAlpha)
    return np


def add_line(
    parent: NodePath,
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    color: Color,
    *,
    thickness: float = 1.5,
) -> NodePath:
    segs = LineSegs(name)
    segs.setThickness(thickness)
    segs.setColor(*_rgba(color))
    segs.moveTo(*start)
    segs.drawTo(*end)
    node = segs.create()
    np = parent.attachNewNode(node)
    return np


def set_flat_shading(np: NodePath) -> NodePath:
    """让几何体使用平直法线观感；当前顶点法线由构建函数控制。"""
    return np


def apply_tint(np: NodePath, color: tuple[float, float, float, float]) -> NodePath:
    np.setColorScale(*color)  # type: ignore[arg-type]
    return np
