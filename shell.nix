with import <nixpkgs> {};
let
  my-packages = python-packages: with python-packages; [
    flask
    beautifulsoup4
    ./cet_bus
  ];
  python-with-my-packages = python3.withPackages my-packages;
in
  python-with-my-packages
