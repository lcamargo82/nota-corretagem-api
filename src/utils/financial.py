from typing import List, Dict, Any
import logging

def calcular_impostos_estimados(operacoes: List[Dict[str, Any]], resumo: Dict[str, Any]) -> Dict[str, Any]:
    """
    Realiza a auditoria e cálculo estimado de impostos (IRRF Day Trade e Swing Trade)
    com base nas operações realizadas na nota de corretagem.
    """
    total_vendas_swing = 0.0
    lucro_estimado_day_trade = 0.0

    for op in operacoes:
        modalidade = op.get("modalidade", "DAY_TRADE")
        tipo = op.get("tipo_operacao", "C")
        valor = op.get("valor_total", 0.0)

        if modalidade == "SWING_TRADE" and tipo == "V":
            total_vendas_swing += valor
        elif modalidade == "DAY_TRADE":
            # Para uma estimativa simples de IRRF Day Trade (1% sobre o lucro),
            # somamos os créditos e subtraímos os débitos dos ajustes
            dc = op.get("debito_credito", "D")
            if dc == "C":
                lucro_estimado_day_trade += valor
            else:
                lucro_estimado_day_trade -= valor

    # IRRF Swing Trade (0,005% sobre o valor total de vendas na nota)
    irrf_swing_calc = round(total_vendas_swing * 0.00005, 2) if total_vendas_swing > 0 else 0.0

    # IRRF Day Trade (1% sobre o lucro líquido no day trade)
    irrf_dt_calc = round(lucro_estimado_day_trade * 0.01, 2) if lucro_estimado_day_trade > 0 else 0.0

    # Se o resumo extraído do PDF tiver valores zerados, preenchemos com a estimativa calculada
    if resumo.get("irrf_swing_trade", 0.0) == 0.0 and irrf_swing_calc > 0:
        logging.info(f"IRRF Swing Trade ausente no resumo. Estimativa calculada: {irrf_swing_calc}")
        resumo["irrf_swing_trade"] = irrf_swing_calc

    if resumo.get("irrf_day_trade", 0.0) == 0.0 and irrf_dt_calc > 0:
        logging.info(f"IRRF Day Trade ausente no resumo. Estimativa calculada: {irrf_dt_calc}")
        resumo["irrf_day_trade"] = irrf_dt_calc

    return resumo
