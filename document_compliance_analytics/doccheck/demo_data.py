"""Gera, de forma reproduzível, 250 dossiês fictícios para demonstração."""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path


def gerar_dossies(pasta: str | Path, quantidade: int = 250, seed: int = 125) -> list[Path]:
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    primeiros_nomes = ["Mariana", "Lucas", "Beatriz", "Rafael", "Camila", "Pedro", "Larissa", "Felipe", "Isabela", "Gustavo", "Ana", "Bruno", "Juliana", "Thiago", "Fernanda", "Diego", "Leticia", "Marcelo", "Renata", "Eduardo", "Patricia", "Vinicius", "Carolina", "Andre", "Daniela"]
    sobrenomes = [
        "Costa Lima", "Almeida Santos", "Oliveira Rocha", "Souza Mendes", "Ferreira Alves",
        "Ribeiro Costa", "Gomes Martins", "Carvalho Nunes", "Barros Lima", "Araujo Silva",
        "Bianchi Moretti", "Rossi Conti", "Romano Gallo", "Esposito Ferrari", "Ricci Lombardi",
        "Marino Greco", "Bruno De Luca", "Costa Bellini", "Giordano Rinaldi", "Fontana Colombo",
        "Müller Schneider", "Schmidt Fischer", "Weber Wagner", "Becker Hoffmann", "Schulz Bauer",
        "Koch Richter", "Klein Wolf", "Neumann Krüger", "Hartmann Vogel", "Zimmermann Braun",
    ]
    nomes_rua = ["das Flores", "das Acácias", "do Sol", "São João", "Ipê Amarelo", "Boa Vista", "das Palmeiras", "Central"]
    hoje = date.today()
    paths = []
    for n in range(1, quantidade + 1):
        contrato = f"{n:05d}"
        indice_nome = (n - 1) % len(primeiros_nomes)
        indice_sobrenome = ((n - 1) // len(primeiros_nomes) + indice_nome) % len(sobrenomes)
        nome = f"{primeiros_nomes[indice_nome]} {sobrenomes[indice_sobrenome]}"
        cpf_digitos = f"{n:09d}"
        cpf = f"{cpf_digitos[:3]}.{cpf_digitos[3:6]}.{cpf_digitos[6:9]}-{(n * 17) % 100:02d}"
        endereco_cliente = f"Rua {rng.choice(nomes_rua)}, {rng.randint(10, 1800)}, São Paulo - SP"
        renda = float(rng.randrange(350, 1801) * 10)
        falta = rng.choice([None, None, None, "comprovante_renda", "contrato_financiamento"])
        vencido = rng.choice([None, None, None, "certidoes", "comprovante_residencia"])
        divergencia = rng.choice([None, None, None, "comprovante_renda", "identificacao"])
        docs = [
            {"tipo": "identificacao", "nome_arquivo": f"rg_{contrato}.pdf", "recebido": True,
             "data_validade": (hoje + timedelta(days=500)).isoformat(), "dados": {"nome": nome}, "hash_conteudo": f"rg-{contrato}"},
            {"tipo": "cpf", "nome_arquivo": f"cpf_{contrato}.pdf", "recebido": True,
             "dados": {"cpf": cpf}, "hash_conteudo": f"cpf-{contrato}"},
            {"tipo": "comprovante_residencia", "nome_arquivo": f"residencia_{contrato}.pdf", "recebido": falta != "comprovante_residencia",
             "data_validade": (hoje - timedelta(days=15) if vencido == "comprovante_residencia" else hoje + timedelta(days=45)).isoformat(),
             "dados": {"endereco": endereco_cliente}, "hash_conteudo": f"res-{contrato}"},
            {"tipo": "comprovante_renda", "nome_arquivo": f"renda_{contrato}.pdf", "recebido": falta != "comprovante_renda",
             "data_validade": (hoje + timedelta(days=15)).isoformat(),
             "dados": {"renda_mensal": renda + (500 if divergencia == "comprovante_renda" else 0)}, "hash_conteudo": f"ren-{contrato}"},
            {"tipo": "certidoes", "nome_arquivo": f"certidoes_{contrato}.pdf", "recebido": True,
             "data_validade": (hoje - timedelta(days=5) if vencido == "certidoes" else hoje + timedelta(days=90)).isoformat(), "dados": {}, "hash_conteudo": f"cert-{contrato}"},
        ]
        if falta != "contrato_financiamento":
            docs.append({"tipo": "contrato_financiamento", "nome_arquivo": f"contrato_{contrato}.pdf", "recebido": True,
                         "dados": {"nome": nome, "cpf": cpf}, "hash_conteudo": f"contrato-{contrato}"})
        if divergencia == "identificacao":
            docs[0]["dados"]["nome"] = "Nome divergente"
        payload = {"contrato": contrato, "cliente": {"nome": nome, "cpf": cpf, "endereco": endereco_cliente, "renda_mensal": renda},
                   "dados_imovel": {"matricula": f"{70000 + n}", "endereco": f"Rua do Imóvel, {n}, São Paulo - SP"},
                   "checklist": ["identificacao", "cpf", "comprovante_renda", "comprovante_residencia", "certidoes", "contrato_financiamento"],
                   "documentos": docs}
        path = pasta / f"contrato_{contrato}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        paths.append(path)
    return paths
