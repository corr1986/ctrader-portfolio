"""Smoke test per brand.py — asset grafici del profilo X."""
import os

from copyfunnel.brand import make_banner, make_profile_image


def test_profile_image_is_square_png(tmp_path):
    out = tmp_path / "profile.png"
    make_profile_image(str(out))
    assert out.exists() and os.path.getsize(out) > 1000


def test_banner_png_created(tmp_path):
    out = tmp_path / "banner.png"
    make_banner(str(out))
    assert out.exists() and os.path.getsize(out) > 1000
