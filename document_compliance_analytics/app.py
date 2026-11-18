"""Audita o conjunto fictício de 250 contratos e gera painel local."""

from doccheck.batch import executar_lote


if __name__ == "__main__":
    relatorio = executar_lote()
    print("250 contratos fictícios auditados.")
    print(f"Painel gerado em: {relatorio}")
    print("Se o servidor local estiver ativo, abra http://localhost:8000/")
