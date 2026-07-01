# 3TDV

**Três** **T**ipos de **D**egradação de **V**oz

Projeto desenvolvido para disciplina GCC269 - Fundamentos de Sistemas Multimídia da UFLA.

Data: 25 de abril de 2026
Criador: Jhuan Carlos Sabaini Dassie
Professor: Demóstenes Zegarra Rodríguez

## Objetivos do trabalho

Terminada as discussões sobre transmissão de áudio em sala de aula, os alunos foram convidados a testar os conhecimentos através de um trabalho prático. Neste Repositório consta então a minha solução para atividade proposta.

## Como executar

Você pode obter os primeiros passos de como usar o programa usando:

```sh
python 3tdv.py -h
```

Você também pode usar o `degrate_and_evaluate.sh` indicando a pasta com arquivos `.wav` e a pasta de saída.
‼️ Lembrando que tanto o `AutoTesting` quanto o `degrate_and_evaluate.sh` foram criados usando IA ‼️

O Teste 4 foi otimizado para usar uma grade reduzida por padrão, com execução paralela via múltiplos processos. Se quiser o comportamento exaustivo antigo, use `--test4-mode full`.

Exemplo em lote:

```sh
./degrate_and_evaluate.sh 3tdv.py /caminho/para/pesq ./results entrada1.wav entrada2.wav -- --test4-mode reduced-grid --repetitions 3
```

## ⚠️ Aviso

O autor reporta abertamente o uso de IA na produção do código.
