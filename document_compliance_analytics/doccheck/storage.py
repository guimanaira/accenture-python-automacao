from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .models import Cliente, Documento, Processo


def carregar_processo(caminho: str | Path) -> Processo:
    raw = json.loads(Path(caminho).read_text(encoding="utf-8"))
    cliente = Cliente(**raw["cliente"])
    docs = []
    for item in raw.get("documentos", []):
        item = dict(item)
        for key in ("data_emissao", "data_validade"):
            if item.get(key):
                item[key] = date.fromisoformat(item[key])
        docs.append(Documento(**item))
    return Processo(raw["contrato"], cliente, docs, raw.get("dados_imovel", {}), raw.get("checklist", []))


def inicializar_banco(caminho: str | Path) -> None:
    with sqlite3.connect(caminho) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS processos (contrato TEXT PRIMARY KEY, cliente_json TEXT NOT NULL, auditado_em TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS documentos (id INTEGER PRIMARY KEY, contrato TEXT NOT NULL, tipo TEXT NOT NULL,
          recebido INTEGER NOT NULL, nome_arquivo TEXT, data_validade TEXT, dados_json TEXT NOT NULL,
          FOREIGN KEY (contrato) REFERENCES processos(contrato));
        CREATE TABLE IF NOT EXISTS inconsistencias (id INTEGER PRIMARY KEY, contrato TEXT NOT NULL, documento TEXT NOT NULL,
          status TEXT NOT NULL, detalhe TEXT NOT NULL, acao TEXT NOT NULL, revisao_manual INTEGER NOT NULL,
          FOREIGN KEY (contrato) REFERENCES processos(contrato));
        """)


def salvar_auditoria(caminho: str | Path, processo: Processo, resultado) -> None:
    inicializar_banco(caminho)
    with sqlite3.connect(caminho) as con:
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("INSERT INTO processos VALUES (?, ?, ?) ON CONFLICT(contrato) DO UPDATE SET cliente_json=excluded.cliente_json, auditado_em=excluded.auditado_em",
                    (processo.contrato, json.dumps(asdict(processo.cliente), ensure_ascii=False), date.today().isoformat()))
        con.execute("DELETE FROM documentos WHERE contrato = ?", (processo.contrato,))
        con.execute("DELETE FROM inconsistencias WHERE contrato = ?", (processo.contrato,))
        for doc in processo.documentos:
            validade = doc.data_validade.isoformat() if doc.data_validade else None
            con.execute("INSERT INTO documentos (contrato,tipo,recebido,nome_arquivo,data_validade,dados_json) VALUES (?,?,?,?,?,?)",
                        (processo.contrato, doc.tipo, int(doc.recebido), doc.nome_arquivo, validade, json.dumps(doc.dados, ensure_ascii=False)))
        for item in resultado.inconsistencias:
            con.execute("INSERT INTO inconsistencias (contrato,documento,status,detalhe,acao,revisao_manual) VALUES (?,?,?,?,?,?)",
                        (processo.contrato, item.documento, item.status, item.detalhe, item.acao, int(item.revisao_manual)))
