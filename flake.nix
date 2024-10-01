{
  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        lib = pkgs.lib;
        propositionalcalculus = { poetry2nix, lib }: poetry2nix.mkPoetryApplication {
          projectDir = self;
          overrides = poetry2nix.defaultPoetryOverrides.extend (self: super: {
            tree-sitter = super.tree-sitter.overridePythonAttrs (old: {
              buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools ];
            });
          });
          buildInputs = [ pkgs.graphviz pkgs.python3Packages.setuptools ];
        };
        propositionalcalculus-grammar = {}:
          let
            generate = true;
          in
          pkgs.stdenv.mkDerivation {
            pname = "propositionalcalculus-grammar";
            version = "0.1.0";

            src = ./grammar;

            nativeBuildInputs = lib.optionals generate [ pkgs.nodejs pkgs.tree-sitter ];

            CFLAGS = [ "-Isrc" "-O2" ];
            CXXFLAGS = [ "-Isrc" "-O2" ];

            stripDebugList = [ "parser" ];

            configurePhase = lib.optionalString generate ''
              tree-sitter generate
            '';

            buildPhase = ''
              runHook preBuild
              $CC -fPIC -c src/parser.c -o parser.o $CFLAGS
              $CXX -shared -o parser *.o
              runHook postBuild
            '';

            installPhase = ''
              runHook preInstall
              mkdir $out
              mv parser $out/
              if [[ -d queries ]]; then
              cp -r queries $out
              fi
              runHook postInstall
            '';
          };
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            poetry2nix.overlays.default
            (final: _: {
              propositionalcalculus = final.callPackage propositionalcalculus { };
              propositionalcalculus-grammar = final.callPackage
                propositionalcalculus-grammar
                { };
            })
          ];
        };
      in
      {
        packages = {
          default = pkgs.propositionalcalculus;
          propositionalcalculus-grammar = pkgs.propositionalcalculus-grammar;
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [
            pkgs.propositionalcalculus
            pkgs.propositionalcalculus-grammar
          ];
          packages = with pkgs; [
            nodejs
            tree-sitter
            graphviz
            # self.packages.${system}.propositionalcalculus-grammar
            # self.packages.propositionalcalculus.dependencyEnv
          ];
          shellHook = ''
            export PYTHONPATH=$PYTHONPATH:$PWD/src
          '';
        };
      });
}
