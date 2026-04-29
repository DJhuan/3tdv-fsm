"""
Teste automático para 3TDV: Simulador
=========================================
Tipos de teste:
1 - Variação somente em Jitter
2 - Variação somente em Perda de Pacotes
3 - Variação somente em Corrupção de Bits
4 - Variação combinada (todos os parâmetros)

Uso:
    python 3tdvAutoTesting.py caminho_3tdv executavel_PESQ entrada.wav [opções]
    --output-dir       Diretório para salvar os resultados (padrão: ./results)
    --save-degraded    Salvar os arquivos degradados (padrão: False)
    --skip-tests       Lista de tipos de teste a pular (ex.: --skip-tests 2 4)
"""

import subprocess
import matplotlib.pyplot as plt
import argparse
import os
import csv
import sys 

JITTER_MAX_MS = [0, 1, 2, 3, 4, 5, 10]

P_LOSS_GB = [0.1, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.01]
P_LOSS_BB = [0.01, 0.5]

BER = [1e-7, 5e-7, 1e-6, 5e-6, 1e-5, 5e-5, 1e-4]
DEFAULT_REPETITIONS = 5


def plot_results(results, output_dir, test_type):
    """Gera gráficos dos resultados e salva como PNG."""
    if not results:
        print(f"Sem resultados para gerar gráfico do teste {test_type}.")
        return

    os.makedirs(output_dir, exist_ok=True)

    if test_type == 1:
        x = [jitter for jitter, _ in results]
        y = [score for _, score in results]

        plt.figure(figsize=(10, 6))
        plt.plot(x, y, marker='o')
        plt.title("Teste 1 - Jitter vs PESQ")
        plt.xlabel("Jitter máximo (ms)")
        plt.ylabel("PESQ")
        plt.grid(True)
        plt.tight_layout()

        out = os.path.join(output_dir, "test_type_1.png")
        plt.savefig(out, dpi=150)
        plt.close()
        print(f"✓ Gráfico salvo em: {out}")

    elif test_type == 2:
        grouped = {}
        for (p_gb, p_bb), score in results:
            grouped.setdefault(p_bb, []).append((p_gb, score))

        plt.figure(figsize=(10, 6))
        for p_bb, values in sorted(grouped.items()):
            values_sorted = sorted(values, key=lambda v: v[0])
            x = [v[0] for v in values_sorted]
            y = [v[1] for v in values_sorted]
            plt.plot(x, y, marker='o', label=f"P(B→B)={p_bb}")

        plt.title("Teste 2 - Perda de Pacotes vs PESQ")
        plt.xlabel("P(G→B)")
        plt.ylabel("PESQ")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        out = os.path.join(output_dir, "test_type_2.png")
        plt.savefig(out, dpi=150)
        plt.close()
        print(f"✓ Gráfico salvo em: {out}")

    elif test_type == 3:
        x = [ber for ber, _ in results]
        y = [score for _, score in results]

        plt.figure(figsize=(10, 6))
        plt.semilogx(x, y, marker='o')
        plt.title("Teste 3 - BER vs PESQ")
        plt.xlabel("BER")
        plt.ylabel("PESQ")
        plt.grid(True, which="both")
        plt.tight_layout()

        out = os.path.join(output_dir, "test_type_3.png")
        plt.savefig(out, dpi=150)
        plt.close()
        print(f"✓ Gráfico salvo em: {out}")

    elif test_type == 4:
        # Gráfico A: distribuição dos valores de PESQ
        scores = [score for _, score in results]
        plt.figure(figsize=(10, 6))
        plt.hist(scores, bins=20, edgecolor='black')
        plt.title("Teste 4 - Distribuição de PESQ")
        plt.xlabel("PESQ")
        plt.ylabel("Frequência")
        plt.grid(True, axis='y')
        plt.tight_layout()

        out_hist = os.path.join(output_dir, "test_type_4_hist.png")
        plt.savefig(out_hist, dpi=150)
        plt.close()
        print(f"✓ Gráfico salvo em: {out_hist}")

        # Gráfico B: média de PESQ por nível de jitter
        by_jitter = {}
        for (jitter, _, _, _), score in results:
            by_jitter.setdefault(jitter, []).append(score)

        jitter_levels = sorted(by_jitter.keys())
        avg_scores = [sum(by_jitter[j]) / len(by_jitter[j]) for j in jitter_levels]

        plt.figure(figsize=(10, 6))
        plt.plot(jitter_levels, avg_scores, marker='o')
        plt.title("Teste 4 - PESQ médio por Jitter")
        plt.xlabel("Jitter máximo (ms)")
        plt.ylabel("PESQ médio")
        plt.grid(True)
        plt.tight_layout()

        out_avg = os.path.join(output_dir, "test_type_4_avg_by_jitter.png")
        plt.savefig(out_avg, dpi=150)
        plt.close()
        print(f"✓ Gráfico salvo em: {out_avg}")

