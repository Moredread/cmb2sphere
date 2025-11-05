# cmb2sphere - Justfile for building CMB visualization
# Downloads Planck satellite CMB data and orchestrates the build process

# Default recipe - show help
default:
    @just --list

# Variables
data_dir := "data"
cmb_file := "COM_CMB_IQU-commander_1024_R2.02_full.fits"
cmb_url := "https://irsa.ipac.caltech.edu/data/Planck/release_2/all-sky-maps/maps/component-maps/cmb/" + cmb_file
output_file := "cmb_sphere.stl"

# Setup: Create data directory and install Python dependencies
setup:
    @echo "Setting up cmb2sphere environment..."
    mkdir -p {{data_dir}}
    pip install -r requirements.txt
    @echo "Setup complete!"

# Download CMB data from Planck mission archive
download:
    @echo "Downloading CMB data from IRSA..."
    @echo "URL: {{cmb_url}}"
    @if [ -f "{{data_dir}}/{{cmb_file}}" ]; then \
        echo "File already exists: {{data_dir}}/{{cmb_file}}"; \
        echo "Skipping download. Use 'just clean-data' to re-download."; \
    else \
        mkdir -p {{data_dir}}; \
        curl -L -o "{{data_dir}}/{{cmb_file}}" "{{cmb_url}}" --progress-bar; \
        echo "Download complete!"; \
    fi

# Verify that CMB data is downloaded
verify-data:
    @if [ ! -f "{{data_dir}}/{{cmb_file}}" ]; then \
        echo "ERROR: CMB data file not found!"; \
        echo "Run 'just download' to download the data."; \
        exit 1; \
    else \
        echo "CMB data file found: {{data_dir}}/{{cmb_file}}"; \
        ls -lh "{{data_dir}}/{{cmb_file}}"; \
    fi

# Build (run) cmb2sphere with default parameters
build output=output_file: verify-data
    @echo "Running cmb2sphere to generate 3D mesh..."
    python cmb2sphere.py {{output}}
    @echo "Generated: {{output}}"

# Build with custom smoothing parameter (FWHM in degrees)
build-smooth fwhm output=output_file: verify-data
    @echo "Running cmb2sphere with FWHM={{fwhm}} degrees..."
    python cmb2sphere.py --fwhm={{fwhm}} {{output}}
    @echo "Generated: {{output}}"

# Build with custom resolution (nside parameter)
build-hires nside output=output_file: verify-data
    @echo "Running cmb2sphere with nside={{nside}}..."
    python cmb2sphere.py --nside={{nside}} {{output}}
    @echo "Generated: {{output}}"

# Build with custom smoothing and resolution
build-custom fwhm nside output=output_file: verify-data
    @echo "Running cmb2sphere with FWHM={{fwhm}} and nside={{nside}}..."
    python cmb2sphere.py --fwhm={{fwhm}} --nside={{nside}} {{output}}
    @echo "Generated: {{output}}"

# Run tests
test: verify-data
    @echo "Running tests..."
    pytest tests/test_end2end.py -v

# Complete setup: setup environment and download data
all: setup download
    @echo "All setup complete! Ready to build."
    @echo "Run 'just build' to generate the CMB sphere mesh."

# Clean generated cache files and output
clean:
    @echo "Cleaning cache files and generated outputs..."
    rm -f *.pickle
    rm -f cache.shelve*
    rm -f faces.shelve*
    rm -f *.stl
    @echo "Clean complete!"

# Clean downloaded data (requires re-download)
clean-data:
    @echo "Removing downloaded CMB data..."
    rm -f {{data_dir}}/{{cmb_file}}
    @echo "Data removed. Run 'just download' to re-download."

# Clean everything including downloaded data
clean-all: clean clean-data
    @echo "All files cleaned!"

# Show information about the CMB data file
info:
    @echo "CMB Data Information:"
    @echo "  File: {{cmb_file}}"
    @echo "  Source: Planck Release 2 (2015)"
    @echo "  Component: CMB temperature map (Commander algorithm)"
    @echo "  Resolution: 1024 (HEALPix NSIDE)"
    @echo "  URL: {{cmb_url}}"
    @echo ""
    @if [ -f "{{data_dir}}/{{cmb_file}}" ]; then \
        echo "Status: Downloaded ✓"; \
        ls -lh "{{data_dir}}/{{cmb_file}}"; \
    else \
        echo "Status: Not downloaded"; \
        echo "Run 'just download' to download the data."; \
    fi

# Show usage examples
help:
    @echo "cmb2sphere - CMB Visualization Tool"
    @echo ""
    @echo "Quick Start:"
    @echo "  just all              # Setup and download data"
    @echo "  just build            # Generate CMB sphere mesh"
    @echo ""
    @echo "Available Commands:"
    @echo "  just setup            # Install dependencies"
    @echo "  just download         # Download CMB data from Planck archive"
    @echo "  just build [output]   # Build with default parameters"
    @echo "  just build-smooth 5 output.stl  # Build with 5 degree smoothing"
    @echo "  just build-hires 256 output.stl # Build with higher resolution"
    @echo "  just build-custom 3 256 out.stl # Custom smoothing & resolution"
    @echo "  just test             # Run test suite"
    @echo "  just clean            # Remove cache and output files"
    @echo "  just clean-all        # Remove everything including data"
    @echo "  just info             # Show CMB data information"
    @echo ""
    @echo "Parameters:"
    @echo "  fwhm     - Gaussian smoothing (degrees), default: 2"
    @echo "  nside    - HEALPix resolution, default: 128 (higher = more detail)"
    @echo "  output   - Output STL filename, default: {{output_file}}"
