# Conferência documental de financiamento imobiliário

Ferramenta de linha de comando para organizar o checklist por contrato, apontar documentos ausentes ou vencidos, comparar dados cadastrais, sinalizar possíveis duplicidades e gerar relatórios de pendências. Os arquivos da pasta `data` são fictícios e servem apenas para demonstração.

## Requisitos e execução

Python 3.10 ou superior e pandas.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m doccheck.cli
```

Também é possível iniciar pela raiz do projeto com `python app.py`. Esse modo cria/recria 250 dossiês fictícios em `data/processos/`, audita todos, gera um relatório por contrato e cria o painel `relatorios/index.html` com busca, filtro e indicadores do lote.

O comando padrão analisa `data/processo_demo.json`, salva HTML visual, Markdown e CSV em `relatorios/` e persiste o resultado em `data/auditorias.sqlite3`. Abra o arquivo HTML no navegador para ver o resumo com indicadores coloridos e ações sugeridas.

Para informar outro processo:

```powershell
python -m doccheck.cli caminho\processo.json --saida relatorios --db data\auditorias.sqlite3
```

## Formato dos dados

O JSON deve conter `contrato`, `cliente`, `documentos` e, opcionalmente, `checklist` e `dados_imovel`. Cada documento usa `tipo`, `recebido`, `nome_arquivo`, `data_validade`, `dados` e `hash_conteudo`. Tipos usados no checklist demo: `identificacao`, `cpf`, `comprovante_residencia`, `comprovante_renda`, `documentacao_imovel`, `certidoes` e `contrato_financiamento`. Datas usam ISO `AAAA-MM-DD`.

Os campos disponíveis no cadastro do cliente são comparados quando presentes no documento: nome, CPF, endereço e renda mensal. A duplicidade é sinalizada quando hash ou nome de arquivo coincide. A revisão manual indica divergência, duplicidade ou impossibilidade de validar uma data. A lista de validade é configurável em `doccheck/audit.py`.

## Estrutura

- `doccheck/models.py`: classes Cliente, Documento, Processo e resultado.
- `doccheck/audit.py`: checklist e regras de conferência.
- `doccheck/storage.py`: leitura JSON e persistência SQLite.
- `doccheck/reporting.py`: geração de relatórios Markdown/CSV com Pandas.
- `data/processo_demo.json`: dossiê fictício com pendências demonstrativas.

Esta versão confere metadados informados no JSON; não extrai texto ou datas diretamente de PDFs ou imagens.
