"""Persistência SQLite, cálculo dos prazos e histórico de movimentações."""

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from domain import ETAPA_CONCLUIDA, ETAPA_DATA_COMBINADA, ETAPAS, SEM_PENDENCIA, calcular_prazo_sla

DB_PATH = Path(__file__).parent / "data" / "mortgage_operations.db"

ETAPAS_ANTIGAS = {
    "Recebimento da proposta": "Validação pré engenharia",
    "Conferência cadastral": "Pendência da pasta",
    "Conferência documental": "Análise documental",
    "Análise e validação das pendências": "Pendência documental",
    "Formalização do contrato": "Emissão de contrato",
    "Acompanhamento do registro em cartório": "Registro do contrato no cartório",
    "Controle da liberação dos recursos": "Pagamento ao vendedor",
    "Conclusão do processo": ETAPA_CONCLUIDA,
}


def conectar():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _iso_prazo(etapa: str, inicio: date, combinado: str | None = None) -> str:
    data_combinada = date.fromisoformat(combinado) if combinado else None
    prazo = calcular_prazo_sla(etapa, inicio, data_combinada)
    return prazo.isoformat() if prazo else ""


def inicializar():
    with conectar() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS contratos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT NOT NULL UNIQUE,
                cliente TEXT NOT NULL,
                documento TEXT DEFAULT '',
                valor REAL NOT NULL DEFAULT 0,
                etapa TEXT NOT NULL,
                responsavel TEXT NOT NULL,
                pendencia TEXT DEFAULT '',
                prazo_sla TEXT NOT NULL DEFAULT '',
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contrato_id INTEGER NOT NULL REFERENCES contratos(id) ON DELETE CASCADE,
                data_hora TEXT NOT NULL,
                campo TEXT NOT NULL,
                valor_anterior TEXT DEFAULT '',
                valor_novo TEXT DEFAULT '',
                usuario TEXT NOT NULL DEFAULT 'Backoffice'
            );
        """)
        _migrar_fluxo_anterior(conn)
        if conn.execute("SELECT COUNT(*) FROM contratos").fetchone()[0] == 0:
            _inserir_demonstracao(conn)
        _preencher_pendencias_vazias(conn)


def _preencher_pendencias_vazias(conn) -> int:
    agora = datetime.now().isoformat(timespec="seconds")
    rows = conn.execute("SELECT id FROM contratos WHERE TRIM(COALESCE(pendencia, ''))='' ").fetchall()
    for row in rows:
        conn.execute("UPDATE contratos SET pendencia=? WHERE id=?", (SEM_PENDENCIA, row["id"]))
        conn.execute("""INSERT INTO movimentacoes
            (contrato_id, data_hora, campo, valor_anterior, valor_novo, usuario)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (row["id"], agora, "Classificação da pendência", "", SEM_PENDENCIA, "Carga demonstrativa"))
    return len(rows)


