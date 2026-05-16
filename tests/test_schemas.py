import pytest
from pydantic import ValidationError
from src.schemas.nota import (
    CabecalhoNota,
    OperacaoNota,
    ResumoFinanceiro,
    ModalidadeOperacional,
    DadosNotaDTO,
    NotaCorretagemResponse
)

def test_cabecalho_valido():
    cabecalho = CabecalhoNota(
        numero_nota=123456,
        data_pregao="2026-05-16",
        cpf_cliente="111.222.333-44",
        corretora_nome="XP INVESTIMENTOS"
    )
    assert cabecalho.numero_nota == 123456

def test_cabecalho_invalido():
    with pytest.raises(ValidationError):
        CabecalhoNota(
            numero_nota=0, # Inválido
            data_pregao="2026-05-16",
            cpf_cliente="111.222.333-44",
            corretora_nome="XP INVESTIMENTOS"
        )

def test_operacao_valida_swing_trade():
    operacao = OperacaoNota(
        tipo_operacao="C",
        mercado="VISTA",
        ativo="VALE3",
        quantidade=100,
        preco_unitario=65.50,
        valor_total=6550.00,
        debito_credito="D",
        modalidade=ModalidadeOperacional.SWING_TRADE
    )
    assert operacao.modalidade == ModalidadeOperacional.SWING_TRADE

def test_operacao_invalida_quantidade_negativa():
    with pytest.raises(ValidationError):
        OperacaoNota(
            tipo_operacao="C",
            mercado="VISTA",
            ativo="VALE3",
            quantidade=-100, # Inválido
            preco_unitario=65.50,
            valor_total=6550.00,
            debito_credito="D"
        )

def test_response_completo():
    resumo = ResumoFinanceiro(
        taxa_liquidacao=5.0,
        emolumentos=3.0,
        taxa_corretagem=0.0,
        iss=0.0,
        irrf_day_trade=1.50,
        irrf_swing_trade=0.0,
        valor_liquido_nota=1000.0
    )
    cabecalho = CabecalhoNota(
        numero_nota=123,
        data_pregao="2026-05-16",
        cpf_cliente="123",
        corretora_nome="XP"
    )
    operacao = OperacaoNota(
        tipo_operacao="C",
        mercado="VISTA",
        ativo="PETR4",
        quantidade=100,
        preco_unitario=30.0,
        valor_total=3000.0,
        debito_credito="D",
        modalidade=ModalidadeOperacional.DAY_TRADE
    )
    
    dto = DadosNotaDTO(cabecalho=cabecalho, operacoes=[operacao], resumo_financeiro=resumo)
    response = NotaCorretagemResponse(sucesso=True, ambiente="development", dados=dto)
    
    assert response.sucesso is True
    assert len(response.dados.operacoes) == 1
