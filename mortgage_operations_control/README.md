# Mortgage Operations Control

Aplicação local para acompanhar a jornada operacional de contratos imobiliários: etapa atual, responsável, pendências, SLA e histórico.

## Executar

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

O banco SQLite `data/mortgage_operations.db` é criado automaticamente na primeira execução. A carteira local contém 250 contratos demonstrativos fictícios, distribuídos pelas etapas do fluxo. Os 250 registros estão classificados: 107 têm pendências abertas e 143 estão marcados como “Sem pendência em aberto”; não há campos de pendência vazios. A função `gerar_carteira_demo(250)` em `database.py` completa uma carteira existente até 250 sem duplicar os contratos demonstrativos.

## Funcionalidades

- Painel com indicadores, distribuição por etapa, alertas de SLA e processos parados.
- Cadastro, consulta, edição e conclusão de contratos.
- Atribuição de responsável e acompanhamento de pendências.
- Histórico de alterações de etapa, responsável, prazo e pendência.
- Filtros por etapa, responsável e situação de SLA.
- Exportação da carteira filtrada em CSV.

## Fluxo e regras de SLA

O fluxo é apresentado em quatro frentes: **Análise técnica da operação · Preparação/análise documental**, **Análise técnica da operação · Engenharia**, **Contrato** e **Liberação dos valores**. Ao final, o processo pode ser marcado como concluído.

Os prazos D+1, D+2, D+3 e D+5 são calculados em dias úteis a partir da entrada na etapa; fins de semana não contam e feriados não são descontados. Na etapa **Assinatura**, informe a data combinada. **Registro do contrato no cartório** e **Processo concluído** aparecem como “Sem SLA”.

| Frente | Etapa | SLA |
|---|---|---:|
| Preparação/análise documental | Validação pré engenharia | D+1 |
| Preparação/análise documental | Pendência da pasta; validação da pasta; recebimento de matrícula interna; análise documental; pendência documental; reanálise documental; análise/pendência de resseguro | D+3 cada |
| Preparação/análise documental | Esclarecimento de qualificação; inclusão de vaga autônoma | D+5 cada |
| Engenharia | Vistoria do imóvel; esclarecimento para vistoria; análise de risco ambiental; confirmação de pagamento da tarifa; divergência do valor de avaliação; tratamento de recusa do imóvel; tratamento de recusa do risco ambiental | D+5 cada |
| Contrato | Confirmação de valores | D+2 |
| Contrato | Resgate do FGTS, quando houver | D+5 |
| Contrato | Emissão de contrato | D+3 |
| Contrato | Assinatura | Data combinada |
| Contrato | Conferência/validação de assinaturas; ajuste, remissão ou aditivo/em tempo | D+3 cada |
| Contrato | Registro do contrato no cartório | Sem SLA |
| Liberação dos valores | Contrato registrado + matrícula com alienação; pagamento ao vendedor | D+5 cada |

## Estrutura

- `app.py`: interface Streamlit e fluxo de interação.
- `domain.py`: entidades e regras operacionais.
- `database.py`: persistência SQLite e trilha de auditoria.
- `data/`: banco local criado automaticamente.

Um processo é considerado parado após 5 dias corridos sem movimentação; esse limite pode ser ajustado em `domain.py`. Contratos da versão anterior do fluxo são atualizados automaticamente na próxima inicialização.