def _migrar_fluxo_anterior(conn):
    agora = datetime.now().isoformat(timespec="seconds")
    for antiga, nova in ETAPAS_ANTIGAS.items():
        rows = conn.execute("SELECT id, prazo_sla, atualizado_em FROM contratos WHERE etapa=?", (antiga,)).fetchall()
        for row in rows:
            try:
                inicio = datetime.fromisoformat(row["atualizado_em"]).date()
            except (TypeError, ValueError):
                inicio = date.today()
            prazo = _iso_prazo(nova, inicio)
            conn.execute("UPDATE contratos SET etapa=?, prazo_sla=? WHERE id=?", (nova, prazo, row["id"]))
            conn.execute("""INSERT INTO movimentacoes
                (contrato_id, data_hora, campo, valor_anterior, valor_novo, usuario)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (row["id"], agora, "Migração do fluxo", antiga, nova, "Sistema"))


def _inserir_demonstracao(conn):
    hoje = date.today()
    amostras = [
        ("MOR-2026-001", "Mariana Costa", "123.456.789-00", 420000, "Validação pré engenharia", "Ana Souza", "", 0, 0),
        ("MOR-2026-002", "Rafael Oliveira", "234.567.890-11", 585000, "Pendência da pasta", "Bruno Lima", "Atualizar comprovante de renda", 0, 1),
        ("MOR-2026-003", "Camila Santos", "345.678.901-22", 350000, "Análise documental", "Ana Souza", "Matrícula do imóvel ilegível", 0, 7),
        ("MOR-2026-004", "Lucas Almeida", "456.789.012-33", 710000, "Vistoria do imóvel", "Carla Mendes", "Aguardar laudo de vistoria", 0, 3),
        ("MOR-2026-005", "Fernanda Rocha", "567.890.123-44", 490000, "Emissão de contrato", "Bruno Lima", "", 0, 2),
        ("MOR-2026-006", "Pedro Martins", "678.901.234-55", 625000, "Registro do contrato no cartório", "Carla Mendes", "Aguardando protocolo do cartório", 0, 9),
        ("MOR-2026-007", "Juliana Ferreira", "789.012.345-66", 380000, "Pagamento ao vendedor", "Ana Souza", "", 0, 4),
        ("MOR-2026-008", "Diego Ribeiro", "890.123.456-77", 540000, ETAPA_CONCLUIDA, "Bruno Lima", "", 0, 1),
    ]
    for numero, cliente, doc, valor, etapa, resp, pend, _, parado in amostras:
        atualizado = datetime.now() - timedelta(days=parado)
        criado = atualizado - timedelta(days=3)
        inicio_sla = atualizado.date()
        prazo = _iso_prazo(etapa, inicio_sla)
        cur = conn.execute("""INSERT INTO contratos
            (numero, cliente, documento, valor, etapa, responsavel, pendencia, prazo_sla, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (numero, cliente, doc, valor, etapa, resp, pend, prazo, criado.isoformat(), atualizado.isoformat()))
        conn.execute("INSERT INTO movimentacoes (contrato_id, data_hora, campo, valor_novo) VALUES (?, ?, ?, ?)",
                     (cur.lastrowid, criado.isoformat(timespec="seconds"), "Cadastro", etapa))


def listar_contratos() -> pd.DataFrame:
    with conectar() as conn:
        return pd.read_sql_query("SELECT * FROM contratos ORDER BY CASE WHEN prazo_sla='' THEN 1 ELSE 0 END, prazo_sla ASC", conn)


def gerar_carteira_demo(total: int = 250) -> int:
    """Completa a carteira com contratos fictícios até atingir `total` registros."""
    nomes = ["Alex", "Beatriz", "Caio", "Daniela", "Eduardo", "Fernanda", "Gabriel", "Helena", "Igor", "Joana"]
    sobrenomes = ["Alves", "Barbosa", "Cardoso", "Dias", "Esteves", "Freitas", "Gomes", "Lopes", "Moraes", "Nunes"]
    responsaveis = ["Ana Souza", "Bruno Lima", "Carla Mendes", "Diego Alves", "Marina Costa"]
    pendencias = [
        "Aguardar envio do documento solicitado",
        "Validar informação com a área responsável",
        "Solicitar atualização do documento",
        "Aguardar retorno do cliente",
        "Conferir divergência apontada na análise",
    ]
    agora = datetime.now()
    criados = 0
    with conectar() as conn:
        _preencher_pendencias_vazias(conn)
        existentes = int(conn.execute("SELECT COUNT(*) FROM contratos").fetchone()[0])
        if existentes >= total:
            return 0
        numeros_existentes = {row[0] for row in conn.execute("SELECT numero FROM contratos").fetchall()}
        candidato = 1
        while existentes + criados < total:
            numero = f"MOR-DEMO-{candidato:03d}"
            candidato += 1
            if numero in numeros_existentes:
                continue
            indice = existentes + criados
            etapa = ETAPAS[indice % len(ETAPAS)]
            cliente = f"{nomes[indice % len(nomes)]} {sobrenomes[(indice // len(nomes)) % len(sobrenomes)]}"
            responsavel = responsaveis[indice % len(responsaveis)]
            pendencia = pendencias[indice % len(pendencias)] if indice % 2 == 0 and etapa != ETAPA_CONCLUIDA else SEM_PENDENCIA
            idade = [0, 1, 2, 4, 6, 8, 10][indice % 7]
            atualizado = agora - timedelta(days=idade)
            criado = atualizado - timedelta(days=5 + (indice % 24))
            if etapa == ETAPA_DATA_COMBINADA:
                combinado = (date.today() + timedelta(days=(indice % 17) - 4)).isoformat()
            else:
                combinado = None
            prazo = _iso_prazo(etapa, atualizado.date(), combinado)
            valor = float(280000 + ((indice * 13791) % 620000))
            documento = f"SIM-{candidato - 1:06d}"
            cur = conn.execute("""INSERT INTO contratos
                (numero, cliente, documento, valor, etapa, responsavel, pendencia, prazo_sla, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (numero, cliente, documento, valor, etapa, responsavel, pendencia, prazo,
                 criado.isoformat(timespec="seconds"), atualizado.isoformat(timespec="seconds")))
            conn.execute("""INSERT INTO movimentacoes
                (contrato_id, data_hora, campo, valor_novo, usuario)
                VALUES (?, ?, ?, ?, ?)""",
                (cur.lastrowid, criado.isoformat(timespec="seconds"), "Cadastro", etapa, "Carga demonstrativa"))
            numeros_existentes.add(numero)
            criados += 1
    return criados


def salvar_contrato(dados: dict, contrato_id: int | None = None, usuario: str = "Backoffice"):
    agora_dt = datetime.now()
    agora = agora_dt.isoformat(timespec="seconds")
    etapa = dados["etapa"]
    data_fornecida = dados.get("prazo_sla") or ""
    with conectar() as conn:
        if contrato_id is None:
            prazo = _iso_prazo(etapa, agora_dt.date(), data_fornecida or None)
            cur = conn.execute("""INSERT INTO contratos
                (numero, cliente, documento, valor, etapa, responsavel, pendencia, prazo_sla, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (dados["numero"], dados["cliente"], dados.get("documento", ""), dados["valor"], etapa,
                 dados["responsavel"], dados.get("pendencia", ""), prazo, agora, agora))
            contrato_id = cur.lastrowid
            conn.execute("INSERT INTO movimentacoes (contrato_id, data_hora, campo, valor_novo, usuario) VALUES (?, ?, ?, ?, ?)",
                         (contrato_id, agora, "Cadastro", etapa, usuario))
            return contrato_id

        anterior = conn.execute("SELECT * FROM contratos WHERE id = ?", (contrato_id,)).fetchone()
        if anterior is None:
            raise ValueError("Contrato não encontrado.")
        mudou_etapa = anterior["etapa"] != etapa
        if mudou_etapa:
            prazo = _iso_prazo(etapa, agora_dt.date(), data_fornecida or None)
        elif etapa == ETAPA_DATA_COMBINADA:
            prazo = _iso_prazo(etapa, agora_dt.date(), data_fornecida or None)
        else:
            prazo = anterior["prazo_sla"]
        campos = ["etapa", "responsavel", "pendencia", "prazo_sla"]
        conn.execute("""UPDATE contratos SET cliente=?, documento=?, valor=?, etapa=?, responsavel=?, pendencia=?, prazo_sla=?, atualizado_em=? WHERE id=?""",
                     (dados["cliente"], dados.get("documento", ""), dados["valor"], etapa, dados["responsavel"],
                      dados.get("pendencia", ""), prazo, agora, contrato_id))
        labels = {"etapa": "Etapa", "responsavel": "Responsável", "pendencia": "Pendência", "prazo_sla": "Prazo SLA"}
        for campo in campos:
            novo = str(prazo or "") if campo == "prazo_sla" else str(dados.get(campo, "") or "")
            antigo = str(anterior[campo] or "")
            if antigo != novo:
                conn.execute("""INSERT INTO movimentacoes
                    (contrato_id, data_hora, campo, valor_anterior, valor_novo, usuario)
                    VALUES (?, ?, ?, ?, ?, ?)""", (contrato_id, agora, labels[campo], antigo, novo, usuario))
        return contrato_id


def historico(contrato_id: int) -> pd.DataFrame:
    with conectar() as conn:
        return pd.read_sql_query("SELECT data_hora, campo, valor_anterior, valor_novo, usuario FROM movimentacoes WHERE contrato_id=? ORDER BY data_hora DESC, id DESC", conn, params=(contrato_id,))


def excluir_contrato(contrato_id: int):
    with conectar() as conn:
        conn.execute("DELETE FROM contratos WHERE id=?", (contrato_id,))
