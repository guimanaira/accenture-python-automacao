from __future__ import annotations

import argparse
from pathlib import Path

from .audit import auditar
from .reporting import gerar_relatorios
from .storage import carregar_processo, salvar_auditoria


def main() -> None:
    parser = argparse.ArgumentParser(description="Confere documentos de um processo de financiamento imobiliário.")
    parser.add_argument("arquivo", nargs="?", default="data/processo_demo.json", help="Arquivo JSON do processo")
    parser.add_argument("--saida", default="relatorios", help="Pasta de saída dos relatórios")
    parser.add_argument("--db", default="data/auditorias.sqlite3", help="Arquivo SQLite para persistência")
    args = parser.parse_args()
    processo = carregar_processo(args.arquivo)
    resultado = auditar(processo)
    md, csv, visual = gerar_relatorios(resultado, args.saida)
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    salvar_auditoria(args.db, processo, resultado)
    print(f"Contrato {resultado.contrato}: {'com pendências' if resultado.tem_pendencias else 'sem pendências'}")
    print(f"Revisão manual: {'sim' if resultado.precisa_revisao_manual else 'não'}")
    print(f"Relatórios: {visual}, {md} e {csv}\nBanco: {args.db}")


if __name__ == "__main__":
    main()
