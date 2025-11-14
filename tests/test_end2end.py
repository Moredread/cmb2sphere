from stl import mesh
from subprocess import run
import os
import tempfile
import pytest
import numpy as np
import healpy as hp


@pytest.fixture
def temp(request):
    _, filename = tempfile.mkstemp()
    yield filename
    os.remove(filename)


def test_cli_writes_a_file(temp):
    run(["python", "cmb2sphere.py", temp], check=True)
    assert os.path.getsize(temp) > 0


def test_vertex_normals_all_point_outwards(temp):
    run(["python", "cmb2sphere.py", temp], check=True)
    cmb_mesh = mesh.Mesh.from_file(temp)

    for normal, vertex in zip(cmb_mesh.normals, cmb_mesh.v0):
        assert np.dot(normal, vertex) > 0


def test_vertex_number_is_correct_for_nside_default(temp):
    nside_default = 128
    run(["python", "cmb2sphere.py", temp], check=True)
    cmb_mesh = mesh.Mesh.from_file(temp)

    assert cmb_mesh.normals.shape[0] == hp.nside2npix(int(nside_default))


def test_vertex_number_is_correct_for_nside_from_parameter(temp):
    nside = "256"
    run(["python", "cmb2sphere.py", "--nside", nside, temp], check=True)
    cmb_mesh = mesh.Mesh.from_file(temp)

    assert len(set(cmb_mesh.v0)) == hp.nside2npix(int(nside))
