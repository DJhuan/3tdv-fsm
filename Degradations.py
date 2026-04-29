""""Implementação dos módulos de degradação: jitter, perda de pacotes (Gilbert-Elliott) e corrupção de bits."""

# Importações base;
import random

# Importações dos módulos auxiliares;
from SimulationReport import SimulationReport
from WavUtil import *

# Anotações de tipo;
from typing import List

# ---------------------------;
# --- Degradação 1 Jitter ---;
def apply_jitter(
    packets: List[List[int]],
    jitter_max_ms: float,
    framerate: int,
    distribution: str,
    rng: random.Random,
    report: SimulationReport,
) -> List[List[int]]:
    """
    Aplica atraso variável a cada pacote.

    Modela o buffer de jitter: pacotes atrasados além do deadline
    (jitter_max_ms) são descartados (substituídos por silêncio).
    Pacotes dentro do deadline têm seu conteúdo deslocado no tempo
    de forma acumulada — o excesso é preenchido com silêncio.

    Distribuições disponíveis:
        uniform   — U[0, jitter_max_ms]
        gaussian  — N(jitter_max_ms/2, jitter_max_ms/6)  truncada em [0, jitter_max_ms]
        pareto    — Pareto heavy-tail, truncada em [0, jitter_max_ms]
    """
    samples_max_delay = int(jitter_max_ms / 1000.0 * framerate)
    result = []

    for pkt in packets:
        # jitter = 0 = sem atraso, sem descarte;
        if jitter_max_ms == 0.0:
            report.jitter_values_ms.append(0.0)
            result.append(list(pkt))
            continue
        
        # Gera delay aleatório em samples;
        if distribution == "uniform":
            delay_ms = rng.uniform(0, jitter_max_ms)
            
        elif distribution == "gaussian":
            mu    = jitter_max_ms / 2
            sigma = jitter_max_ms / 6
            delay_ms = rng.gauss(mu, sigma)
            delay_ms = max(0.0, min(jitter_max_ms, delay_ms))
            
        elif distribution == "pareto":
            # Pareto com shape=1.5 escalado para [0, jitter_max_ms];
            alpha = 1.5
            raw   = rng.paretovariate(alpha) - 1.0   # em [0, ∞)
            delay_ms = min(raw / alpha * jitter_max_ms * 0.5, jitter_max_ms)
            
        else:
            raise ValueError(f"Distribuição desconhecida: {distribution}")

        report.jitter_values_ms.append(delay_ms)
        delay_samples = int(delay_ms / 1000.0 * framerate)

        if delay_samples >= samples_max_delay and samples_max_delay > 0:
            # Pacote chegou tarde demais → silêncio (descarte por jitter);
            result.append([0] * len(pkt))
        else:
            # Desloca pacote: prefixo de silêncio + corte no final;
            shifted = [0] * delay_samples + pkt
            shifted = shifted[:len(pkt)]
            result.append(shifted)

    return result

# --------------------------------------;
# --- Degradação 2: Perda de Pacotes ---;
def apply_packet_loss_markov(
    packets: List[List[int]],
    p_good_to_bad: float,
    p_bad_to_bad: float,
    rng: random.Random,
    report: SimulationReport,
) -> List[List[int]]:
    """
    Modelo de Gilbert-Elliott (Cadeia de Markov de 2 estados):
        Estado G (Good): pacote é entregue normalmente.
        Estado B (Bad) : pacote é perdido (substituído por silêncio ou PLC).

    Parâmetros:
        p_good_to_bad  — P(G→B): probabilidade de entrar em burst de perda.
        p_bad_to_bad   — P(B→B): probabilidade de continuar em burst.

    P(B→G) = 1 - p_bad_to_bad
    P(G→G) = 1 - p_good_to_bad

    A perda em rajada (burst) simula o comportamento real de redes congestionadas.
    """
    p_bad_to_good  = 1.0 - p_bad_to_bad
    p_good_to_good = 1.0 - p_good_to_bad

    # Estado inicial: Good
    state = "G"
    result = []
    

    for pkt in packets:
        report.total_packets += 1

        # Sem perda = pacote passa normalmente;
        if p_good_to_bad == 0.0:
            report.transitions_gg += 1
            result.append(list(pkt))
            continue
        
        # Transição de estado
        if state == "G":
            if rng.random() < p_good_to_bad:
                next_state = "B"
                report.transitions_gb += 1
            else:
                next_state = "G"
                report.transitions_gg += 1
        else:  # state == "B"
            if rng.random() < p_bad_to_good:
                next_state = "G"
                report.transitions_bg += 1
            else:
                next_state = "B"
                report.transitions_bb += 1

        # Ação com base no estado ATUAL (antes da transição)
        if state == "B":
            report.lost_packets += 1
            # Substituição por silêncio (PLC simples)
            result.append([0] * len(pkt))
        else:
            result.append(list(pkt))

        state = next_state

    return result

