"""程序生成的圆角矩形贴图，供 DirectGUI 面板和按钮使用。"""

from __future__ import annotations

from functools import lru_cache

from direct.gui.DirectGui import DirectButton, DirectFrame
from panda3d.core import (
    PNMImage,
    SamplerState,
    Texture,
    TransparencyAttrib,
)


@lru_cache(maxsize=128)
def rounded_texture(width: float, height: float, radius: float = 0.03) -> Texture:
    """生成与控件长宽比一致的白色圆角贴图，颜色由 frameColor 控制。"""
    aspect = max(0.05, width / max(height, 1e-4))
    if aspect >= 1:
        px_w = 256
        px_h = max(12, round(px_w / aspect))
    else:
        px_h = 256
        px_w = max(12, round(px_h * aspect))
    px_w = min(1024, px_w)
    px_h = min(1024, px_h)
    r = max(2.0, radius / max(width, height) * max(px_w, px_h))

    image = PNMImage(px_w, px_h, 4)
    image.fill(1.0)
    inner_x0 = r
    inner_y0 = r
    inner_x1 = px_w - r
    inner_y1 = px_h - r
    samples = 4
    for y in range(px_h):
        for x in range(px_w):
            covered = 0
            for sy in range(samples):
                for sx in range(samples):
                    px = x + (sx + 0.5) / samples
                    py = y + (sy + 0.5) / samples
                    cx = min(max(px, inner_x0), inner_x1)
                    cy = min(max(py, inner_y0), inner_y1)
                    if (px - cx) ** 2 + (py - cy) ** 2 <= r * r:
                        covered += 1
            image.setAlpha(x, y, covered / (samples * samples))

    texture = Texture(f"roundrect_{px_w}x{px_h}_{r:.1f}")
    texture.load(image)
    texture.setMagfilter(SamplerState.FT_linear)
    texture.setMinfilter(SamplerState.FT_linear)
    texture.setWrapU(SamplerState.WM_clamp)
    texture.setWrapV(SamplerState.WM_clamp)
    return texture


def round_widget(widget: DirectFrame, *, radius: float = 0.03) -> None:
    """给已有 DirectFrame/DirectButton 加上圆角贴图。"""
    try:
        left, right, bottom, top = widget["frameSize"]
    except (KeyError, TypeError, ValueError):
        return
    width = abs(right - left)
    height = abs(top - bottom)
    if width <= 0 or height <= 0:
        return
    widget["frameTexture"] = rounded_texture(width, height, min(radius, height * 0.4))
    widget.setTransparency(TransparencyAttrib.MAlpha)


def round_button(button: DirectButton, *, radius: float = 0.03) -> None:
    round_widget(button, radius=radius)
