import json
import logging
from typing import Dict, Any, Optional
from mistralai.client import Mistral
from mistralai.client.models import UserMessage, SystemMessage
from src.core.config import settings

class LLMEngineError(Exception):
    """Exceção levantada quando ocorre falha na comunicação ou parse com a Mistral API."""
    pass

class LLMEngine:
    """
    Motor de Inteligência Artificial para extração de notas de corretagem.
    Utiliza exclusivamente a Mistral API em nuvem (mistral-large-latest)
    com suporte nativo a chamadas estruturadas em JSON (json_object).
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.MISTRAL_API_KEY
        if not self.api_key or self.api_key.startswith("sua_api_key"):
            logging.warning("MISTRAL_API_KEY não configurada ou com valor padrão. As chamadas reais à API falharão.")
        self.client = Mistral(api_key=self.api_key)

    def parse_nota(self, text: str) -> Dict[str, Any]:
        """
        Envia o texto bruto da nota de corretagem para a Mistral API
        e solicita a extração estruturada seguindo o contrato Pydantic.
        """
        if not text.strip():
            raise ValueError("O texto de entrada para o LLM não pode estar vazio.")

        system_prompt = """
Você é um especialista financeiro em notas de corretagem do mercado brasileiro (Padrão SINACOR).
Sua tarefa é analisar o texto bruto de uma nota de corretagem e extrair os dados EXATAMENTE na estrutura JSON abaixo.

Regras de Negócio e Segregação Fiscal:
1. Modalidade Operacional:
   - Identifique se a operação é DAY_TRADE (iniciada e encerrada no mesmo dia) ou SWING_TRADE (operações normais/posição).
   - Indique essa modalidade em cada item da lista de operações.

2. Identificação de Mercado:
   - VISTA: Ações normais (ex: PETR4, VALE3).
   - FUTURO: Contratos futuros (ex: WIN, WDO, IND, DOL, BIT FUT).
   - OPCOES: Opções de compra/venda (ex: PETRM, VALEC).

3. Estrutura Obrigatória do JSON de Saída:
{
  "cabecalho": {
    "numero_nota": 123456,
    "data_pregao": "YYYY-MM-DD",
    "cpf_cliente": "111.222.333-44",
    "corretora_nome": "NOME DA CORRETORA"
  },
  "operacoes": [
    {
      "tipo_operacao": "C", // C para Compra, V para Venda
      "mercado": "VISTA", // VISTA, FUTURO ou OPCOES
      "ativo": "TICKER DO ATIVO",
      "quantidade": 100,
      "preco_unitario": 25.50,
      "valor_total": 2550.00, // Quantidade x Preço ou Ajuste
      "debito_credito": "D", // D para Débito, C para Crédito
      "modalidade": "DAY_TRADE" // DAY_TRADE ou SWING_TRADE
    }
  ],
  "resumo_financeiro": {
    "taxa_liquidacao": 5.00,
    "emolumentos": 3.00,
    "taxa_corretagem": 0.00,
    "iss": 0.00,
    "irrf_day_trade": 1.50, // 1% sobre lucro day trade
    "irrf_swing_trade": 0.00, // 0,005% sobre vendas swing trade
    "valor_liquido_nota": 1000.00
  }
}

Retorne APENAS o JSON válido, sem markdown ou explicações adicionais.
"""
        messages = [
            SystemMessage(content=system_prompt.strip()),
            UserMessage(content=text.strip())
        ]

        try:
            logging.info("Enviando texto da nota para a Mistral API (mistral-large-latest)...")
            response = self.client.chat.complete(
                model="mistral-large-latest",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            raw_content = response.choices[0].message.content
            parsed_json = json.loads(raw_content)
            logging.info("Extração via Mistral API concluída com sucesso.")
            return parsed_json
        except Exception as e:
            logging.error(f"Falha na comunicação ou parse com a Mistral API: {e}")
            raise LLMEngineError(f"Erro na Mistral API: {str(e)}")
