#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'EOF'
Uso:
  ./degrate_and_evaluate.sh <3tdv.py> <pesq_exe> <output_dir> <audio1.wav> [audio2.wav ...] [-- argumentos extras]

Os argumentos após -- são repassados para 3tdvAutoTesting.py.
Exemplo:
  ./degrate_and_evaluate.sh 3tdv.py /caminho/pesq ./results voz1.wav voz2.wav -- --test4-mode reduced-grid --repetitions 3
EOF
}

if [[ $# -lt 4 ]]; then
    usage
    exit 1
fi

ttdv_path="$1"
pesq_exe="$2"
output_dir="$3"
shift 3

audio_files=()
extra_args=()
forward_extra_args=false

for arg in "$@"; do
    if [[ "$arg" == "--" ]]; then
        forward_extra_args=true
        continue
    fi

    if [[ "$forward_extra_args" == true ]]; then
        extra_args+=("$arg")
    else
        audio_files+=("$arg")
    fi
done

if [[ ${#audio_files[@]} -eq 0 ]]; then
    echo "Erro: informe ao menos um arquivo WAV." >&2
    usage
    exit 1
fi

mkdir -p "$output_dir"

python_bin="${PYTHON_BIN:-}"
if [[ -z "$python_bin" ]]; then
    if [[ -x "./venv/bin/python" ]]; then
        python_bin="./venv/bin/python"
    else
        python_bin="python3"
    fi
fi

for input_wav in "${audio_files[@]}"; do
    if [[ ! -f "$input_wav" ]]; then
        echo "Aviso: arquivo não encontrado, pulando: $input_wav" >&2
        continue
    fi

    base_name="$(basename "${input_wav%.*}")"
    file_output_dir="$output_dir/$base_name"
    mkdir -p "$file_output_dir"

    "$python_bin" 3tdvAutoTesting.py "$ttdv_path" "$pesq_exe" "$input_wav" --output-dir "$file_output_dir" "${extra_args[@]}"
done