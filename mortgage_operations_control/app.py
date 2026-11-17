"""Painel de Acompanhamento da jornada de contratos imobiliários."""

import base64
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from database import excluir_contrato, historico, inicializar, listar_contratos, salvar_contrato
from domain import (DIAS_PARA_ALERTA, DIAS_PARA_PARADO, ETAPA_CONCLUIDA,
                    ETAPA_DATA_COMBINADA, ETAPAS, ETAPAS_POR_FRENTE,
                    ETAPAS_SEM_SLA, SEM_PENDENCIA, SLA_DIAS)

LOGO_SANTANDER = Path(__file__).parent / "logo_santander.png"
LOGO_MARCA = Path(__file__).parent / "Santander-Logo-.png"
LOGO_MARCA_BASE64 = base64.b64encode(LOGO_MARCA.read_bytes()).decode("ascii")
ETAPAS_POR_FRENTE_UI = {**ETAPAS_POR_FRENTE, "ENCERRAMENTO": [ETAPA_CONCLUIDA]}
_ROTULOS_AREAS = ["Análise documental", "Engenharia", "Contrato", "Liberação de valores"]
AREA_POR_ETAPA = {
    etapa: area
    for (frente, etapas), area in zip(ETAPAS_POR_FRENTE.items(), _ROTULOS_AREAS)
    for etapa in etapas
}
AREA_POR_ETAPA[ETAPA_CONCLUIDA] = "Liberação de valores"
CORES_AREAS = {
    "Análise documental": "#ec0000",
    "Engenharia": "#f28c00",
    "Contrato": "#7d1d1d",
    "Liberação de valores": "#53616d",
}

st.set_page_config(page_title="Santander | Mortgage Operations Control", page_icon=str(LOGO_SANTANDER), layout="wide", initial_sidebar_state="expanded")
inicializar()

st.markdown("""
<style>
.stApp { background:#f7f7f7; color:#222; font-family:Arial,Helvetica,sans-serif; }
h1,h2,h3 { font-family:Arial,Helvetica,sans-serif !important; letter-spacing:-.025em; color:#222; }
.block-container { max-width:none; padding:1.5rem 2rem 3rem; }
header[data-testid="stHeader"] { background:#fff; }
.stApp [data-testid="stSidebar"] { background:#ec0000; border-right:0; min-width:290px !important; max-width:290px !important; }
.stApp [data-testid="stSidebar"] > div:first-child { padding:1.5rem 1.25rem; }
.stApp [data-testid="stSidebar"] * { color:#fff; }
.sidebar-brand { padding:.7rem 0 1.6rem; }
.sidebar-logo { display:flex; align-items:center; margin:-.25rem 0 1.25rem; }
.sidebar-logo img { width:200px; height:66px; object-fit:cover; object-position:center; display:block; border-radius:2px; }
.sidebar-title { color:#fff; font-size:1.18rem; line-height:1.4; font-weight:700; }
.sidebar-subtitle { color:#fff; opacity:.9; font-size:.72rem; margin-top:.6rem; }
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] { position:static; background:transparent; width:100%; min-height:0 !important; margin:0 0 1.5rem; padding:0; display:block; }
.stApp [data-testid="stSidebar"] [data-testid="stRadio"]::before,
.stApp [data-testid="stSidebar"] [data-testid="stRadio"]::after { content:none; }
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] > div { display:block; }
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] { display:flex; flex-direction:column; align-items:stretch; gap:.12rem; width:100%; }
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] label { width:100%; color:#fff !important; border:0 !important; border-radius:4px; padding:.48rem .25rem; font-weight:500; }
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { color:#fff !important; background:#c90000; font-weight:700; }
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] input { accent-color:#fff; }
.stApp [data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.42); margin:1.25rem 0; }
.stApp [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color:rgba(255,255,255,.82); }
.eyebrow { color:#ec0000; font-size:.73rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.4rem; }
.hero { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1.4rem; }
.subtle { color:#666; font-size:.94rem; margin-top:-.45rem; }
.metric-card { background:#fff; border:1px solid #e5e5e5; border-top:3px solid #ec0000; border-radius:4px; padding:17px 19px 15px; min-height:112px; box-shadow:0 2px 7px rgba(0,0,0,.035); }
.metric-label { color:#666; font-size:.81rem; font-weight:600; }
.metric-value { color:#ec0000; font-family:Arial,Helvetica,sans-serif; font-size:1.9rem; font-weight:700; line-height:1.3; margin-top:7px; }
.metric-foot { color:#888; font-size:.75rem; margin-top:2px; }
.section-title { font-family:Arial,Helvetica,sans-serif; font-size:1.06rem; font-weight:700; margin:.35rem 0 .8rem; color:#333; }
.stButton > button { border-radius:4px; font-weight:650; border-color:#ec0000; }
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button { background:#ec0000; color:#fff; border-color:#ec0000; }
.stButton > button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button:hover { background:#c90000; border-color:#c90000; color:#fff; }
[data-testid="stDataFrame"] { border:1px solid #e3e3e3; border-radius:4px; overflow:hidden; }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="textarea"] { border-radius:4px; }
@media (max-width:700px) { .stApp [data-testid="stSidebar"] { min-width:250px !important; max-width:250px !important; } .block-container { padding:.8rem 1rem 2rem; } }
</style>
""", unsafe_allow_html=True)


