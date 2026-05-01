"""
cmb2sphere

Usage:
  cmb2sphere [--fwhm=<degrees> --nside=<n> --input=<file> --colormap=<n> --synthetic --seed=<n>] <outfilename>

Options:
  --fwhm=<degrees>      Smooth using Gaussian with FWHM of <degrees> [default: 2]
  --nside=<n>           Reduce healpix mesh to n_side = <n> [default: 128]
  --input=<file>        Input FITS file [default: data/COM_CMB_IQU-commander_1024_R2.02_full.fits]
  --colormap=<n>        Matplotlib colormap for .ply / .3mf output [default: RdBu_r]
  --synthetic           Use a synthetic low-l Gaussian random field instead of reading <input>.
                        Useful for tests and demos without the 1 GB Planck FITS file.
  --seed=<n>            RNG seed for --synthetic [default: 42]

Output format is chosen from <outfilename> extension:
  .stl   geometry only
  .ply   geometry + per-vertex color (works in most full-color print services)
  .3mf   geometry + per-vertex color via 3MF Materials Extension (lib3mf)
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


import math
import os
import sys

import numpy as np
import healpy as hp
from scipy.spatial import ConvexHull
from docopt import docopt

# Constants
RADIUS = 30.0
# Scale factor to convert CMB temperature fluctuations (Kelvin) to mesh displacement (mm).
CMB_SCALE_FACTOR = 20000


def main():
    opts = docopt(__doc__)
    nside_target = int(opts["--nside"])
    fwhm = math.radians(float(opts["--fwhm"]))
    outfile = opts["<outfilename>"]
    cmap_name = opts["--colormap"]

    if opts["--synthetic"]:
        sky_map = synthetic_cmb_map(nside_target, seed=int(opts["--seed"]))
    else:
        input_file = opts["--input"]
        if not os.path.exists(input_file):
            print(f"Error: Required data file not found: {input_file}", file=sys.stderr)
            print("Please download the file as described in README.md, "
                  "or run with --synthetic for a no-data demo.", file=sys.stderr)
            sys.exit(1)
        sky_map = hp.read_map(input_file)

    # Smooth and resample to target nside via spherical-harmonic round-trip.
    alm = hp.map2alm(sky_map)
    map_ps = hp.alm2map(alm, nside_target, fwhm=fwhm)

    vertices, points = build_displaced_sphere(map_ps, nside_target)
    faces = build_faces(points)

    n_corrected = fix_orientation(faces, points)
    print(f"Faces corrected: {n_corrected}/{len(faces)} "
          f"({(n_corrected / len(faces) * 100):.1f}%)")

    save(outfile, vertices, faces, scalars=map_ps, cmap_name=cmap_name)


# --- mesh construction ---------------------------------------------------

def spherical(r, theta, phi):
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    return x, y, z


def build_displaced_sphere(map_ps, nside):
    """Return (displaced vertices, unit-sphere points) for a HEALPix map."""
    theta, phi = hp.pix2ang(nside, np.arange(hp.nside2npix(nside)))
    r = RADIUS + CMB_SCALE_FACTOR * map_ps
    vertices = np.stack(spherical(r, theta, phi), -1)
    points = np.stack(spherical(1.0, theta, phi), -1)
    assert points.shape[0] == hp.nside2npix(nside)
    assert points.shape[0] == vertices.shape[0]
    return vertices, points


def build_faces(points):
    """Triangulate pixel-center points via convex hull on the sphere."""
    return ConvexHull(points).simplices.copy()


def fix_orientation(faces, points):
    """
    Ensure all triangular faces have outward-pointing normals.

    scipy.spatial.ConvexHull does not guarantee consistent winding for
    triangles in spherical meshes. For each face with corner positions a,
    b, c we check sign(dot(cross(a - c, a - b), a)). If positive, the face
    points inward and we swap two vertices. Vectorized over all faces.

    Args:
        faces: (N, 3) integer array of vertex indices, modified in-place.
        points: (M, 3) array of vertex positions on the unit sphere.

    Returns:
        int: number of faces that were corrected.
    """
    a = points[faces[:, 0]]
    b = points[faces[:, 1]]
    c = points[faces[:, 2]]
    flip = np.einsum("ij,ij->i", np.cross(a - c, a - b), a) > 0.0
    # Swap columns 0 and 1 on rows that need flipping.
    faces[flip, 0], faces[flip, 1] = faces[flip, 1], faces[flip, 0].copy()
    return int(flip.sum())


# --- synthetic data ------------------------------------------------------

def synthetic_cmb_map(nside, seed=42, lmax=None):
    """
    Generate a low-l Gaussian random field suitable for end-to-end tests.

    This is *not* a physically-accurate CMB realization - it just produces
    something with the same shape, sign, and rough amplitude as a Planck
    temperature anisotropy map (a few hundred microkelvin RMS, dominated
    by low multipoles after smoothing). Plenty for exercising the pipeline
    without downloading the 1 GB FITS file.
    """
    if lmax is None:
        lmax = 3 * nside - 1
    ell = np.arange(lmax + 1)
    # Red spectrum: Cl ~ 1 / (l + 1)^2, scaled to ~10^-4 K (i.e. ~100 uK) RMS.
    cl = 1.0e-8 / (ell + 1) ** 2
    rng = np.random.default_rng(seed)
    # synfast doesn't take an RNG directly; seed numpy's legacy state for it.
    np.random.seed(int(rng.integers(0, 2**31 - 1)))
    return hp.synfast(cl, nside, lmax=lmax, new=True)


# --- output --------------------------------------------------------------

def save(outfile, vertices, faces, scalars=None, cmap_name="RdBu_r"):
    """Dispatch on extension. STL is geometry-only; PLY and 3MF carry color."""
    ext = os.path.splitext(outfile)[1].lower()
    if ext == ".stl":
        save_stl(outfile, vertices, faces)
    elif ext == ".ply":
        save_ply(outfile, vertices, faces, scalars, cmap_name)
    elif ext == ".3mf":
        save_3mf(outfile, vertices, faces, scalars, cmap_name)
    else:
        raise ValueError(f"Unsupported output extension: {ext!r} "
                         "(expected .stl, .ply, or .3mf)")


def _scalars_to_rgba(scalars, cmap_name):
    import matplotlib
    norm = (scalars - scalars.min()) / np.ptp(scalars)
    return (matplotlib.colormaps[cmap_name](norm) * 255).astype(np.uint8)


def save_stl(outfile, vertices, faces):
    # Kept on numpy-stl to preserve byte-for-byte STL output for existing tests.
    from stl import mesh as stlmesh
    out = stlmesh.Mesh(np.zeros(faces.shape[0], dtype=stlmesh.Mesh.dtype))
    out.vectors[:] = vertices[faces]
    out.save(outfile)


def save_ply(outfile, vertices, faces, scalars, cmap_name):
    if scalars is None:
        raise ValueError(".ply output requires scalars for vertex color")
    import trimesh
    rgba = _scalars_to_rgba(scalars, cmap_name)
    m = trimesh.Trimesh(vertices=vertices, faces=faces,
                        vertex_colors=rgba, process=False)
    m.export(outfile)


def save_3mf(outfile, vertices, faces, scalars, cmap_name):
    """
    Write a 3MF using the Materials Extension. 3MF has no native per-vertex
    color; we put one entry per vertex into a ColorGroup and reference it
    per-corner from each triangle, which is equivalent.
    """
    if scalars is None:
        raise ValueError(".3mf output requires scalars for vertex color")
    import lib3mf

    rgba = _scalars_to_rgba(scalars, cmap_name)

    w = lib3mf.Wrapper()
    model = w.CreateModel()
    mesh = model.AddMeshObject()
    mesh.SetName("cmb_sphere")

    for v in vertices:
        pos = lib3mf.Position()
        pos.Coordinates[0] = float(v[0])
        pos.Coordinates[1] = float(v[1])
        pos.Coordinates[2] = float(v[2])
        mesh.AddVertex(pos)

    cgroup = model.AddColorGroup()
    color_idx = np.empty(len(vertices), dtype=np.uint32)
    for i, c in enumerate(rgba):
        color_idx[i] = cgroup.AddColor(
            w.RGBAToColor(int(c[0]), int(c[1]), int(c[2]), int(c[3]))
        )
    cgroup_id = cgroup.GetResourceID()

    for f in faces:
        tri = lib3mf.Triangle()
        tri.Indices[0] = int(f[0])
        tri.Indices[1] = int(f[1])
        tri.Indices[2] = int(f[2])
        tri_idx = mesh.AddTriangle(tri)
        props = lib3mf.TriangleProperties()
        props.ResourceID = cgroup_id
        props.PropertyIDs[0] = int(color_idx[f[0]])
        props.PropertyIDs[1] = int(color_idx[f[1]])
        props.PropertyIDs[2] = int(color_idx[f[2]])
        mesh.SetTriangleProperties(tri_idx, props)

    mesh.SetObjectLevelProperty(cgroup_id, int(color_idx[0]))
    model.AddBuildItem(mesh, w.GetIdentityTransform())

    writer = model.QueryWriter("3mf")
    writer.WriteToFile(outfile)


if __name__ == "__main__":
    main()
