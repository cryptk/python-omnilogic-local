{
  pkgs ? import <nixpkgs> { },
}:

let
  shellInit = pkgs.writeText "haomnilogic-shell-init" ''
    # Preserve the user's existing shell configuration
    if [ -f "$HOME/.bashrc" ]; then
      source "$HOME/.bashrc"
    fi

    if [ ! -d ".venv" ]; then
      echo "--- Initializing venv ---"
      uv venv --python python3.14
    fi

    echo "--- Activating Virtual Environment ---"
    source .venv/bin/activate

    echo "--- Syncing Project Dependencies ---"
    uv sync --all-extras
  '';
in
(pkgs.buildFHSEnv {
  name = "haomnilogic-fhs";
  targetPkgs =
    pkgs: with pkgs; [
      nodejs
      python314
      uv
    ];

  runScript = "bash --rcfile ${shellInit}";
}).env