def carregar():
    df = listar_contratos()
    if df.empty:
        return df
    df["prazo_sla"] = pd.to_datetime(df["prazo_sla"], errors="coerce").dt.date
    df["atualizado_em"] = pd.to_datetime(df["atualizado_em"], errors="coerce")
    pendencia_normalizada = df["pendencia"].fillna("").astype(str).str.strip().str.casefold()
    df["pendencia_aberta"] = pendencia_normalizada.ne("") & pendencia_normalizada.ne(SEM_PENDENCIA.casefold())
    hoje = date.today()
    df["dias_para_vencer"] = df["prazo_sla"].apply(lambda d: (d - hoje).days if pd.notna(d) else 99999)
    df["dias_parado"] = (pd.Timestamp.now() - df["atualizado_em"]).dt.days.clip(lower=0).fillna(0).astype(int)
    df["situacao_sla"] = df.apply(
        lambda r: "Concluído" if r["etapa"] == ETAPA_CONCLUIDA else (
            "Sem SLA" if pd.isna(r["prazo_sla"]) else (
                "Fora do SLA" if r["dias_para_vencer"] < 0 else (
                    "Próximo do vencimento" if r["dias_para_vencer"] <= DIAS_PARA_ALERTA else "No prazo"
                )
            )
        ), axis=1
    )
    df["parado"] = (df["etapa"] != ETAPA_CONCLUIDA) & (df["dias_parado"] >= DIAS_PARA_PARADO)
    return df


def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def cabecalho(kicker, titulo, descricao):
    st.markdown(f'<div class="eyebrow">{kicker}</div><h1 style="margin:0 0 .7rem">{titulo}</h1><div class="subtle">{descricao}</div>', unsafe_allow_html=True)


def cartao_metrica(col, rotulo, valor, detalhe, cor="#ec0000"):
    col.markdown(f'<div class="metric-card"><div class="metric-label">{rotulo}</div><div class="metric-value" style="color:{cor}">{valor}</div><div class="metric-foot">{detalhe}</div></div>', unsafe_allow_html=True)


