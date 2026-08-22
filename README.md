# Exploit Script

Este repositório contém um script em Python para testar um payload baseado em `regex` em uma requisição `POST` e tentar reconstruir um valor caractere por caractere.

## Arquivo principal

- `exploit.py`: executa a lógica principal de tentativa e validação.

## Como funciona

O script:

1. Define uma URL alvo fixa.
2. Envia requisições `POST` com os campos:
   - `username[$regex]`
   - `password[$ne]`
3. Testa caracteres candidatos até encontrar um que produza a resposta esperada.
4. Acumula os caracteres encontrados e continua o processo.

## Requisitos

- Python 3
- Biblioteca `requests`

Instalação da dependência:

```bash
pip install requests
```

## Execução

```bash
python3 exploit.py
```

## Configurações do script

No arquivo `exploit.py`, estes valores controlam o comportamento:

- `TARGET_URL`: endereço do alvo
- `FLAG_PREFIX`: string usada para validar a resposta
- `REQUEST_TIMEOUT`: tempo limite da requisição
- `INVALID_REGEX_CHARS`: caracteres ignorados no brute force

## Observações

- O script usa `requests.Session()` para reaproveitar conexões.
- Se nenhuma combinação funcionar, o script lança um erro informando que não encontrou correspondência.
- `Ctrl+C` interrompe a execução e mostra o valor parcial descoberto.

## Aviso

Use este código apenas em ambientes próprios, autorizados ou de laboratório.
