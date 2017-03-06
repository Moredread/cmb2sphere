from stl import mesh
from subprocess import run
import os
import tempfile
import pytest
import numpy as np


@pytest.fixture
def temp(request):
    _, filename = tempfile.mkstemp()
    yield filename
    os.remove(filename)

def test_cli_writes_a_file(temp):
    run(["python", "cmb2sphere.py", temp])
    assert os.path.isfile(temp)


def test_vertex_normals_all_point_outwards(temp):
    run(["python", "cmb2sphere.py", temp])
    cmb_mesh = mesh.Mesh.from_file(temp)

    for normal, vertex in zip(cmb_mesh.normals, cmb_mesh.v0):
        assert np.dot(normal, vertex)
        