def run_degradation(input_file, ttdv_path, params):
    """Executa a degradação e retorna o arquivo de saída."""
    output_file = input_file.replace(".wav", "_degraded.wav")
    
    cmd = f"python {ttdv_path} {input_file} {output_file} --no-report " + " ".join(params)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Erro ao degradar {input_file}: {result.stderr}", file=sys.stderr)
        return None
    
    return output_file

def run_pesq(degraded_file, reference_file, pesq_exe):
    """Executa PESQ e retorna o score."""
    cmd = f"{pesq_exe} +16000 {reference_file} {degraded_file}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Erro ao executar PESQ: {result.stderr}", file=sys.stderr)
        return None
    
    # Parsear a saída do PESQ para obter o score
    for line in reversed(result.stdout.split('\n')):
        if 'Prediction' in line or 'PESQ' in line:
            try:
                score = float(line.split()[-1])
                return score
            except (ValueError, IndexError):
                continue
    
    return None


def run_mean_pesq_for_repetitions(input_file, ttdv_path, pesq_exe, base_params, repetitions):
    """Executa REPETITIONS simulações e retorna a média de PESQ válida."""
    scores = []

    for rep in range(repetitions):
        params = list(base_params)
        params.append(f"--seed {42 + rep}")

        degraded = run_degradation(input_file, ttdv_path, params)
        if degraded is None:
            continue

        pesq_score = run_pesq(degraded, input_file, pesq_exe)
        if pesq_score is not None:
            scores.append(pesq_score)

        if os.path.exists(degraded):
            os.remove(degraded)

    if not scores:
        return None

    return sum(scores) / len(scores)

def test_type_1(input_file, ttdv_path, pesq_exe, output_dir, repetitions):
    """Teste Tipo 1: Variação somente em Jitter."""
    print("\n" + "="*60)
    print("TESTE TIPO 1: Variação somente em Jitter")
    print("="*60)
    
    results = []
    
    for jitter in JITTER_MAX_MS:
        print(f"  Testando Jitter: {jitter} ms (média de {repetitions})", end=" ... ")
        
        base_params = [
            f"--jitter-max-ms {jitter}",
            "--p-loss-gb 0",
            "--p-loss-bb 0",
            "--ber 0"
        ]
        pesq_score = run_mean_pesq_for_repetitions(
            input_file=input_file,
            ttdv_path=ttdv_path,
            pesq_exe=pesq_exe,
            base_params=base_params,
            repetitions=repetitions,
        )
        
        if pesq_score is not None:
            results.append((jitter, pesq_score))
            print(f"PESQ: {pesq_score:.4f}")
        else:
            print("FALHA")
    
    return results

