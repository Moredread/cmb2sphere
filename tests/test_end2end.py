from stl import mesh
from subprocess import run
import os
import tempfile
import pytest
import numpy as np
import healpy as hp


# End-to-end CLI tests. These invoke cmb2sphere.py as a subprocess and
# use --synthetic so they can run without the 1 GB Planck FITS file.


@pytest.fixture
def temp(request):
    fd, filename = tempfile.mkstemp(suffix=".stl")
    os.close(fd)
    yield filename
    os.remove(filename)


def test_cli_writes_a_file(temp):
    run(["python", "cmb2sphere.py", "--synthetic", temp], check=True)
    assert os.path.getsize(temp) > 0


def test_vertex_normals_all_point_outwards(temp):
    run(["python", "cmb2sphere.py", "--synthetic", temp], check=True)
    cmb_mesh = mesh.Mesh.from_file(temp)

    for normal, vertex in zip(cmb_mesh.normals, cmb_mesh.v0):
        assert np.dot(normal, vertex) > 0


def _unique_vertex_count(cmb_mesh):
    """Count unique vertices across all triangle corners of an STL mesh."""
    corners = np.vstack([cmb_mesh.v0, cmb_mesh.v1, cmb_mesh.v2])
    return len({tuple(v) for v in corners})


def test_vertex_number_is_correct_for_nside_default(temp):
    nside_default = 128
    run(["python", "cmb2sphere.py", "--synthetic", temp], check=True)
    cmb_mesh = mesh.Mesh.from_file(temp)

    assert _unique_vertex_count(cmb_mesh) == hp.nside2npix(nside_default)


def test_vertex_number_is_correct_for_nside_from_parameter(temp):
    nside = "256"
    run(["python", "cmb2sphere.py", "--synthetic", "--nside", nside, temp], check=True)
    cmb_mesh = mesh.Mesh.from_file(temp)

    assert _unique_vertex_count(cmb_mesh) == hp.nside2npix(int(nside))
