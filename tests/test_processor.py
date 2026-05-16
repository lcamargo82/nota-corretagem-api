import pytest
from unittest.mock import MagicMock, patch
from src.services.processor import NoteProcessorService, PDFDecryptionError
from src.schemas.nota import DadosNotaDTO

def test_process_note_regex_sucesso():
    service = NoteProcessorService()
    dto = service.process_note("notas/Nota.pdf")
    
    assert isinstance(dto, DadosNotaDTO)
    assert dto.cabecalho.numero_nota == 125838
    assert len(dto.operacoes) == 7
    assert dto.resumo_financeiro.valor_liquido_nota == 2.0

@patch("src.services.processor.PDFProcessor")
def test_process_note_fallback_llm(mock_pdf_processor_class):
    mock_pdf_instance = MagicMock()
    # Simula falha no parse Regex para forçar o LLM
    mock_pdf_instance.parse.side_effect = ValueError("Regex falhou")
    mock_pdf_instance.extract_text.return_value = "Texto bruto da nota para o LLM"
    mock_pdf_processor_class.return_value = mock_pdf_instance

    mock_llm = MagicMock()
    mock_llm.parse_nota.return_value = {
        "cabecalho": {
            "numero_nota": 777666,
            "data_pregao": "2026-05-16",
            "cpf_cliente": "111.222.333-44",
            "corretora_nome": "MISTRAL CORRETORA"
        },
        "operacoes": [
            {
                "tipo_operacao": "C",
                "mercado": "VISTA",
                "ativo": "PETR4",
                "quantidade": 100,
                "preco_unitario": 30.00,
                "valor_total": 3000.00,
                "debito_credito": "D",
                "modalidade": "SWING_TRADE"
            }
        ],
        "resumo_financeiro": {
            "taxa_liquidacao": 1.0,
            "emolumentos": 1.0,
            "taxa_corretagem": 0.0,
            "iss": 0.0,
            "irrf_day_trade": 0.0,
            "irrf_swing_trade": 0.0,
            "valor_liquido_nota": 3002.0
        }
    }

    service = NoteProcessorService(llm_engine=mock_llm)
    dto = service.process_note("caminho_fake.pdf")

    assert dto.cabecalho.numero_nota == 777666
    assert dto.cabecalho.corretora_nome == "MISTRAL CORRETORA"
    mock_llm.parse_nota.assert_called_once_with("Texto bruto da nota para o LLM")

def test_process_note_senha_invalida():
    service = NoteProcessorService()
    with pytest.raises(PDFDecryptionError):
        service.process_note("notas/NotaNegociacao-18526735-01-08-2025-31-08-2025-0.pdf", password="senha_errada")
