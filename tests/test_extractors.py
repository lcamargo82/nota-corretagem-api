import pytest
from src.services.extractors import PDFProcessor, PDFDecryptionError

def test_extracao_nota_sem_senha():
    processor = PDFProcessor("notas/Nota.pdf")
    dados = processor.parse()
    
    assert dados["cabecalho"]["numero_nota"] == 125838
    assert dados["cabecalho"]["data_pregao"] == "2026-05-15"
    assert dados["cabecalho"]["corretora_nome"] == "RENASCENCA DTVM LTDA"
    assert len(dados["operacoes"]) == 7
    assert dados["resumo_financeiro"]["taxa_liquidacao"] == 1.92
    assert dados["resumo_financeiro"]["emolumentos"] == 1.08
    assert dados["resumo_financeiro"]["valor_liquido_nota"] == 2.0

def test_extracao_nota_santander():
    processor = PDFProcessor("notas/Notas de Corretagem.pdf")
    dados = processor.parse()
    
    assert dados["cabecalho"]["numero_nota"] == 909475
    assert dados["cabecalho"]["data_pregao"] == "2026-05-12"
    assert len(dados["operacoes"]) == 35
    assert dados["resumo_financeiro"]["taxa_liquidacao"] == 5.76
    assert dados["resumo_financeiro"]["emolumentos"] == 3.24
    assert dados["resumo_financeiro"]["valor_liquido_nota"] == 201.0

def test_extracao_nota_cm_capital():
    processor = PDFProcessor("notas/NotaCM.pdf")
    dados = processor.parse()
    
    assert dados["cabecalho"]["numero_nota"] == 41192
    assert dados["cabecalho"]["data_pregao"] == "2025-01-30"
    assert len(dados["operacoes"]) == 74
    assert dados["resumo_financeiro"]["taxa_liquidacao"] == 568.74
    assert dados["resumo_financeiro"]["emolumentos"] == 306.44
    assert dados["resumo_financeiro"]["taxa_corretagem"] == 190.98
    assert dados["resumo_financeiro"]["iss"] == 10.52
    assert dados["resumo_financeiro"]["valor_liquido_nota"] == 3750.43

def test_extracao_nota_protegida_sem_senha_deve_falhar():
    processor = PDFProcessor("notas/NotaNegociacao-18526735-01-08-2025-31-08-2025-0.pdf")
    with pytest.raises(PDFDecryptionError) as exc_info:
        processor.extract_text()
    assert "PDF protegido por senha" in str(exc_info.value)