def test_type_2(input_file, ttdv_path, pesq_exe, output_dir, repetitions):
    """Teste Tipo 2: Variação somente em Perda de Pacotes."""
    print("\n" + "="*60)
    print("TESTE TIPO 2: Variação somente em Perda de Pacotes")
    print("="*60)
    
    results = []
    
    for p_gb in P_LOSS_GB:
        for p_bb in P_LOSS_BB:
            print(f"  Testando P(G→B)={p_gb}, P(B→B)={p_bb} (média de {repetitions})", end=" ... ")
            
            base_params = [
                "--jitter-max-ms 0",
                f"--p-loss-gb {p_gb}",
                f"--p-loss-bb {p_bb}",
                "--ber 0"
            ]
            pesq_score = run_mean_pesq_for_repetitions(
                input_file=input_file,
                ttdv_path=ttdv_path,
                pesq_exe=pesq_exe,
                base_params=base_params,
                repetitions=repetitions,
            )
            
            if pesq_score is not None:
                # Usar a combinação (p_gb, p_bg) como índice
                results.append(((p_gb, p_bb), pesq_score))
                print(f"PESQ: {pesq_score:.4f}")
            else:
                print("FALHA")
    
    return results

def test_type_3(input_file, ttdv_path, pesq_exe, output_dir, repetitions):
    """Teste Tipo 3: Variação somente em Corrupção de Bits."""
    print("\n" + "="*60)
    print("TESTE TIPO 3: Variação somente em Corrupção de Bits")
    print("="*60)
    
    results = []
    
    for ber in BER:
        print(f"  Testando BER: {ber:.0e} (média de {repetitions})", end=" ... ")
        
        base_params = [
            "--jitter-max-ms 0",
            "--p-loss-gb 0",
            "--p-loss-bb 0",
            f"--ber {ber}"
        ]
        pesq_score = run_mean_pesq_for_repetitions(
            input_file=input_file,
            ttdv_path=ttdv_path,
            pesq_exe=pesq_exe,
            base_params=base_params,
            repetitions=repetitions,
        )
        
        if pesq_score is not None:
            results.append((ber, pesq_score))
            print(f"PESQ: {pesq_score:.4f}")
        else:
            print("FALHA")
    
    return results

def test_type_4(input_file, ttdv_path, pesq_exe, output_dir):
    """Teste Tipo 4: Variação combinada (todos os parâmetros)."""
    print("\n" + "="*60)
    print("TESTE TIPO 4: Variação Combinada (Todos os Parâmetros)")
    print("="*60)
    
    results = []
    count = 0
    total = len(JITTER_MAX_MS) * len(P_LOSS_GB) * len(P_LOSS_BB) * len(BER)
    
    for jitter in JITTER_MAX_MS:
        for p_gb in P_LOSS_GB:
            for p_bb in P_LOSS_BB:
                for ber in BER:
                    count += 1
                    print(f"  [{count}/{total}] Jitter={jitter}ms, P(G→B)={p_gb}, P(B→B)={p_bb}, BER={ber:.0e}", end=" ... ")
                    
                    params = [
                        f"--jitter-max-ms {jitter}",
                        f"--p-loss-gb {p_gb}",
                        f"--p-loss-bb {p_bb}",
                        f"--ber {ber}"
                    ]
                    
                    degraded = run_degradation(input_file, ttdv_path, params)
                    if degraded is None:
                        continue
                    
                    pesq_score = run_pesq(degraded, input_file, pesq_exe)
                    
                    if pesq_score is not None:
                        results.append(((jitter, p_gb, p_bb, ber), pesq_score))
                        print(f"PESQ: {pesq_score:.4f}")
                    else:
                        print("FALHA")
                    
                    # Remover arquivo degradado
                    if os.path.exists(degraded):
                        os.remove(degraded)
    
    return results

