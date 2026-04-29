"""Utilitários para leitura e escrita de arquivos WAV, e conversão entre raw bytes e samples PCM."""

# Importações base;
import wave
import struct

# Anotações de tipo;
from typing import List, Tuple

def read_wav(path: str) -> Tuple[bytes, int, int, int]:
    """Lê arquivo WAV e retorna (raw_samples_bytes, n_channels, sampwidth, framerate)."""

    with wave.open(path, 'rb') as wf:
        n_channels  = wf.getnchannels()
        sampwidth   = wf.getsampwidth()   # bytes por amostra;
        framerate   = wf.getframerate()
        raw_data    = wf.readframes(wf.getnframes())

    return raw_data, n_channels, sampwidth, framerate


def write_wav(path: str, raw_data: bytes, n_channels: int,
              sampwidth: int, framerate: int) -> None:
    """Escreve bytes PCM em arquivo WAV."""
    
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(raw_data)


def raw_to_samples(raw: bytes, sampwidth: int) -> List[int]:
    """Converte raw bytes em lista de inteiros (PCM)."""
    
    fmt = {1: 'b', 2: '<h', 4: '<i'}.get(sampwidth)
    if fmt is None:
        raise ValueError(f"sampwidth={sampwidth} não suportado.")
    n = len(raw) // sampwidth
    
    return list(struct.unpack(f'{n}{fmt[1:] or fmt}', raw))


def samples_to_raw(samples: List[int], sampwidth: int) -> bytes:
    """Converte lista de inteiros PCM de volta para raw bytes."""
    
    fmt = {1: 'b', 2: '<h', 4: '<i'}.get(sampwidth)
    if fmt is None:
        raise ValueError(f"sampwidth={sampwidth} não suportado.")
    
    return struct.pack(f'{len(samples)}{fmt[1:] or fmt}', *samples)


def clamp_sample(value: int, sampwidth: int) -> int:
    """Garante que a amostragem fique dentro do range válido do PCM."""
    
    bits  = sampwidth * 8
    lo    = -(1 << (bits - 1))
    hi    =  (1 << (bits - 1)) - 1
    
    return max(lo, min(hi, value))