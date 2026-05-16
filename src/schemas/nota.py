from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional
from enum import Enum
from datetime import date

class ModalidadeOperacional(str, Enum):
    """Modalidade da operação financeira para segregação fiscal."""
    DAY_TRADE = "DAY_TRADE"
    SWING_TRADE = "SWING_TRADE"

class CabecalhoNota(BaseModel):
    """Dados de identificação e cabeçalho da nota de corretagem."""
    numero_nota: int = Field(..., description="Número único da nota de corretagem")
    data_pregao: str = Field(..., description="Data do pregão no formato YYYY-MM-DD")
    cpf_cliente: str = Field(..., description="CPF ou identificação do cliente")
    corretora_nome: str = Field(..., description="Nome da instituição corretora")

    @field_validator("numero_nota")
    @classmethod
    def validar_numero_nota(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("O número da nota deve ser maior que zero.")
        return v

class OperacaoNota(BaseModel):
    """Dados de uma linha de operação na tabela de negócios."""
    tipo_operacao: Literal["C", "V"] = Field(..., description="C para Compra, V para Venda")
    mercado: str = Field(..., description="Tipo de mercado: VISTA, FUTURO, OPCOES, etc.")
    ativo: str = Field(..., description="Ticker do ativo ou contrato")
    quantidade: int = Field(..., description="Quantidade de títulos ou contratos")
    preco_unitario: float = Field(..., description="Preço unitário da operação")
    valor_total: float = Field(..., description="Valor total (Quantidade x Preço ou Ajuste)")
    debito_credito: Literal["D", "C"] = Field(..., description="D para Débito, C para Crédito")
    modalidade: ModalidadeOperacional = Field(ModalidadeOperacional.DAY_TRADE, description="Classificação Day Trade ou Swing Trade")

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
        return v

    @field_validator("preco_unitario", "valor_total")
    @classmethod
    def validar_valores(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Valores monetários não podem ser negativos.")
        return v

class ResumoFinanceiro(BaseModel):
    """Custos operacionais e impostos retidos na nota de corretagem."""
    taxa_liquidacao: float = Field(0.0, description="Taxa de liquidação da B3")
    emolumentos: float = Field(0.0, description="Emolumentos da B3")
    taxa_corretagem: float = Field(0.0, description="Corretagem cobrada pela corretora")
    iss: float = Field(0.0, description="Imposto municipal sobre corretagem")
    irrf_day_trade: float = Field(0.0, description="IRRF retido na fonte sobre Day Trade (1%)")
    irrf_swing_trade: float = Field(0.0, description="IRRF retido na fonte sobre Swing Trade (0,005%)")
    valor_liquido_nota: float = Field(..., description="Valor líquido final financeiro da nota")

class DadosNotaDTO(BaseModel):
    """Agregação completa dos dados extraídos de uma nota."""
    cabecalho: CabecalhoNota
    operacoes: List[OperacaoNota]
    resumo_financeiro: ResumoFinanceiro

class NotaCorretagemResponse(BaseModel):
    """Contrato final de resposta da API."""
    sucesso: bool = Field(True, description="Indicador de sucesso do processamento")
    ambiente: str = Field(..., description="Ambiente de execução (development/production)")
    dados: DadosNotaDTO
