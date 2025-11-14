{
  description = "CMB2Sphere - Converts Planck CMB temperature data into 3D sphere meshes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, uv2nix, pyproject-nix, pyproject-build-systems }:
    let
      inherit (nixpkgs) lib;

      # Systems to support
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];

      forAllSystems = lib.genAttrs systems;

      # Load workspace for all systems
      workspaceFor = system:
        uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

    in {
      # Development shells
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};

          # Load the workspace
          workspace = workspaceFor system;

          # Create base Python set with pyproject.nix
          python = pkgs.python313;
          pythonBase = pkgs.callPackage pyproject-nix.build.packages {
            inherit python;
          };

          # Create overlay from uv.lock
          overlay = workspace.mkPyprojectOverlay {
            sourcePreference = "wheel"; # Prefer binary wheels
          };

          # Create editable overlay for development
          editableOverlay = workspace.mkEditablePyprojectOverlay {
            root = "$REPO_ROOT";
          };

          # Compose the final Python package set
          pythonSet = pythonBase.overrideScope (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.default
              overlay
              editableOverlay
            ]
          );

          # Create virtual environment with all dependencies
          virtualenv = pythonSet.mkVirtualEnv "cmb2sphere-dev-env" workspace.deps.all;

        in {
          default = pkgs.mkShell {
            packages = [
              python
              pkgs.uv
              pkgs.just
              pkgs.curl
            ];

            shellHook = ''
              # Get repository root
              export REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

              # Unset PYTHONPATH to avoid conflicts
              unset PYTHONPATH

              # Prevent uv from managing venv
              export UV_NO_SYNC=1

              # Add virtual environment to PATH
              export PATH="${virtualenv}/bin:$PATH"

              echo "🚀 CMB2Sphere development environment"
              echo "Python: $(python --version)"
              echo "UV: $(uv --version)"
              echo ""
              echo "Available commands:"
              echo "  just --list    - Show all available recipes"
              echo "  just setup     - Install dependencies"
              echo "  just test      - Run tests"
              echo ""
            '';
          };
        });

      # Packages
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          workspace = workspaceFor system;

          python = pkgs.python313;
          pythonBase = pkgs.callPackage pyproject-nix.build.packages {
            inherit python;
          };

          overlay = workspace.mkPyprojectOverlay {
            sourcePreference = "wheel";
          };

          pythonSet = pythonBase.overrideScope (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.default
              overlay
            ]
          );

        in {
          default = pythonSet.mkVirtualEnv "cmb2sphere-env" workspace.deps.default;
          cmb2sphere = pythonSet.cmb2sphere;
        });
    };
}
