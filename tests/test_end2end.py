from stl import mesh
from subprocess import run
import os
import tempfile
import pytest


@pytest.fixture
def temp(request):
    _, filename = tempfile.mkstemp()
    yield filename
    os.remove(filename)

def test_cli_writes_a_file(temp):
    run(["python", "cmb2sphere.py", temp])
    assert os.path.isfile(temp)



#def test_vertex_normals_all_point_outwards():
#    cmb_mesh = mesh.Mesh.from_file('some_file.stl')