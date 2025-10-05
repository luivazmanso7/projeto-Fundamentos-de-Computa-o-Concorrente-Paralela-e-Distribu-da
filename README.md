# DistribCalc – Arquitetura Distribuída para Cálculo de Primos

Este projeto demonstra uma arquitetura cliente-servidor desenvolvida em Python, explorando conceitos de sistemas distribuídos, concorrência e paralelismo. O servidor aceita múltiplas conexões simultâneas via TCP, delega computações CPU-bound para um pool de processos e mantém métricas sincronizadas com mecanismos de exclusão mútua. O cliente fornece uma interface interativa que envia comandos e apresenta respostas em tempo real utilizando uma thread dedicada para escuta.

## Estrutura do Repositório

- `src/distribcalc/` – código fonte do servidor, cliente, protocolo e gerador de relatório.
- `tests/` – testes automatizados de funções de cálculo.
- `docs/artigo.pdf` – artigo em formato PDF gerado com ReportLab.
- `.venv/` – ambiente virtual opcional (criado ao instalar dependências localmente).

## Pré-requisitos

- Python 3.10 ou superior.
- Recomenda-se criar um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

- Instalação das dependências:

```bash
pip install -e .
```

Para incluir ferramentas de desenvolvimento (pytest), utilize:

```bash
pip install -e .[dev]
```

## Execução do Servidor

```bash
source .venv/bin/activate  # caso esteja utilizando o ambiente virtual
PYTHONPATH=src python -m distribcalc.server
```

O servidor ficará escutando em `127.0.0.1:9090` e exibirá logs a cada conexão.

## Execução do Cliente

Em outro terminal:

```bash
source .venv/bin/activate
PYTHONPATH=src python -m distribcalc.client
```

Comandos disponíveis no cliente:

- `prime <n>` – verifica se `n` é primo.
- `range <início> <fim>` – lista os primos no intervalo.
- `count <início> <fim>` – conta os primos no intervalo.
- `stats` – obtém métricas do servidor.
- `exit` – encerra o cliente.

## Testes Automatizados

```bash
source .venv/bin/activate
PYTHONPATH=src pytest
```

## Geração do Artigo em PDF

O artigo em `docs/artigo.pdf` pode ser regenerado a qualquer momento:

```bash
source .venv/bin/activate
PYTHONPATH=src python -m distribcalc.report
```

## Como a Arquitetura Atende aos Requisitos

- **Arquitetura distribuída**: Servidor TCP multi-thread + múltiplos clientes.
- **Concorrência**: Threads independentes para cada conexão de cliente.
- **Paralelismo**: `ProcessPoolExecutor` para cálculos intensivos de primos.
- **Sincronização**: `threading.Lock` garante consistência nas métricas do servidor.
- **Comunicação**: Mensagens JSON bidirecionais sobre sockets TCP.


