"""Define a estrutura de dados para armazenar as estatísticas da simulação."""

# Importações base;
from dataclasses import dataclass, field

# Anotações de tipo;
from typing import List

@dataclass
class SimulationReport:
    """Armazena estatísticas da simulação."""
    total_packets: int = 0
    lost_packets: int = 0
    corrupted_packets: int = 0
    jitter_values_ms: List[float] = field(default_factory=list)

    # Markov;
    transitions_gb: int = 0  # Good → Bad;
    transitions_bg: int = 0  # Bad → Good;
    transitions_gg: int = 0
    transitions_bb: int = 0

    # Bits corrompidos;
    total_bits: int = 0
    flipped_bits: int = 0

    def print_report(self):
        loss_pct = 100.0 * self.lost_packets / max(self.total_packets, 1)
        corr_pct = 100.0 * self.corrupted_packets / max(self.total_packets, 1)
        ber_real  = self.flipped_bits / max(self.total_bits, 1)

        jitter_mean = (sum(self.jitter_values_ms) / len(self.jitter_values_ms)
                       if self.jitter_values_ms else 0.0)
        jitter_max  = max(self.jitter_values_ms, default=0.0)
        jitter_min  = min(self.jitter_values_ms, default=0.0)

        sep = "=" * 60
        print(f"\n{sep}")
        print("  RELATÓRIO DE SIMULAÇÃO DE DEGRADAÇÃO DE VOZ")
        print(sep)

        print("\n[1] JITTER (Atraso Variável)")
        print(f"    Mínimo : {jitter_min:.2f} ms")
        print(f"    Médio  : {jitter_mean:.2f} ms")
        print(f"    Máximo : {jitter_max:.2f} ms")

        print("\n[2] PERDA DE PACOTES — Cadeia de Markov")
        print(f"    Total de pacotes     : {self.total_packets}")
        print(f"    Pacotes perdidos     : {self.lost_packets}  ({loss_pct:.2f}%)")
        print(f"    Transições G→G       : {self.transitions_gg}")
        print(f"    Transições G→B       : {self.transitions_gb}")
        print(f"    Transições B→G       : {self.transitions_bg}")
        print(f"    Transições B→B       : {self.transitions_bb}")

        print("\n[3] CORRUPÇÃO DE BITS")
        print(f"    Total de bits        : {self.total_bits}")
        print(f"    Bits corrompidos     : {self.flipped_bits}")
        print(f"    BER real             : {ber_real:.2e}")
        print(f"    Pacotes com corrupção: {self.corrupted_packets}  ({corr_pct:.2f}%)")

        print(f"\n{sep}\n")
        