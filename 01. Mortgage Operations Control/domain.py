"""Entidades, etapas e regras de SLA da jornada imobiliária."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta


ETAPAS_POR_FRENTE = {
    "ANÁLISE TÉCNICA DA OPERAÇÃO · PREPARAÇÃO / ANÁLISE DOCUMENTAL": [
        "Validação pré engenharia",
        "Pendência da pasta",
        "Validação da pasta",
        "Aguardando recebimento de matrícula interna",
        "Análise documental",
        "Pendência documental",
        "Reanálise documental",
        "Análise/pendência de resseguro",
        "Esclarecimento de qualificação",
        "Inclusão de vaga autônoma",
    ],
    "ANÁLISE TÉCNICA DA OPERAÇÃO · ENGENHARIA": [
        "Vistoria do imóvel",
        "Esclarecimento para vistoria",
        "Análise de risco ambiental",
        "Confirmação de pagamento de tarifa de avaliação",
        "Divergência do valor de avaliação",
        "Tratamento de recusa do imóvel",
        "Tratamento de recusa do risco ambiental",
    ],
    "CONTRATO": [
        "Confirmação de valores",
        "Resgate do FGTS, quando houver",
        "Emissão de contrato",
        "Assinatura",
        "Conferência/validação de assinaturas",
        "Ajuste, remissão, aditivo/em tempo",
        "Registro do contrato no cartório",
    ],
    "LIBERAÇÃO DOS VALORES": [
        "Contrato registrado + matrícula com alienação",
        "Pagamento ao vendedor",
    ],
}

ETAPA_CONCLUIDA = "Processo concluído"
SEM_PENDENCIA = "Sem pendência em aberto"
ETAPAS = [etapa for etapas in ETAPAS_POR_FRENTE.values() for etapa in etapas] + [ETAPA_CONCLUIDA]

SLA_DIAS = {
    "Validação pré engenharia": 1,
    "Pendência da pasta": 3,
    "Validação da pasta": 3,
    "Aguardando recebimento de matrícula interna": 3,
    "Análise documental": 3,
    "Pendência documental": 3,
    "Reanálise documental": 3,
    "Análise/pendência de resseguro": 3,
    "Esclarecimento de qualificação": 5,
    "Inclusão de vaga autônoma": 5,
    "Vistoria do imóvel": 5,
    "Esclarecimento para vistoria": 5,
    "Análise de risco ambiental": 5,
    "Confirmação de pagamento de tarifa de avaliação": 5,
    "Divergência do valor de avaliação": 5,
    "Tratamento de recusa do imóvel": 5,
    "Tratamento de recusa do risco ambiental": 5,
    "Confirmação de valores": 2,
    "Resgate do FGTS, quando houver": 5,
    "Emissão de contrato": 3,
    "Conferência/validação de assinaturas": 3,
    "Ajuste, remissão, aditivo/em tempo": 3,
    "Contrato registrado + matrícula com alienação": 5,
    "Pagamento ao vendedor": 5,
}
ETAPA_DATA_COMBINADA = "Assinatura"
ETAPAS_SEM_SLA = {"Registro do contrato no cartório", ETAPA_CONCLUIDA}
DIAS_PARA_ALERTA = 3
DIAS_PARA_PARADO = 5


def adicionar_dias_uteis(inicio: date, dias: int) -> date:
    """Calcula D+N sem contar sábados e domingos; não aplica feriados."""
    atual = inicio
    adicionados = 0
    while adicionados < dias:
        atual += timedelta(days=1)
        if atual.weekday() < 5:
            adicionados += 1
    return atual


def calcular_prazo_sla(etapa: str, inicio: date | None = None, data_combinada: date | None = None) -> date | None:
    if etapa in ETAPAS_SEM_SLA:
        return None
    if etapa == ETAPA_DATA_COMBINADA:
        return data_combinada
    dias = SLA_DIAS.get(etapa)
    if dias is None:
        return None
    return adicionar_dias_uteis(inicio or date.today(), dias)


@dataclass
class Cliente:
    nome: str
    documento: str = ""


@dataclass
class Processo:
    etapa: str
    responsavel: str
    pendencia: str = ""
    atualizado_em: datetime | None = None

    @property
    def dias_parado(self) -> int:
        if not self.atualizado_em:
            return 0
        return max((datetime.now() - self.atualizado_em).days, 0)

    @property
    def esta_parado(self) -> bool:
        return self.etapa != ETAPA_CONCLUIDA and self.dias_parado >= DIAS_PARA_PARADO


@dataclass
class Contrato:
    numero: str
    cliente: Cliente
    valor: float
    processo: Processo
    prazo_sla: date | None

    @property
    def dias_para_vencer(self) -> int | None:
        return (self.prazo_sla - date.today()).days if self.prazo_sla else None

    @property
    def situacao_sla(self) -> str:
        if self.processo.etapa == ETAPA_CONCLUIDA:
            return "Concluído"
        if self.prazo_sla is None:
            return "Sem SLA"
        dias = self.dias_para_vencer
        if dias < 0:
            return "Fora do SLA"
        if dias <= DIAS_PARA_ALERTA:
            return "Próximo do vencimento"
        return "No prazo"
