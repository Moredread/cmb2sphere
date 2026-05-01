"""Tests for the synthetic mode and the colored output formats."""
import os
import tempfile
import zipfile
import re

import numpy as np
import healpy as hp
import pytest
import trimesh

import cmb2sphere as c2s


@pytest.fixture
def tmp_path_factory_ext():
    created = []

    def make(ext):
        fd, path = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        created.append(path)
        return path

    yield make
    for p in created:
        if os.path.exists(p):
            os.remove(p)


# --- synthetic generator -------------------------------------------------

def test_synthetic_map_has_correct_shape():
    nside = 16
    m = c2s.synthetic_cmb_map(nside, seed=0)
    assert m.shape == (hp.nside2npix(nside),)


def test_synthetic_map_is_reproducible_under_seed():
    a = c2s.synthetic_cmb_map(16, seed=123)
    b = c2s.synthetic_cmb_map(16, seed=123)
    assert np.array_equal(a, b)


def test_synthetic_map_amplitude_is_realistic():
    # ~100 uK RMS is the right order of magnitude for CMB anisotropies.
    m = c2s.synthetic_cmb_map(64, seed=42)
    rms = float(np.std(m))
    assert 1e-5 < rms < 1e-3, f"RMS {rms} outside expected ~1e-4 K range"


# --- vectorized fix_orientation ------------------------------------------

def test_fix_orientation_makes_all_normals_outward():
    nside = 16
    m = c2s.synthetic_cmb_map(nside, seed=1)
    _, points = c2s.build_displaced_sphere(m, nside)
    faces = c2s.build_faces(points)
    c2s.fix_orientation(faces, points)

    a = points[faces[:, 0]]
    b = points[faces[:, 1]]
    c = points[faces[:, 2]]
    signs = np.einsum("ij,ij->i", np.cross(a - c, a - b), a)
    assert np.all(signs <= 0.0)


# --- output formats ------------------------------------------------------

def _build_small_mesh(nside=16):
    m = c2s.synthetic_cmb_map(nside, seed=7)
    alm = hp.map2alm(m)
    smoothed = hp.alm2map(alm, nside, fwhm=0.05)
    vertices, points = c2s.build_displaced_sphere(smoothed, nside)
    faces = c2s.build_faces(points)
    c2s.fix_orientation(faces, points)
    return vertices, faces, smoothed


def test_ply_output_carries_per_vertex_color(tmp_path_factory_ext):
    out = tmp_path_factory_ext(".ply")
    vertices, faces, scalars = _build_small_mesh()
    c2s.save(out, vertices, faces, scalars=scalars)

    reloaded = trimesh.load(out)
    assert reloaded.visual.vertex_colors.shape == (len(vertices), 4)
    # More than one unique color means the colormap actually got applied.
    unique = {tuple(c) for c in reloaded.visual.vertex_colors.tolist()}
    assert len(unique) > 1


def test_3mf_output_contains_colorgroup_with_one_entry_per_vertex(tmp_path_factory_ext):
    out = tmp_path_factory_ext(".3mf")
    vertices, faces, scalars = _build_small_mesh()
    c2s.save(out, vertices, faces, scalars=scalars)

    with zipfile.ZipFile(out) as zf:
        xml = zf.read("3D/3dmodel.model").decode("utf-8")

    assert "<m:colorgroup" in xml
    assert len(re.findall(r'<m:color color="#', xml)) == len(vertices)
    # Triangles must reference per-corner color indices.
    assert len(re.findall(r'p1="\d+"', xml)) == len(faces)


def test_stl_output_still_works(tmp_path_factory_ext):
    from stl import mesh as stlmesh

    out = tmp_path_factory_ext(".stl")
    vertices, faces, _ = _build_small_mesh()
    c2s.save(out, vertices, faces)

    reloaded = stlmesh.Mesh.from_file(out)
    assert reloaded.vectors.shape == (len(faces), 3, 3)


def test_unknown_extension_raises(tmp_path_factory_ext):
    out = tmp_path_factory_ext(".obj")
    vertices, faces, scalars = _build_small_mesh()
    with pytest.raises(ValueError, match="Unsupported output extension"):
        c2s.save(out, vertices, faces, scalars=scalars)