def tabela(df, colunas=None):
    if df.empty:
        st.info("Nenhum contrato encontrado para os filtros selecionados.")
        return
    exibicao = df.copy()
    exibicao["valor"] = exibicao["valor"].apply(moeda)
    exibicao["pendencia"] = exibicao["pendencia"].apply(lambda p: "Sem pendência" if str(p).strip().casefold() == SEM_PENDENCIA.casefold() else p)
    exibicao["prazo_sla"] = exibicao["prazo_sla"].apply(lambda d: d.strftime("%d/%m/%Y") if pd.notna(d) else "Sem SLA")
    exibicao["dias_parado"] = exibicao["dias_parado"].apply(lambda n: f"{n} dias")
    exibicao["dias_para_vencer"] = exibicao.apply(lambda r: "Sem SLA" if r["situacao_sla"] in ("Sem SLA", "Concluído") else (f"Vencido há {abs(r['dias_para_vencer'])} dias" if r["dias_para_vencer"] < 0 else f"{r['dias_para_vencer']} dias"), axis=1)
    exibicao = exibicao.rename(columns={"numero":"Contrato", "cliente":"Cliente", "valor":"Valor", "etapa":"Etapa atual", "responsavel":"Responsável", "pendencia":"Pendência", "prazo_sla":"Prazo SLA", "situacao_sla":"Situação SLA", "dias_parado":"Sem movimentação", "dias_para_vencer":"Prazo restante"})
    colunas = colunas or ["Contrato", "Cliente", "Valor", "Etapa atual", "Responsável", "Pendência", "Prazo SLA", "Situação SLA", "Sem movimentação"]
    st.dataframe(exibicao[colunas], hide_index=True, use_container_width=True)


def formulario(dados=None, prefixo="novo"):
    existente = dados is not None
    hoje = date.today()
    frente_atual = next((frente for frente, etapas in ETAPAS_POR_FRENTE_UI.items() if existente and dados["etapa"] in etapas), next(iter(ETAPAS_POR_FRENTE_UI)))
    frente_key = f"frente_{prefixo}"
    frente = st.selectbox("Frente operacional *", list(ETAPAS_POR_FRENTE_UI), index=list(ETAPAS_POR_FRENTE_UI).index(frente_atual), key=frente_key)
    etapas_disponiveis = ETAPAS_POR_FRENTE_UI[frente]
    etapa_atual = dados["etapa"] if existente and dados["etapa"] in etapas_disponiveis else etapas_disponiveis[0]
    etapa = st.selectbox("Etapa atual *", etapas_disponiveis, index=etapas_disponiveis.index(etapa_atual), key=f"etapa_{prefixo}_{frente}")
    prazo_default = dados["prazo_sla"] if existente and pd.notna(dados["prazo_sla"]) else hoje
    if etapa == ETAPA_DATA_COMBINADA:
        prazo = st.date_input("Data combinada para assinatura *", value=prazo_default, format="DD/MM/YYYY", key=f"prazo_{prefixo}")
        st.caption("O prazo da assinatura segue a data acordada com o cliente.")
    elif etapa in ETAPAS_SEM_SLA:
        prazo = None
        st.caption("Esta etapa não possui SLA de prazo.")
    else:
        prazo = None
        st.caption(f"SLA desta etapa: D+{SLA_DIAS[etapa]} dias úteis. O prazo é calculado ao entrar na etapa.")
    with st.form(f"form_{prefixo}", clear_on_submit=not existente):
        c1, c2, c3 = st.columns(3)
        numero = c1.text_input("Número do contrato *", value=str(dados["numero"]) if existente else "", disabled=existente, placeholder="MOR-2026-009")
        cliente = c2.text_input("Nome do cliente *", value=str(dados["cliente"]) if existente else "")
        documento = c3.text_input("CPF/CNPJ", value=str(dados["documento"] or "") if existente else "")
        c4, c5 = st.columns(2)
        valor = c4.number_input("Valor do financiamento (R$) *", min_value=0.0, step=10000.0, value=float(dados["valor"]) if existente else 0.0)
        responsavel = c5.text_input("Responsável *", value=str(dados["responsavel"]) if existente else "", placeholder="Nome do analista")
        pendencia_atual = str(dados["pendencia"] or "") if existente else ""
        if pendencia_atual.strip().casefold() == SEM_PENDENCIA.casefold():
            pendencia_atual = ""
        pendencia = st.text_area("Pendência em aberto", value=pendencia_atual, placeholder="Descreva o documento ou deixe vazio para indicar que não há pendência.", height=90)
        enviar = st.form_submit_button("Salvar alterações" if existente else "Cadastrar contrato", type="primary", use_container_width=True)
        if enviar:
            if not (numero.strip() if not existente else True) or not cliente.strip() or not responsavel.strip():
                st.error("Preencha número do contrato, cliente e responsável.")
            elif valor <= 0:
                st.error("O valor do financiamento deve ser maior que zero.")
            else:
                registro = {"numero": numero.strip() if not existente else str(dados["numero"]), "cliente": cliente.strip(), "documento": documento.strip(), "valor": valor, "etapa": etapa, "responsavel": responsavel.strip(), "pendencia": pendencia.strip() or SEM_PENDENCIA, "prazo_sla": prazo.isoformat() if prazo else ""}
                try:
                    salvar_contrato(registro, int(dados["id"]) if existente else None)
                    st.success("Contrato atualizado." if existente else "Contrato cadastrado.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Não foi possível salvar o contrato: {exc}")


