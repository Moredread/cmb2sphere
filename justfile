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

# Setup: Create data directory and sync Python dependencies with uv
setup:
    @echo "Setting up cmb2sphere environment..."
    mkdir -p {{data_dir}}
    uv sync
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

# Ensure required data exists before running builds/tests
verify-data:
    @echo "Checking for {{data_dir}}/{{cmb_file}}..."
    @if [ -f "{{data_dir}}/{{cmb_file}}" ]; then \
        echo "Data available."; \
    else \
        echo "Data missing. Run 'just download' first."; \
        exit 1; \
    fi

# Build with custom smoothing and resolution
build fwhm="5" nside="128" output=output_file: verify-data
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
    @echo "Run 'just build-custom <fwhm> <nside>' to generate the CMB sphere mesh."

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
