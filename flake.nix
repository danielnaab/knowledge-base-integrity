{
  description = "graft-pins";

  # graft (https://github.com/danielnaab/graft) copies the pinned exports of the knowledge this repo
  # follows into scions/. `nix run .#graft` after changing a pin, then commit scions/;
  # `nix flake check` fails if scions/ drifts from flake.lock.
  inputs.graft.url = "github:danielnaab/graft/v2.5.0";
  inputs.meta-knowledge-base = { url = "github:danielnaab/meta-knowledge-base/v1.0.1"; flake = false; };
  inputs.living-specifications = { url = "github:danielnaab/living-specifications/v1.0.1"; flake = false; };

  outputs = inputs: inputs.graft.lib.mkGraft { inherit inputs; deps = [ "meta-knowledge-base" "living-specifications" ]; };
}