with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
      <div class="sidebar-logo"><img src="data:image/png;base64,{LOGO_MARCA_BASE64}" alt="Santander"></div>
      <div class="sidebar-title">Mortgage<br>Operations Control</div>
      <div class="sidebar-subtitle">BACKOFFICE · OPERAÇÕES</div>
    </div>
    """, unsafe_allow_html=True)
    pagina = st.radio("NAVEGAÇÃO", ["Visão geral", "Contratos", "Pendências e SLA", "Histórico"], label_visibility="visible")
    st.markdown("---")
    st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
    st.caption("Dados armazenados localmente em SQLite")

df = carregar()

if pagina == "Visão geral":
    cabecalho("CENTRAL DE OPERAÇÕES", "Painel de Acompanhamento", "Visibilidade da carteira, dos prazos e das próximas ações do time.")
    st.write("")
    total = len(df)
    concluidos = int((df["etapa"] == ETAPA_CONCLUIDA).sum()) if total else 0
    com_pendencia = int(df["pendencia_aberta"].sum()) if total else 0
    fora = int((df["situacao_sla"] == "Fora do SLA").sum()) if total else 0
    proximos = int((df["situacao_sla"] == "Próximo do vencimento").sum()) if total else 0
    k = st.columns(5)
    cartao_metrica(k[0], "Processos recebidos", total, "Contratos na carteira")
    cartao_metrica(k[1], "Concluídos", concluidos, f"{concluidos / total:.0%} da carteira" if total else "Sem contratos", "#ec0000")
    cartao_metrica(k[2], "Com pendências", com_pendencia, "Aguardam ação ou documento", "#bd7a24")
    cartao_metrica(k[3], "Fora do SLA", fora, "Prazo operacional vencido", "#c25350")
    cartao_metrica(k[4], "Vencem em até 3 dias", proximos, "Prioridade de acompanhamento", "#bd7a24")
    st.write("")
    left, right = st.columns([1.22, .78], gap="large")
    with left:
        st.markdown('<div class="section-title">Distribuição dos processos por etapa</div>', unsafe_allow_html=True)
        if total:
            dist = df.groupby("etapa", as_index=False).size().rename(columns={"size":"Processos"})
            dist["etapa"] = pd.Categorical(dist["etapa"], categories=ETAPAS, ordered=True)
            dist = dist.sort_values("etapa")
            dist["Área de atuação"] = dist["etapa"].map(AREA_POR_ETAPA)
            fig = px.bar(dist, x="Processos", y="etapa", orientation="h", text="Processos", color="Área de atuação", color_discrete_map=CORES_AREAS, category_orders={"Área de atuação": _ROTULOS_AREAS})
            fig.update_layout(height=max(560, len(dist) * 25), margin=dict(l=0,r=20,t=10,b=55), plot_bgcolor="white", paper_bgcolor="white", font=dict(family="Arial", color="#444"), xaxis=dict(showgrid=True, gridcolor="#ededed", title="Contratos", dtick=1), yaxis=dict(title="", autorange="reversed"), showlegend=True, legend=dict(title="Área de atuação", orientation="h", y=-.15, x=0, font=dict(size=10)))
            fig.update_traces(textposition="outside", cliponaxis=False, marker_cornerradius=5)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        else:
            st.info("Cadastre um contrato para visualizar a distribuição.")
    with right:
        st.markdown('<div class="section-title">Situação da carteira</div>', unsafe_allow_html=True)
        if total:
            sla = df["situacao_sla"].value_counts().reindex(["No prazo", "Próximo do vencimento", "Fora do SLA", "Sem SLA", "Concluído"], fill_value=0).rename_axis("Situação").reset_index(name="Processos")
            cores = {"No prazo":"#ec0000", "Próximo do vencimento":"#ff8a00", "Fora do SLA":"#a50000", "Sem SLA":"#b7b7b7", "Concluído":"#4b4b4b"}
            fig2 = px.pie(sla[sla["Processos"] > 0], values="Processos", names="Situação", hole=.68, color="Situação", color_discrete_map=cores)
            fig2.update_layout(height=300, margin=dict(l=0,r=0,t=5,b=5), paper_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=-.13, x=.5, xanchor="center", font=dict(size=11)), font=dict(family="Arial", color="#444"))
            fig2.update_traces(textinfo="percent", textfont_size=12)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        st.markdown('<div class="section-title" style="margin-top:.6rem">Atenção necessária</div>', unsafe_allow_html=True)
        urgentes = df[(df["situacao_sla"].isin(["Fora do SLA", "Próximo do vencimento"])) | df["parado"]] if total else df
        if urgentes.empty:
            st.success("Nenhum processo com alerta de prazo ou parado.")
        else:
            for _, row in urgentes.sort_values(["dias_para_vencer", "dias_parado"]).head(4).iterrows():
                tipo = "Fora do SLA" if row["situacao_sla"] == "Fora do SLA" else ("Vence em breve" if row["situacao_sla"] == "Próximo do vencimento" else "Sem movimentação")
                st.markdown(f"**{row['numero']} · {row['cliente']}**  \n{tipo} · {row['responsavel']} · {row['dias_parado']} dias sem atualização")
    st.markdown('<div class="section-title" style="margin-top:1rem">Carteira operacional</div>', unsafe_allow_html=True)
    tabela(df.sort_values(["dias_para_vencer", "dias_parado"]).head(8))

elif pagina == "Contratos":
    cabecalho("GESTÃO DA CARTEIRA", "Contratos", "Cadastre operações, atualize a etapa e consulte os dados de cada financiamento.")
    tab1, tab2, tab3 = st.tabs(["Consultar carteira", "Novo contrato", "Editar contrato"])
    with tab1:
        if not df.empty:
            f1, f2 = st.columns(2)
            etapas_sel = f1.multiselect("Etapas", ETAPAS, placeholder="Todas as etapas")
            responsáveis = sorted(df["responsavel"].dropna().unique().tolist())
            resp_sel = f2.multiselect("Responsáveis", responsáveis, placeholder="Todos os responsáveis")
            filtrado = df.copy()
            if etapas_sel: filtrado = filtrado[filtrado["etapa"].isin(etapas_sel)]
            if resp_sel: filtrado = filtrado[filtrado["responsavel"].isin(resp_sel)]
            pesquisa = st.text_input("Buscar por contrato ou cliente", placeholder="Digite para pesquisar")
            if pesquisa: filtrado = filtrado[filtrado["numero"].str.contains(pesquisa, case=False, na=False) | filtrado["cliente"].str.contains(pesquisa, case=False, na=False)]
            tabela(filtrado)
            csv = filtrado.drop(columns=["atualizado_em", "criado_em"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇  Exportar carteira filtrada (CSV)", csv, file_name="carteira_operacional.csv", mime="text/csv")
        else:
            st.info("A carteira está vazia. Use a aba Novo contrato para começar.")
    with tab2:
        formulario()
    with tab3:
        if df.empty:
            st.info("Cadastre um contrato antes de editar.")
        else:
            opcoes = {f"{r.numero} · {r.cliente}": r.id for r in df.itertuples()}
            selecionado = st.selectbox("Contrato para editar", list(opcoes), key="editar_selecao")
            registro = df[df["id"] == opcoes[selecionado]].iloc[0]
            formulario(registro, f"editar_{int(registro['id'])}")
            st.markdown("---")
            confirmar = st.checkbox("Confirmo a exclusão deste contrato e do histórico vinculado", key="confirmar_exclusao")
            if st.button("Excluir contrato", disabled=not confirmar):
                excluir_contrato(int(registro["id"]))
                st.success("Contrato excluído.")
                st.rerun()

elif pagina == "Pendências e SLA":
    cabecalho("GESTÃO DE EXCEÇÕES", "Pendências e prazos", "Priorize contratos vencidos, próximos do vencimento e sem movimentação recente.")
    c1, c2, c3 = st.columns(3)
    pendentes = df[df["pendencia_aberta"]] if not df.empty else df
    atrasados = df[df["situacao_sla"] == "Fora do SLA"] if not df.empty else df
    parados = df[df["parado"]] if not df.empty else df
    cartao_metrica(c1, "Pendências em aberto", len(pendentes), "Itens aguardando resolução", "#bd7a24")
    cartao_metrica(c2, "Fora do SLA", len(atrasados), "Precisam de ação imediata", "#c25350")
    cartao_metrica(c3, "Parados há 5+ dias", len(parados), "Sem atualização de etapa", "#bd7a24")
    st.write("")
    categoria = st.selectbox("Exibir", ["Todos os alertas", "Pendências", "Fora do SLA", "Próximos do vencimento", "Processos parados"])
    if categoria == "Pendências": vis = pendentes
    elif categoria == "Fora do SLA": vis = atrasados
    elif categoria == "Próximos do vencimento": vis = df[df["situacao_sla"] == "Próximo do vencimento"] if not df.empty else df
    elif categoria == "Processos parados": vis = parados
    else: vis = df[df["pendencia_aberta"] | df["situacao_sla"].isin(["Fora do SLA", "Próximo do vencimento"]) | df["parado"]] if not df.empty else df
    tabela(vis.sort_values(["dias_para_vencer", "dias_parado"]) if not vis.empty else vis)
    st.caption(f"Processo parado: sem atualização por {DIAS_PARA_PARADO} dias ou mais. O D+N do SLA considera dias úteis (sem feriados); alerta de vencimento: até {DIAS_PARA_ALERTA} dias.")

else:
    cabecalho("TRILHA DE AUDITORIA", "Histórico de movimentações", "Consulte quando cada operação mudou de etapa, prazo, responsável ou pendência.")
    if df.empty:
        st.info("Ainda não há contratos para consultar.")
    else:
        opcoes = {f"{r.numero} · {r.cliente}": int(r.id) for r in df.itertuples()}
        selecionado = st.selectbox("Contrato", list(opcoes))
        registro = df[df["id"] == opcoes[selecionado]].iloc[0]
        m1, m2, m3 = st.columns(3)
        m1.metric("Etapa atual", registro["etapa"])
        m2.metric("Responsável", registro["responsavel"])
        m3.metric("Situação SLA", registro["situacao_sla"])
        log = historico(opcoes[selecionado])
        if log.empty:
            st.info("Este contrato ainda não possui movimentações registradas.")
        else:
            log["data_hora"] = pd.to_datetime(log["data_hora"]).dt.strftime("%d/%m/%Y %H:%M")
            log = log.rename(columns={"data_hora":"Data e hora", "campo":"Campo", "valor_anterior":"Valor anterior", "valor_novo":"Novo valor", "usuario":"Usuário"})
            st.dataframe(log, hide_index=True, use_container_width=True)