# ---------------------------------------;
# --- Degradação 3: Corrupção de Bits ---;
def apply_bit_corruption(
    packets: List[List[int]],
    ber: float,
    sampwidth: int,
    rng: random.Random,
    report: SimulationReport,
) -> List[List[int]]:
    """
    Corrompe bits individuais dos samples PCM com probabilidade `ber`.

    Modelo: canal BSC (Binary Symmetric Channel).
    Cada bit de cada sample tem probabilidade `ber` de ser invertido (XOR 1).
    Samples corrompidos são re-saturados no range do PCM.

    Nota: corrupção nos bits mais significativos (MSB) causa cliques audíveis;
    nos bits menos significativos (LSB) causa ruído de quantização leve.
    """
    bits_per_sample = sampwidth * 8

    result = []
    for pkt in packets:
        new_pkt = []
        pkt_corrupted = False
        for sample in pkt:
            report.total_bits += bits_per_sample
            
            # Sem alteração = sample original é mantido;
            if ber == 0.0:
                new_pkt.append(sample)
                continue

            # Converte para representação sem sinal para fazer XOR seguro
            # Ex: -1 em 16 bits (complemento de 2) = 0xFFFF = 65535
            if sample < 0:
                unsigned_sample = sample + (1 << bits_per_sample)
            else:
                unsigned_sample = sample

            bits_flipped = 0
            for bit_pos in range(bits_per_sample):
                if rng.random() < ber:
                    bits_flipped += 1
                    unsigned_sample ^= (1 << bit_pos)

            if bits_flipped > 0:
                report.flipped_bits += bits_flipped
                pkt_corrupted = True
                # Re-interpretar como complemento de 2 com sinal
                if unsigned_sample & (1 << (bits_per_sample - 1)):
                    new_sample = unsigned_sample - (1 << bits_per_sample)
                else:
                    new_sample = unsigned_sample
                new_sample = clamp_sample(new_sample, sampwidth)
            else:
                # Nenhum bit alternado = sample original inalterado;
                new_sample = sample
            new_pkt.append(new_sample)

        if pkt_corrupted:
            report.corrupted_packets += 1
        result.append(new_pkt)

    return result

# ----------------------------------------;
# --- Empacotamento e desempacotamento ---;
def packetize(samples: List[int], packet_size: int) -> List[List[int]]:
    """Divide o stream de samples em pacotes de tamanho fixo."""
    packets = []
    for i in range(0, len(samples), packet_size):
        pkt = samples[i:i + packet_size]
        # Preenche o último pacote incompleto com silêncio
        if len(pkt) < packet_size:
            pkt += [0] * (packet_size - len(pkt))
        packets.append(pkt)
    return packets

def depacketize(packets: List[List[int]], original_length: int) -> List[int]:
    """Concatena pacotes e corta para o comprimento original."""
    flat = [s for pkt in packets for s in pkt]
    return flat[:original_length]

# --------------------------;
# -- Simulação principal ---;
def simulate(
    input_path: str,
    output_path: str,
    packet_ms: float        = 20.0,
    jitter_max_ms: float    = 80.0,
    jitter_dist: str        = "gaussian",
    p_loss_gb: float        = 0.05,
    p_loss_bb: float        = 0.70,
    ber: float              = 1e-4,
    seed: int               = 42,
    show_report: bool       = True,
) -> SimulationReport:

    rng    = random.Random(seed)
    report = SimulationReport()

    print(f"[*] Lendo arquivo de entrada: {input_path}")
    raw, n_channels, sampwidth, framerate = read_wav(input_path)

    print(f"    Canais       : {n_channels}")
    print(f"    Sample width : {sampwidth} byte(s)  ({sampwidth*8} bits)")
    print(f"    Amostragem   : {framerate} Hz")
    print(f"    Duração      : {len(raw)/(framerate*n_channels*sampwidth):.2f} s")

    samples = raw_to_samples(raw, sampwidth)
    original_length = len(samples)

    # Tamanho do pacote em samples (por canal);
    packet_size = int(packet_ms / 1000.0 * framerate) * n_channels
    if packet_size == 0:
        raise ValueError("packet_ms muito pequeno para a amostragem dada.")

    print(f"\n[*] Pacotização: {packet_ms} ms  →  {packet_size} samples/pacote")
    packets = packetize(samples, packet_size)
    print(f"    Total de pacotes: {len(packets)}")

    # --- Passo 1: Jitter ---;
    print("\n[1] Aplicando Jitter...")
    packets = apply_jitter(
        packets, jitter_max_ms, framerate, jitter_dist, rng, report
    )

    # --- Passo 2: Perda de Pacotes (Markov) ---;
    print("[2] Aplicando Perda de Pacotes (Cadeia de Markov)...")
    packets = apply_packet_loss_markov(
        packets, p_loss_gb, p_loss_bb, rng, report
    )

    # --- Passo 3: Corrupção de Bits ---;
    print("[3] Aplicando Corrupção de Bits (BSC)...")
    packets = apply_bit_corruption(
        packets, ber, sampwidth, rng, report
    )

    # --- Remontagem e escrita ---;
    degraded_samples = depacketize(packets, original_length)
    degraded_raw     = samples_to_raw(degraded_samples, sampwidth)

    print(f"\n[*] Escrevendo arquivo de saída: {output_path}")
    write_wav(output_path, degraded_raw, n_channels, sampwidth, framerate)
    print(f"    Arquivo salvo com sucesso.")

    if show_report:
        report.print_report()

    return report
