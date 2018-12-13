with import <nixpkgs> {};
let
  a = stdenv.mkDerivation rec {
    name = "healpy";
    version = "1.12.4";

    #propagatedBuildInputs = with python27Packages; [
    #  six pytestrunner cython numpy matplotlib scipy astropy #simple
    #];

    #patchPhase = ''
    #  substituteInPlace setup.py --replace '--disable-shared' '--disable-static'
    #  '';

    buildInputs = [ cfitsio gcc-unwrapped.lib ];

    nativeBuildInputs = [ pkgconfig autoreconfHook ];

    src = python27Packages.fetchPypi {
      inherit version;
      pname = name;
      sha256 = "0w1b99h6fyk6q9gk2qsmqvpwxy4dy60cm1xf2852jr808a5p9wfz";
    };

    enableParallelBuilding = true;

    sourceRoot = "healpy-1.12.4/healpixsubmodule/src/cxx/autotools";

  preAutoreconf = ''
    aclocal
  '';

  };

  healpy = python3Packages.buildPythonPackage rec {
    pname = "healpy";
    version = "1.12.4";

    propagatedBuildInputs = with python3Packages; [
      six pytestrunner cython numpy matplotlib scipy astropy a #simple
    ];

    patchPhase = ''
      substituteInPlace setup.py --replace '--disable-shared' '--disable-static'
      '';

    buildInputs = [ cfitsio gcc-unwrapped.lib ];

    nativeBuildInputs = [ pkgconfig ];

    src = python27Packages.fetchPypi {
      inherit pname version;
      sha256 = "0w1b99h6fyk6q9gk2qsmqvpwxy4dy60cm1xf2852jr808a5p9wfz";
    };

    doCheck = false;

    enableParallelBuilding = true;
  };
in

mkShell {
  name = "env";
  buildInputs = with python3Packages; [
    bashInteractive
    healpy
    matplotlib
    numpy
    scipy
    numpy-stl
    docopt
    pytest
  ];
}
