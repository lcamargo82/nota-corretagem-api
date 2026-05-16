import pytest
from unittest.mock import MagicMock, patch
from src.services.llm_engine import LLMEngine, LLMEngineError

@patch("src.services.llm_engine.Mistral")
def test_parse_nota_sucesso(mock_mistral_class):
    # Configura o mock da resposta da Mistral API
    mock_client = MagicMock()
    mock_response = MagicMock()
    
    json_retorno = """
    {
      "cabecalho": {
        "numero_nota": 999888,
        "data_pregao": "2026-05-16",
        "cpf_cliente": "111.222.333-44",
        "corretora_nome": "XP INVESTIMENTOS"
      },
      "operacoes": [
        {
          "tipo_operacao": "C",
          "mercado": "VISTA",
          "ativo": "VALE3",
          "quantidade": 200,
          "preco_unitario": 60.00,
          "valor_total": 12000.00,
          "debito_credito": "D",
          "modalidade": "SWING_TRADE"
        }
      ],
      "resumo_financeiro": {
        "taxa_liquidacao": 2.50,
        "emolumentos": 1.50,
        "taxa_corretagem": 0.0,
        "iss": 0.0,
        "irrf_day_trade": 0.0,
        "irrf_swing_trade": 0.60,
        "valor_liquido_nota": 12004.60
      }
    }
    """
    mock_response.choices[0].message.content = json_retorno
    mock_client.chat.complete.return_value = mock_response
    mock_mistral_class.return_value = mock_client

    engine = LLMEngine(api_key="mock_key")
    resultado = engine.parse_nota("Texto bruto de mentirinha da nota")

    assert resultado["cabecalho"]["numero_nota"] == 999888
    assert resultado["operacoes"][0]["modalidade"] == "SWING_TRADE"
    assert resultado["resumo_financeiro"]["irrf_swing_trade"] == 0.60
    mock_client.chat.complete.assert_called_once()

@patch("src.services.llm_engine.Mistral")
def test_parse_nota_erro_api(mock_mistral_class):
    mock_client = MagicMock()
    mock_client.chat.complete.side_effect = Exception("API Timeout")
    mock_mistral_class.return_value = mock_client

    engine = LLMEngine(api_key="mock_key")

    with pytest.raises(LLMEngineError) as exc_info:
        engine.parse_nota("Texto de teste")

    assert "API Timeout" in str(exc_info.value)

def test_parse_nota_texto_vazio():
    engine = LLMEngine(api_key="mock_key")
    with pytest.raises(ValueError):
        engine.parse_nota("")
