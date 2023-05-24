{
  inputs = {
      flake-utils.url = "github:numtide/flake-utils";
      nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
      inputs.poetry2nix = {
          url = "github:numtide/flake-utils";
          inputs.nixpkgs.follows = "nixpkgs";
      };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }: {
      overlay = {};
  } // (flake-utils.lib.eachDefaultSystem (system:
  let 
      pkgs = import nixpkgs {
          inherit system;
          overlays = [ self.overlay ];
      };
  in {
      apps = {};
  }));
}
