from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class Cliente:
    nome: str
    cpf: str
    endereco: str
    renda_mensal: float


@dataclass
class Documento:
    tipo: str
    nome_arquivo: str | None = None
    recebido: bool = False
    data_emissao: date | None = None
    data_validade: date | None = None
    dados: dict[str, Any] = field(default_factory=dict)
    hash_conteudo: str | None = None


@dataclass
class Processo:
    contrato: str
    cliente: Cliente
    documentos: list[Documento]
    dados_imovel: dict[str, Any] = field(default_factory=dict)
    checklist: list[str] = field(default_factory=list)


@dataclass
class Inconsistencia:
    documento: str
    status: str
    detalhe: str
    acao: str
    revisao_manual: bool = False


@dataclass
class ResultadoAuditoria:
    contrato: str
    inconsistencias: list[Inconsistencia]

    @property
    def tem_pendencias(self) -> bool:
        return bool(self.inconsistencias)

    @property
    def precisa_revisao_manual(self) -> bool:
        # Regra operacional do relatório: toda pendência exige revisão manual.
        return self.tem_pendencias
