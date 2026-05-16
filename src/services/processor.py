import logging
from typing import Optional, Dict, Any
from src.services.extractors import PDFProcessor, PDFDecryptionError
from src.services.llm_engine import LLMEngine, LLMEngineError
from src.schemas.nota import DadosNotaDTO, CabecalhoNota, OperacaoNota, ResumoFinanceiro
from src.utils.financial import calcular_impostos_estimados

class NoteProcessorService:
    """
    Serviço de orquestração central para processamento de notas de corretagem.
    Gerencia o fluxo de extração primária via Regex, fallback inteligente via LLM Mistral,
    validação de contratos Pydantic e auditoria financeira.
    """
    def __init__(self, llm_engine: Optional[LLMEngine] = None):
        self.llm_engine = llm_engine or LLMEngine()

    def process_note(self, pdf_path: str, password: Optional[str] = None) -> DadosNotaDTO:
        """
        Executa o pipeline completo de processamento de uma nota de corretagem em PDF.
        """
        logging.info(f"Iniciando processamento da nota: {pdf_path}")
        pdf_processor = PDFProcessor(pdf_path, password=password)

        raw_data: Optional[Dict[str, Any]] = None
        usou_llm = False

        # Tentativa 1: Extração Primária via Regex (Alta velocidade e precisão)
        try:
            logging.info("Tentando extração primária via Regex...")
            raw_data = pdf_processor.parse()
            
            # Validação de sanidade: Verifica se encontrou o número da nota e operações
            if not raw_data.get("cabecalho", {}).get("numero_nota") or not raw_data.get("operacoes"):
                logging.warning("Extração Regex incompleta (faltando cabeçalho ou operações). Acionando fallback LLM...")
                raw_data = None
        except PDFDecryptionError as e:
            # Erro de senha deve propagar imediatamente para o cliente
            logging.warning(f"Erro de descriptografia de PDF: {e}")
            raise e
        except Exception as e:
            logging.warning(f"Falha na extração Regex ({e}). Acionando fallback LLM...")
            raw_data = None

        # Tentativa 2: Fallback Inteligente via Mistral AI
        if not raw_data:
            logging.info("Iniciando extração de fallback via Mistral AI...")
            try:
                # Extrai o texto bruto do PDF (já descriptografado se a senha foi correta)
                full_text = pdf_processor.extract_text()
                raw_data = self.llm_engine.parse_nota(full_text)
                usou_llm = True
            except Exception as e:
                logging.error(f"Falha em ambos os motores (Regex e LLM): {e}")
                raise RuntimeError(f"Não foi possível extrair os dados da nota de corretagem: {str(e)}")

        # Etapa 3: Auditoria Financeira e Cálculo de Impostos
        raw_data["resumo_financeiro"] = calcular_impostos_estimados(
            raw_data["operacoes"],
            raw_data["resumo_financeiro"]
        )

        # Etapa 4: Validação e Construção do Contrato Pydantic v2
        try:
            logging.info("Validando dados extraídos contra schemas Pydantic v2...")
            cabecalho = CabecalhoNota(**raw_data["cabecalho"])
            operacoes = [OperacaoNota(**op) for op in raw_data["operacoes"]]
            resumo = ResumoFinanceiro(**raw_data["resumo_financeiro"])

            dto = DadosNotaDTO(
                cabecalho=cabecalho,
                operacoes=operacoes,
                resumo_financeiro=resumo
            )
            logging.info(f"Processamento concluído com sucesso. (Motor utilizado: {'Mistral AI' if usou_llm else 'Regex Primário'})")
            return dto
        except Exception as e:
            logging.error(f"Erro de validação Pydantic nos dados extraídos: {e}")
            raise ValueError(f"Os dados extraídos da nota são inválidos ou inconsistentes: {str(e)}")
