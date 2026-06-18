import subprocess
import sys
import tempfile
from pathlib import Path

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from src.analysis.matricula_analyzer import analisar_matricula
from src.ingestion.load_document import (
    load_image,
    load_pdf,
    ocr_disponivel,
    pdf_possui_paginas_escaneadas,
)


MAX_DOCUMENTOS = 5
TIPOS_PERMITIDOS = ["pdf", "png", "jpg", "jpeg", "webp", "tif", "tiff"]
EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}


def abrir_com_streamlit():
    try:
        contexto = get_script_run_ctx(suppress_warning=True)
    except TypeError:
        contexto = get_script_run_ctx()

    if contexto is None:
        arquivo = Path(__file__).resolve()
        subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(arquivo)])
        print("Abrindo Analisador de Matrículas no Streamlit...")
        sys.exit(0)


def extrair_texto_pdf(uploaded_file):
    conteudo = uploaded_file.getvalue()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as arquivo_temporario:
        arquivo_temporario.write(conteudo)
        caminho_temporario = arquivo_temporario.name

    try:
        precisa_ocr = pdf_possui_paginas_escaneadas(caminho_temporario)
        ocr_ativo = ocr_disponivel()
        texto = load_pdf(caminho_temporario, use_ocr=ocr_ativo)
        return texto, precisa_ocr and not ocr_ativo
    finally:
        Path(caminho_temporario).unlink(missing_ok=True)


def extrair_texto_imagem(uploaded_file):
    conteudo = uploaded_file.getvalue()
    suffix = Path(uploaded_file.name).suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as arquivo_temporario:
        arquivo_temporario.write(conteudo)
        caminho_temporario = arquivo_temporario.name

    try:
        ocr_ativo = ocr_disponivel()
        texto = load_image(caminho_temporario) if ocr_ativo else ""
        return texto, not ocr_ativo
    finally:
        Path(caminho_temporario).unlink(missing_ok=True)


def extrair_texto_arquivo(uploaded_file):
    extensao = Path(uploaded_file.name).suffix.lower()

    if extensao == ".pdf":
        return extrair_texto_pdf(uploaded_file)

    if extensao in EXTENSOES_IMAGEM:
        return extrair_texto_imagem(uploaded_file)

    raise ValueError("Formato de arquivo não suportado.")


def exibir_documento(numero, arquivo):
    st.markdown(f"### {numero}. {arquivo.name}")
    st.write("**Documento enviado:**", arquivo.name)

    try:
        texto, analise_incompleta = extrair_texto_arquivo(arquivo)
        resultado = analisar_matricula(texto)
    except Exception as erro:
        st.error(f"Não foi possível analisar este documento: {erro}")
        st.divider()
        return

    if analise_incompleta:
        st.warning(
            "Este arquivo precisa de OCR. Instale/ative o Tesseract OCR para "
            "identificar restrições que aparecem apenas na imagem do documento."
        )

    if not resultado["eh_matricula"]:
        st.write("**Matrícula não Localizada**")
        st.divider()
        return

    irregularidades = resultado["irregularidades"]
    st.write("**Documento:**", "Matrícula Encontrada")

    if analise_incompleta and not irregularidades:
        st.write("**Irregularidades Encontradas**")
        st.write("- Análise incompleta: restrições podem estar na imagem do arquivo")
        st.write("**Nível de Risco**")
        st.write("OCR necessário para concluir")
        st.divider()
        return

    st.write("**Irregularidades Encontradas**")
    if irregularidades:
        for irregularidade in irregularidades:
            st.write(f"- {irregularidade}")
    else:
        st.write("- Nenhuma irregularidade encontrada")

    st.write("**Nível de Risco**")
    st.write(resultado["nivel_risco"])
    st.divider()


abrir_com_streamlit()

st.set_page_config(page_title="Analisador de Matrículas")
st.title("Analisador de Matrículas")

arquivos = st.file_uploader(
    "Anexe até 5 documentos",
    type=TIPOS_PERMITIDOS,
    accept_multiple_files=True,
)

if arquivos and len(arquivos) > MAX_DOCUMENTOS:
    st.error("Envie no máximo 5 documentos.")
    arquivos = arquivos[:MAX_DOCUMENTOS]

st.subheader("Documentos Enviados")

if not arquivos:
    st.info("Nenhum documento enviado.")
else:
    for numero, arquivo in enumerate(arquivos, start=1):
        exibir_documento(numero, arquivo)
