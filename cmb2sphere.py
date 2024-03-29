"""
cmp2sphere

Usage:
  cmb2sphere [--fwhm=<degrees> --nside=<n>] <outfilename>

Options:
  --fwhm=<degrees>      Smooth using Gaussian with FHWM of <degrees> [default: 2]
  --nside=<n>           Reduce healpix mesh to n_side = <n> [default: 128]
"""

"""
cmb2sphere.py
Copyright (C) 2022  André-Patrick Bubel

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


import sys

sys.ps1 = 'SOMETHING'
import numpy as np
import healpy as hp
import pickle
from stl import mesh
from scipy.spatial import ConvexHull
import math
import shelve
from docopt import docopt

opts = docopt(__doc__)

NSIDE_TARGET = int(opts["--nside"])
RADIUS = 30.
AMPLITUDE = 0.1 * RADIUS
FHWM = math.radians(float(opts["--fwhm"]))
# INPUT = "data/COM_CMB_IQU-commander-field-Int_2048_R2.01_full.fits"
INPUT = "data/COM_CMB_IQU-commander_1024_R2.02_full.fits"
# INPUT = "data/COM_CMB_IQU-commander_0256_R2.00.fits"
AUTOSCALE = False


def basename(filename):
    return filename.split(".")[0]

def main():
    map = hp.read_map(INPUT)

    pickle_filename = "{}.pickle".format(basename(INPUT))
    try:
        with open(pickle_filename, "rb") as f:
            alm = pickle.load(f)
            print("Alm loaded")
    except:
        print("Generate alm")
        alm = hp.map2alm(map)
        with open(pickle_filename, "wb") as f:
            pickle.dump(alm, f)

    s = shelve.open("cache.shelve")

    key = "{}^{}^{}".format(INPUT, NSIDE_TARGET, FHWM)
    if key not in s:
        s[key] = hp.alm2map(alm, NSIDE_TARGET, fwhm=FHWM)
    map_ps = s[key]

    s.close()

    theta, phi = hp.pix2ang(NSIDE_TARGET, np.arange(hp.nside2npix(NSIDE_TARGET)))
    amplitude = max(abs(np.max(map_ps)), abs(np.min(map_ps)))

    if AUTOSCALE:
        scale = AMPLITUDE / amplitude
        print(scale)
        r = RADIUS + scale * map_ps
    else:
        r = (RADIUS + 2 * 10000 * map_ps)

    vertices = np.stack(spherical(r, theta, phi), -1)
    points = np.stack(spherical(1, theta, phi), -1)

    assert points.shape[0] == hp.nside2npix(NSIDE_TARGET)
    assert points.shape[0] == vertices.shape[0]

    s = shelve.open("faces.shelve")
    key = str(NSIDE_TARGET)
    if key not in s:
        hull = ConvexHull(points)
        faces = hull.simplices
        fix_orientation(faces, points)
        s[key] = faces
    faces = s[key]
    s.close()

    save_mesh(opts["<outfilename>"], faces, vertices)


def fix_orientation(faces, points):
    for i, f in enumerate(faces):
        p1, p2, p3 = f
        a, b, c = (points[p1], points[p2], points[p3])
        if np.dot(np.cross(a - c, a - b), a) > 0.0:
            faces[i][0] = p2
            faces[i][1] = p1


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
