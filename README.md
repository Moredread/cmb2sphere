# cmb2sphere

Converts [Planck](http://sci.esa.int/planck/) temperature data into a height
profile on a sphere. Inspired by ['Cosmic sculpture: a new way to visualise the cosmic microwave background'] [1] by Clements, D. L., S. Sato, and A. Portela Fonseca.

I plan to write about how the process works, how to use the script and how to print the resulting file soon(tm). Feel free to remind me if this notice is still up.

Also forgive some bad stylistic choices, the certainly existing bugs and
anything that is wrong with the script. As often in "research" there wasn't
enough time to do it right... or maybe I was too lazy to improve it further. :p
(We really need a standardized note for this)

## Installation

This project uses [UV](https://docs.astral.sh/uv/) for dependency management and includes a [Nix flake](https://nixos.wiki/wiki/Flakes) for reproducible development environments.

### Using UV (Recommended)

```bash
# Install dependencies
uv sync

# Run the script directly
uv run python cmb2sphere.py output.stl

# With custom parameters
uv run python cmb2sphere.py --fwhm=3 --nside=256 output.stl
```

### Using Nix Flake

```bash
# Enter development shell
nix develop

# Dependencies are automatically available
python cmb2sphere.py output.stl
```

### Using Just (Task Runner)

This project includes a `justfile` with common tasks:

```bash
# Show all available commands
just --list

# Complete setup (creates directories and installs dependencies)
just setup

# Download CMB data from Planck mission archive
just download

# Build with custom parameters
just build 5 128 output.stl

# Run tests
just test
```

### Manual Installation with pip

If you prefer pip:
```bash
pip install healpy matplotlib numpy scipy numpy-stl docopt-ng
```

## Usage

### Download Data

Download the Planck CMB data:
```bash
just download
```

Or manually download https://irsa.ipac.caltech.edu/data/Planck/release_2/all-sky-maps/maps/component-maps/cmb/COM_CMB_IQU-commander_1024_R2.02_full.fits and place it in the "data" subdirectory.

### Generate Sphere Mesh

```bash
# Using UV
uv run python cmb2sphere.py output.stl

# Using Just
just build 2 128 output.stl

# With custom parameters
uv run python cmb2sphere.py --fwhm=3 --nside=256 custom_output.stl
```

## License

The script itself is licensed under the GNU Affero General Public License v3.0
or later (AGPL-3.0-or-later). Please see the *COPYING* file for details.

If there are questions in your jurisdiction, or if the AGPL is not clear enough
on the point, please consider the resulting mesh files under a CC0 or whatever
you like. Effectively, do what you want with them, but please consider a citation,
or other kind of attribution.


  [1]: http://dx.doi.org/10.1088%2F0143-0807%2F38%2F1%2F015601 "Clements, D. L., S. Sato, and A. Portela Fonseca. 'Cosmic sculpture: a new way to visualise the cosmic microwave background.' European Journal of Physics 38.1 (2016): 015601."
