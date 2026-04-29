"""
3TDV - Três Tipos de Degradações de Voz - Simulador
=========================================
Simula degradações de canal para avaliação de qualidade de voz (ITU-T P.862 / PESQ);
Projeto desenvolvido para disciplina de Fundamentos de Sistemas Multimídias da UFLA.

Degradações implementadas:
  1. Jitter (atraso variável por pacote)
  2. Perda de pacotes via Cadeia de Markov de 2 estados (Gilbert-Elliott)
  3. Corrupção de bits nos samples de áudio

Uso:
    python 3tdv.py entrada.wav saida_degradada.wav [opções]

    --packet-ms       Duração de cada pacote em ms         (padrão: 20)
    --jitter-max-ms   Jitter máximo em ms                  (padrão: 80)
    --jitter-dist     Distribuição do jitter: uniform|gaussian|pareto  (padrão: gaussian)
    --p-loss-gb       P(Good→Bad) na Cadeia de Markov      (padrão: 0.05)
    --p-loss-bb       P(Bad→Bad) na Cadeia de Markov       (padrão: 0.70)
    --ber             Bit Error Rate (taxa de corrupção)   (padrão: 1e-4)
    --seed            Semente aleatória para reprodução    (padrão: 42)
    --report          Exibe relatório detalhado            (padrão: ativado)

Exemplo:
    python 3tdv.py voz_original.wav voz_degradada.wav \
        --packet-ms 20 --jitter-max-ms 100 --p-loss-gb 0.08 --p-loss-bb 0.65 --ber 5e-5
"""

import argparse
import os
import sys
from Degradations import simulate

# -----------;
# --- CLI ---;
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Simulador de Degradação de Transmissão de Voz (ITU-T)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("input",  help="Arquivo WAV de entrada (referência limpa)")
    p.add_argument("output", help="Arquivo WAV de saída (sinal degradado)")
 
    g1 = p.add_argument_group("Pacotização")
    g1.add_argument("--packet-ms", type=float, default=20.0,
                    help="Duração de cada pacote em ms (padrão: 20)")
 
    g2 = p.add_argument_group("Jitter")
    g2.add_argument("--jitter-max-ms", type=float, default=80.0,
                    help="Jitter máximo em ms (padrão: 80)")
    g2.add_argument("--jitter-dist",   type=str,   default="gaussian",
                    choices=["uniform", "gaussian", "pareto"],
                    help="Distribuição do jitter (padrão: gaussian)")
 
    g3 = p.add_argument_group("Perda de Pacotes — Cadeia de Markov")
    g3.add_argument("--p-loss-gb", type=float, default=0.05,
                    help="P(Good→Bad): prob. de iniciar burst de perda (padrão: 0.05)")
    g3.add_argument("--p-loss-bb", type=float, default=0.70,
                    help="P(Bad→Bad): prob. de continuar burst de perda (padrão: 0.70)")
 
    g4 = p.add_argument_group("Corrupção de Bits")
    g4.add_argument("--ber", type=float, default=1e-4,
                    help="Bit Error Rate (padrão: 1e-4)")
 
    p.add_argument("--seed",   type=int,  default=42,   help="Semente aleatória (padrão: 42)")
    p.add_argument("--no-report", action="store_true",  help="Suprime o relatório final")
 
    return p

# ---------------------------;
def main():
    parser = build_parser()
    args   = parser.parse_args()
 
    if not os.path.isfile(args.input):
        print(f"Erro: arquivo de entrada não encontrado: {args.input}", file=sys.stderr)
        sys.exit(1)

    simulate(
        input_path    = args.input,
        output_path   = args.output,
        packet_ms     = args.packet_ms,
        jitter_max_ms = args.jitter_max_ms,
        jitter_dist   = args.jitter_dist,
        p_loss_gb     = args.p_loss_gb,
        p_loss_bb     = args.p_loss_bb,
        ber           = args.ber,
        seed          = args.seed,
        show_report   = not args.no_report,
    )


if __name__ == "__main__":
    main()