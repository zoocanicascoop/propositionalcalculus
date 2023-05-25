{
    inputs = {
        flake-utils.url = "github:numtide/flake-utils";
        nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
        poetry2nix = {
            url = "github:nix-community/poetry2nix";
            inputs.nixpkgs.follows = "nixpkgs";
        };
    };

    outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
    let
        # see https://github.com/nix-community/poetry2nix/tree/master#api for more functions and examples.
        inherit (poetry2nix.legacyPackages.${system}) mkPoetryApplication defaultPoetryOverrides;
        pkgs = nixpkgs.legacyPackages.${system};
        lib = pkgs.lib;
    in
    {
        packages = {
            propositionalcalculus = mkPoetryApplication { 
                projectDir = self; 
                overrides = defaultPoetryOverrides.extend (self: super: {
                    tree-sitter = super.tree-sitter.overridePythonAttrs (old: {
                        buildInputs = (old.buildInputs or []) ++ [ super.setuptools ];
                    });
                });
                buildInputs = [ pkgs.graphviz pkgs.python3Packages.setuptools ];
            };
            propositionalcalculus-grammar = let 
                generate = true; 
            in pkgs.stdenv.mkDerivation {
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
            default = self.packages.${system}.propositionalcalculus;
        };

        devShells.default = pkgs.mkShell {
            packages = with pkgs; [ 
                nodejs
                tree-sitter
                graphviz
                poetry2nix.packages.${system}.poetry 
                self.packages.${system}.propositionalcalculus-grammar
                self.packages.${system}.propositionalcalculus.dependencyEnv
            ];
        };
    });
}
