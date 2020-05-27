with import <nixpkgs> {};
let
  cet-bus = python3Packages.buildPythonPackage rec {
    name = "cet-bus-0.0.0";
    version = "0.0.0";
    src = ./cet_bus;
  };
  my-packages = python-packages: with python-packages; [
    python37Packages.flask
    beautifulsoup4
    cet-bus
  ];
  python-with-my-packages = python3.withPackages my-packages;
in
  pkgs.mkShell {
    buildInputs = [
      python-with-my-packages
      python3Packages.flask
    ];
  }
