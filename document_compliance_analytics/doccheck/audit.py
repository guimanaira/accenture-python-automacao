from __future__ import annotations

from datetime import date

from .models import Documento, Inconsistencia, Processo, ResultadoAuditoria


CHECKLIST_PADRAO = [
    "identificacao", "cpf", "comprovante_residencia", "comprovante_renda",
    "documentacao_imovel", "certidoes", "contrato_financiamento",
]
DOCUMENTOS_COM_VALIDADE = {"identificacao", "comprovante_residencia", "comprovante_renda", "certidoes"}


def _normalizar(valor: object) -> str:
    return " ".join(str(valor or "").strip().casefold().split())


def auditar(processo: Processo, hoje: date | None = None) -> ResultadoAuditoria:
    hoje = hoje or date.today()
    pendencias: list[Inconsistencia] = []
    por_tipo = {doc.tipo: doc for doc in processo.documentos}
    checklist = processo.checklist or CHECKLIST_PADRAO

    for tipo in checklist:
        doc = por_tipo.get(tipo)
        if doc is None or not doc.recebido:
            pendencias.append(Inconsistencia(tipo, "Ausente", "Documento não recebido.", "Solicitar o envio do documento."))
            continue
        if tipo in DOCUMENTOS_COM_VALIDADE and not doc.data_validade:
            pendencias.append(Inconsistencia(tipo, "Data não informada", "Não foi possível confirmar a validade.", "Conferir a data no documento.", True))
        elif doc.data_validade and doc.data_validade < hoje:
            pendencias.append(Inconsistencia(tipo, "Vencido", f"Validade em {doc.data_validade.isoformat()}.", "Solicitar documento atualizado."))

    esperado = {
        "nome": processo.cliente.nome,
        "cpf": processo.cliente.cpf,
        "endereco": processo.cliente.endereco,
        "renda_mensal": processo.cliente.renda_mensal,
    }
    for doc in processo.documentos:
        if not doc.recebido:
            continue
        chaves = {"identificacao": ("nome",), "cpf": ("cpf",), "comprovante_residencia": ("endereco",),
                  "comprovante_renda": ("renda_mensal",), "contrato_financiamento": ("nome", "cpf")}.get(doc.tipo, ())
        for chave in chaves:
            if chave in doc.dados and _normalizar(doc.dados[chave]) != _normalizar(esperado[chave]):
                pendencias.append(Inconsistencia(doc.tipo, "Divergente", f"{chave}: registro '{esperado[chave]}' difere do documento '{doc.dados[chave]}'.", "Validar a informação com o cliente e corrigir o cadastro ou documento.", True))

    vistos: dict[str, Documento] = {}
    for doc in processo.documentos:
        if not doc.recebido:
            continue
        chave = (doc.hash_conteudo or "").strip().lower() or (doc.nome_arquivo or "").strip().casefold()
        if chave and chave in vistos:
            outro = vistos[chave]
            pendencias.append(Inconsistencia(doc.tipo, "Possível duplicidade", f"Conteúdo/nome também consta em {outro.tipo}.", "Confirmar se os arquivos deveriam ser distintos.", True))
        elif chave:
            vistos[chave] = doc

    return ResultadoAuditoria(processo.contrato, pendencias)
