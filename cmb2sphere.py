"""
cmb2sphere

Usage:
  cmb2sphere [--fwhm=<degrees> --nside=<n> --input=<file>] <outfilename>

Options:
  --fwhm=<degrees>      Smooth using Gaussian with FWHM of <degrees> [default: 2]
  --nside=<n>           Reduce healpix mesh to n_side = <n> [default: 128]
  --input=<file>        Input FITS file [default: data/COM_CMB_IQU-commander_1024_R2.02_full.fits]
"""

"""
cmb2sphere.py
Copyright (C) 2022-present  André-Patrick Bubel

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


import numpy as np
import healpy as hp
from stl import mesh
from scipy.spatial import ConvexHull
import math
from docopt import docopt
import os
import sys

# Constants
RADIUS = 30.0
# Scale factor to convert CMB temperature fluctuations (microKelvin) to mesh displacement
CMB_SCALE_FACTOR = 20000


def main():
    opts = docopt(__doc__)
    nside_target = int(opts["--nside"])
    fwhm = math.radians(float(opts["--fwhm"]))
    input_file = opts["--input"]

    if not os.path.exists(input_file):
        print(f"Error: Required data file not found: {input_file}", file=sys.stderr)
        print("Please download the file as described in README.md", file=sys.stderr)
        sys.exit(1)

    map = hp.read_map(input_file)
    alm = hp.map2alm(map)
    map_ps = hp.alm2map(alm, nside_target, fwhm=fwhm)

    theta, phi = hp.pix2ang(nside_target, np.arange(hp.nside2npix(nside_target)))

    r = RADIUS + CMB_SCALE_FACTOR * map_ps

    vertices = np.stack(spherical(r, theta, phi), -1)
    points = np.stack(spherical(1, theta, phi), -1)

    assert points.shape[0] == hp.nside2npix(nside_target)
    assert points.shape[0] == vertices.shape[0]

    hull = ConvexHull(points)
    faces = hull.simplices
    corrected = fix_orientation(faces, points)
    total = len(faces)
    percentage = (corrected / total * 100) if total > 0 else 0
    print(f"Faces corrected: {corrected}/{total} ({percentage:.1f}%)")

    save_mesh(opts["<outfilename>"], faces, vertices)


def fix_orientation(faces, points):
    """
    Ensure all triangular faces have normals pointing outward from the sphere center.

    scipy.spatial.ConvexHull doesn't guarantee consistent face orientation for all
    triangles in spherical meshes. This function corrects any inward-facing normals
    by checking each face's orientation and swapping vertices if needed.

    Algorithm:
    - Compute face normal via cross product of two edge vectors
    - Check if normal points outward by comparing with vertex position (dot product)
    - If pointing inward (dot > 0), swap two vertices to reverse winding order

    Args:
        faces: Nx3 array of vertex indices for each triangular face (modified in-place)
        points: Mx3 array of vertex positions on unit sphere

    Returns:
        int: Number of faces that were corrected
    """
    corrected = 0
    for i, f in enumerate(faces):
        p1, p2, p3 = f
        a, b, c = (points[p1], points[p2], points[p3])
        if np.dot(np.cross(a - c, a - b), a) > 0.0:
            faces[i][0] = p2
            faces[i][1] = p1
            corrected += 1
    return corrected


def spherical(r, theta, phi):
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    return x, y, z


def save_mesh(filename, faces, vertices):
    new_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            new_mesh.vectors[i][j] = vertices[f[j], :]
    new_mesh.save(filename)


if __name__ == "__main__":
    main()