def save_results(results, output_dir, test_type):
    """Salva os resultados em um arquivo CSV."""
    output_file = os.path.join(output_dir, f"test_type_{test_type}.csv")
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w', newline='') as f:
        if test_type == 1:
            writer = csv.writer(f)
            writer.writerow(["Jitter (ms)", "PESQ Score"])
            for jitter, score in results:
                writer.writerow([jitter, score])
        
        elif test_type == 2:
            writer = csv.writer(f)
            writer.writerow(["P(G→B)", "P(B→G)", "PESQ Score"])
            for (p_gb, p_bg), score in results:
                writer.writerow([p_gb, p_bg, score])
        
        elif test_type == 3:
            writer = csv.writer(f)
            writer.writerow(["BER", "PESQ Score"])
            for ber, score in results:
                writer.writerow([ber, score])
        
        elif test_type == 4:
            writer = csv.writer(f)
            writer.writerow(["Jitter (ms)", "P(G→B)", "P(B→G)", "BER", "PESQ Score"])
            for (jitter, p_gb, p_bg, ber), score in results:
                writer.writerow([jitter, p_gb, p_bg, ber, score])
    
    print(f"\n✓ Resultados salvos em: {output_file}")

def build_parser():
    parser = argparse.ArgumentParser(
        description="Teste automático para 3TDV: Simulador",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("ttdv_path", help="Caminho para o script 3tdv.py")
    parser.add_argument("pesq_exe", help="Caminho para o executável PESQ")
    parser.add_argument("input_wav", help="Arquivo WAV de entrada")
    parser.add_argument("--output-dir", default="./results", 
                        help="Diretório para salvar os resultados (padrão: ./results)")
    parser.add_argument("--test-type", type=int, default=0,
                        help="Tipo de teste (1-4, ou 0 para todos)")
    parser.add_argument("--skip-tests", type=int, nargs="*", default=[],
                        help="Tipos de teste para pular (1-4), ex.: --skip-tests 2 4")
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS,
                        help=f"Número de repetições para média dos testes 1-3 (padrão: {DEFAULT_REPETITIONS})")
    
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()
    
    # Validar arquivos de entrada
    if not os.path.isfile(args.ttdv_path):
        print(f"Erro: {args.ttdv_path} não encontrado", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isfile(args.pesq_exe):
        print(f"Erro: {args.pesq_exe} não encontrado", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isfile(args.input_wav):
        print(f"Erro: {args.input_wav} não encontrado", file=sys.stderr)
        sys.exit(1)
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"\nSimulador 3TDV - Teste Automático")
    print(f"Arquivo de entrada: {args.input_wav}")
    print(f"Diretório de saída: {args.output_dir}")

    if args.repetitions < 1:
        print("Erro: --repetitions deve ser >= 1", file=sys.stderr)
        sys.exit(1)
    
    test_type = args.test_type if args.test_type in [1, 2, 3, 4] else 0

    invalid_skips = [t for t in args.skip_tests if t not in [1, 2, 3, 4]]
    if invalid_skips:
        print(f"Erro: valores inválidos em --skip-tests: {invalid_skips}", file=sys.stderr)
        sys.exit(1)

    tests_to_run = [1, 2, 3, 4] if test_type == 0 else [test_type]
    tests_to_run = [t for t in tests_to_run if t not in args.skip_tests]

    if not tests_to_run:
        print("Nenhum teste para executar (todos foram pulados).")
        return

    if 1 in tests_to_run:
        results = test_type_1(args.input_wav, args.ttdv_path, args.pesq_exe, args.output_dir, args.repetitions)
        save_results(results, args.output_dir, 1)
        plot_results(results, args.output_dir, 1)
    
    if 2 in tests_to_run:
        results = test_type_2(args.input_wav, args.ttdv_path, args.pesq_exe, args.output_dir, args.repetitions)
        save_results(results, args.output_dir, 2)
        plot_results(results, args.output_dir, 2)
    
    if 3 in tests_to_run:
        results = test_type_3(args.input_wav, args.ttdv_path, args.pesq_exe, args.output_dir, args.repetitions)
        save_results(results, args.output_dir, 3)
        plot_results(results, args.output_dir, 3)
    
    if 4 in tests_to_run:
        results = test_type_4(args.input_wav, args.ttdv_path, args.pesq_exe, args.output_dir)
        save_results(results, args.output_dir, 4)
        plot_results(results, args.output_dir, 4)
    
    print("\n" + "="*60)
    print("Testes concluídos!")
    print("="*60)

if __name__ == "__main__":
    main()

