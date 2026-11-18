from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from .models import ResultadoAuditoria


def gerar_relatorios(resultado: ResultadoAuditoria, pasta: str | Path) -> tuple[Path, Path, Path]:
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    logo = Path(__file__).resolve().parent.parent / "Santander-Logo-.png"
    if logo.exists():
        shutil.copy2(logo, pasta / logo.name)
    linhas = [{"Documento": i.documento, "Resultado": i.status, "Detalhe": i.detalhe,
               "Ação sugerida": i.acao, "Revisão manual": "Sim" if i.revisao_manual else "Não"}
              for i in resultado.inconsistencias]
    csv = pasta / f"{resultado.contrato}_inconsistencias.csv"
    pd.DataFrame(linhas, columns=["Documento", "Resultado", "Detalhe", "Ação sugerida", "Revisão manual"]).to_csv(csv, index=False, encoding="utf-8-sig")
    status = "Com pendências" if resultado.tem_pendencias else "Sem pendências"
    texto = [f"# Conferência documental — Contrato {resultado.contrato}", "", f"**Resultado da conferência:** {status}",
             f"**Revisão manual:** {'Sim' if resultado.precisa_revisao_manual else 'Não'}", "", "## Documentos — Resultado", ""]
    if not linhas:
        texto.append("Todos os documentos do checklist foram conferidos sem inconsistências.")
    else:
        texto += ["| Documento | Resultado | Detalhe | Ação sugerida |", "|---|---|---|---|"]
        texto.extend(f"| {i.documento} | {i.status} | {i.detalhe} | {i.acao} |" for i in resultado.inconsistencias)
    md = pasta / f"{resultado.contrato}_relatorio.md"
    md.write_text("\n".join(texto) + "\n", encoding="utf-8")

    # Relatório HTML autocontido para visualização no navegador.
    agrupadas: dict[str, list] = {}
    for item in resultado.inconsistencias:
        agrupadas.setdefault(item.documento, []).append(item)
    nomes = {
        "identificacao": "RG", "cpf": "CPF", "comprovante_residencia": "Comprovante de residência",
        "comprovante_renda": "Comprovante de renda", "documentacao_imovel": "Documentação do imóvel",
        "certidoes": "Certidão", "contrato_financiamento": "Contrato de financiamento",
    }
    documentos = [
        ("identificacao", "Recebido"), ("cpf", "Validado"), ("comprovante_renda", "Validado"),
        ("comprovante_residencia", "Validado"), ("certidoes", "Validado"),
        ("documentacao_imovel", "Recebido"), ("contrato_financiamento", "Recebido"),
    ]
    status_por_resultado = {
        "Ausente": ("Ausente", "warning"), "Vencido": ("Vencida", "danger"),
        "Divergente": ("Divergente", "warning"), "Possível duplicidade": ("Possível duplicidade", "warning"),
        "Data não informada": ("Revisar validade", "warning"),
    }
    linhas_html = []
    acoes: list[str] = []
    for tipo, normal in documentos:
        achados = agrupadas.get(tipo, [])
        if achados:
            primeiro = achados[0]
            rotulo, classe = status_por_resultado.get(primeiro.status, (primeiro.status, "warning"))
            for achado in achados:
                if achado.acao not in acoes:
                    acoes.append(achado.acao)
        else:
            rotulo, classe = normal, "success"
        linhas_html.append(f"<tr><td>{nomes[tipo]}</td><td><span class=\"badge {classe}\">{rotulo}</span></td></tr>")
    if resultado.tem_pendencias:
        acoes.append("Manter o processo pendente até a regularização.")
    else:
        acoes.append("Prosseguir com as próximas etapas do processo.")
    acoes_html = "\n".join(f"<li>{acao}</li>" for acao in acoes)
    resumo = "Com pendências" if resultado.tem_pendencias else "Sem pendências"
    html = f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Conferência documental — Contrato {resultado.contrato}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 0 24px 24px; background: #f5f6f7; color: #171717; font: 15px/1.5 Arial, sans-serif; }}
  .brand-bar {{ height: 72px; margin: 0 -24px 24px; padding-left: max(24px, calc((100% - 900px) / 2)); overflow: hidden; background: #ec0000; }}
  .brand-bar img {{ display: block; width: 190px; height: 72px; object-fit: cover; object-position: center; }}
  main {{ max-width: 900px; margin: 0 auto; padding: 12px; background: #fff; border: 1px solid #dedede; border-radius: 13px; }}
  h1 {{ margin: 0 0 14px; font-size: 16px; font-weight: 600; }}
  .summary {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px; color: #555; font-size: 12px; }}
  .badge {{ display: inline-block; padding: 2px 9px; border-radius: 99px; font-size: 12px; white-space: nowrap; }}
  .success {{ color: #087443; background: #d7f3e5; }} .warning {{ color: #a13b00; background: #ffe5d7; }} .danger {{ color: #b42323; background: #ffdddd; }}
  .summary .badge {{ font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; }} th, td {{ padding: 9px 0; border-bottom: 1px solid #ededed; text-align: left; }}
  th {{ font-weight: 600; }} th:last-child, td:last-child {{ width: 29%; }}
  section {{ margin-top: 22px; padding-top: 18px; border-top: 1px solid #ededed; }}
  h2 {{ margin: 0; font-size: 15px; }} ul {{ margin: 12px 0 0; padding-left: 32px; }} li {{ margin: 3px 0; }}
  footer {{ margin: 20px 0 0 32px; color: #666; font-size: 11px; }}
  @media (max-width: 540px) {{ body {{ padding: 0 10px 10px; }} .brand-bar {{ height: 62px; margin: 0 -10px 14px; padding-left: 10px; }} .brand-bar img {{ height: 62px; width: 164px; }} main {{ padding: 12px; }} th:last-child, td:last-child {{ width: 42%; }} }}
</style></head><body><header class="brand-bar"><img src="Santander-Logo-.png" alt="Santander"></header><main>
<h1>Conferência documental — Contrato {resultado.contrato}</h1>
<div class="summary"><span>Resultado da conferência</span><span class="badge {'warning' if resultado.tem_pendencias else 'success'}">{resumo}</span></div>
<table><thead><tr><th>Documento</th><th>Resultado</th></tr></thead><tbody>{''.join(linhas_html)}</tbody></table>
<section><h2>Ações sugeridas</h2><ul>{acoes_html}</ul></section>
<footer>Exemplo fictício. A ferramenta auxilia a conferência, sem substituir a validação documental humana.</footer>
</main></body></html>'''
    visual = pasta / f"{resultado.contrato}_relatorio.html"
    visual.write_text(html, encoding="utf-8")
    return md, csv, visual
