from __future__ import annotations

import html
from pathlib import Path
import shutil

from .audit import auditar
from .demo_data import gerar_dossies
from .reporting import gerar_relatorios
from .storage import carregar_processo, salvar_auditoria


def executar_lote(raiz: str | Path = ".", quantidade: int = 250) -> Path:
    raiz = Path(raiz)
    entrada = raiz / "data" / "processos"
    saida = raiz / "relatorios"
    banco = raiz / "data" / "auditorias.sqlite3"
    # Regenera sempre para aplicar alterações às regras e ao gerador do exemplo.
    caminhos = gerar_dossies(entrada, quantidade=quantidade)

    linhas = []
    pendentes = 0
    revisao = 0
    for caminho in caminhos:
        processo = carregar_processo(caminho)
        resultado = auditar(processo)
        gerar_relatorios(resultado, saida)
        salvar_auditoria(banco, processo, resultado)
        if resultado.tem_pendencias:
            pendentes += 1
        if resultado.precisa_revisao_manual:
            revisao += 1
        badge = "Com pendências" if resultado.tem_pendencias else "Sem pendências"
        klass = "warning" if resultado.tem_pendencias else "success"
        linhas.append(f'<tr><td><a href="{html.escape(processo.contrato)}_relatorio.html">{html.escape(processo.contrato)}</a></td><td>{html.escape(processo.cliente.nome)}</td><td><span class="badge {klass}">{badge}</span></td><td>{len(resultado.inconsistencias)}</td><td>{"Sim" if resultado.precisa_revisao_manual else "Não"}</td></tr>')

    index = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Painel de conferência documental</title><style>
*{{box-sizing:border-box}}body{{margin:0;padding:0 24px 24px;background:#f5f6f7;color:#171717;font:14px/1.5 Arial,sans-serif}}.brand-bar{{height:72px;margin:0 -24px 24px;padding-left:max(24px,calc((100% - 1100px)/2));overflow:hidden;background:#ec0000}}.brand-bar img{{display:block;width:190px;height:72px;object-fit:cover;object-position:center}}main{{max-width:1100px;margin:auto;padding:20px;background:white;border:1px solid #dedede;border-radius:13px}}h1{{font-size:21px;margin:0 0 4px}}.sub{{color:#666;margin:0 0 18px}}.cards{{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}}.card{{min-width:150px;padding:14px 16px;border:1px solid #eee;border-radius:10px}}.num{{font-size:23px;font-weight:bold}}.label{{color:#666;font-size:12px}}.toolbar{{display:flex;gap:10px;margin:18px 0}}input,select{{padding:10px;border:1px solid #ccc;border-radius:7px;font-size:14px}}input{{flex:1}}.table-wrap{{overflow:auto}}table{{border-collapse:collapse;width:100%;min-width:650px}}th,td{{padding:10px 8px;border-bottom:1px solid #eee;text-align:left}}th{{background:#fafafa}}a{{color:#155eef;text-decoration:none}}a:hover{{text-decoration:underline}}.badge{{display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px}}.success{{color:#087443;background:#d7f3e5}}.warning{{color:#a13b00;background:#ffe5d7}}footer{{margin-top:16px;color:#666;font-size:11px}}@media(max-width:540px){{body{{padding:0 10px 10px}}.brand-bar{{height:62px;margin:0 -10px 14px;padding-left:10px}}.brand-bar img{{height:62px;width:164px}}}}
</style></head><body><header class="brand-bar"><img src="Santander-Logo-.png" alt="Santander"></header><main><h1>Conferência documental — Carteira de contratos</h1><p class="sub">Demonstração com {quantidade} contratos e dados integralmente fictícios.</p><div class="cards"><div class="card"><div class="num">{quantidade}</div><div class="label">Contratos analisados</div></div><div class="card"><div class="num">{quantidade-pendentes}</div><div class="label">Sem pendências</div></div><div class="card"><div class="num">{pendentes}</div><div class="label">Com pendências</div></div><div class="card"><div class="num">{revisao}</div><div class="label">Revisão manual</div></div></div><div class="toolbar"><input id="q" placeholder="Buscar contrato ou cliente"><select id="f"><option value="todos">Todos os resultados</option><option value="pendente">Com pendências</option><option value="ok">Sem pendências</option></select></div><div class="table-wrap"><table><thead><tr><th>Contrato</th><th>Cliente fictício</th><th>Resultado</th><th>Apontamentos</th><th>Revisão manual</th></tr></thead><tbody id="rows">{''.join(linhas)}</tbody></table></div><footer>Dados demonstrativos, sem correspondência com clientes reais. A ferramenta auxilia a conferência, sem substituir a validação humana.</footer></main><script>const q=document.querySelector('#q'),f=document.querySelector('#f');function filtrar(){{for(const r of document.querySelectorAll('#rows tr')){{const texto=r.innerText.toLowerCase(),pend=r.cells[2].innerText.includes('Com pendências');r.hidden=!(texto.includes(q.value.toLowerCase())&&(f.value==='todos'||(f.value==='pendente')===pend));}}}}q.addEventListener('input',filtrar);f.addEventListener('change',filtrar);</script></body></html>'''
    logo = Path(__file__).resolve().parent.parent / "Santander-Logo-.png"
    if logo.exists():
        shutil.copy2(logo, saida / logo.name)
    arquivo = saida / "index.html"
    arquivo.write_text(index, encoding="utf-8")
    return arquivo
