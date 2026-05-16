import pdfplumber
import pypdf
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from pdfplumber.utils.exceptions import PdfminerException
from pdfminer.pdfdocument import PDFPasswordIncorrect

class PDFDecryptionError(Exception):
    """Exceção levantada quando um PDF protegido por senha não pode ser descriptografado."""
    pass

class PDFProcessor:
    """
    Processador avançado de notas de corretagem em PDF (Padrão SINACOR).
    Suporta arquivos protegidos por senha e extração via Regex de alta precisão.
    """
    def __init__(self, pdf_path: str, password: Optional[str] = None):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")
        self.password = password

    def extract_text(self) -> str:
        """
        Extrai todo o texto do PDF, página por página, aplicando a senha se fornecida.
        Utiliza as tolerâncias padrão do pdfplumber otimizadas para tabelas SINACOR.
        """
        full_text = ""
        try:
            with pdfplumber.open(self.pdf_path, password=self.password) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
        except (PdfminerException, PDFPasswordIncorrect, pypdf.errors.FileNotDecryptedError) as e:
            logging.warning(f"Falha ao descriptografar PDF {self.pdf_path}: {e}")
            raise PDFDecryptionError("PDF protegido por senha. Forneça a senha correta no campo 'password'.")
        except Exception as e:
            logging.error(f"Erro inesperado ao extrair texto de {self.pdf_path}: {e}")
            raise e
        
        return full_text

    def extract_pages(self) -> List[str]:
        """
        Retorna uma lista de strings, onde cada string é o texto de uma página.
        """
        pages_text = []
        try:
            with pdfplumber.open(self.pdf_path, password=self.password) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    pages_text.append(text if text else "")
        except (PdfminerException, PDFPasswordIncorrect, pypdf.errors.FileNotDecryptedError) as e:
            logging.warning(f"Falha ao descriptografar páginas do PDF {self.pdf_path}: {e}")
            raise PDFDecryptionError("PDF protegido por senha. Forneça a senha correta no campo 'password'.")
        except Exception as e:
            logging.error(f"Erro ao processar páginas de {self.pdf_path}: {e}")
            return []
        return pages_text

    def parse(self) -> Dict[str, Any]:
        """
        Realiza o parse completo do texto do PDF utilizando Expressões Regulares (Regex)
        para extrair cabeçalho, operações e resumo financeiro.
        """
        text = self.extract_text()
        if not text.strip():
            raise ValueError("O PDF está vazio ou não contém texto extraível.")

        cabecalho = self._parse_cabecalho(text)
        operacoes = self._parse_operacoes(text)
        resumo = self._parse_resumo_financeiro(text)

        return {
            "cabecalho": cabecalho,
            "operacoes": operacoes,
            "resumo_financeiro": resumo
        }

    def _parse_cabecalho(self, text: str) -> Dict[str, Any]:
        # Número da Nota e Data do Pregão
        m_cab = re.search(r"(\d[\d\.]+)\s+1\s+(?:/\s+\d\s+)?(\d{2}/\d{2}/\d{4})", text)
        if not m_cab:
            m_cab = re.search(r"(\d[\d\.]+)\s+1\s+.*?(\d{2}/\d{2}/\d{4})", text)

        numero_nota = 0
        data_pregao = ""
        if m_cab:
            numero_nota = int(m_cab.group(1).replace(".", ""))
            # Formata data DD/MM/YYYY para YYYY-MM-DD
            parts = m_cab.group(2).split("/")
            data_pregao = f"{parts[2]}-{parts[1]}-{parts[0]}"

        # CPF do Cliente
        m_cpf = re.search(r"(\d{3}\.\d{3}\.\d{3}\-\d{2})", text)
        cpf_cliente = m_cpf.group(1) if m_cpf else ""

        # Nome da Corretora
        m_cnpj = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}\-\d{2}\n([^\n]+)", text)
        corretora_nome = ""
        if m_cnpj:
            linha = m_cnpj.group(1)
            corretora_nome = re.split(r"(?:Fone|Telefone|RUA|Av|R\.|BackOffice)", linha, flags=re.IGNORECASE)[0].strip()
        else:
            m_corr_fallback = re.search(r"(\b[A-Z\s\.\,\-\&]+S\.?A\.?|\b[A-Z\s\.\,\-\&]+LTDA\.?)", text)
            if m_corr_fallback:
                corretora_nome = m_corr_fallback.group(1).strip()

        return {
            "numero_nota": numero_nota,
            "data_pregao": data_pregao,
            "cpf_cliente": cpf_cliente,
            "corretora_nome": corretora_nome
        }

    def _parse_operacoes(self, text: str) -> List[Dict[str, Any]]:
        linhas = re.findall(r"^([CV])\s+(.*?)\s+(\d+)\s+([\d\.\,]+)\s+(DAY\s*TRADE|NORMAL|.*?)\s+([\d\.\,]+)\s+([DC])", text, re.MULTILINE)
        operacoes = []

        def to_float(val_str):
            clean = re.sub(r"[^\d\,\.]", "", val_str)
            if not clean: return 0.0
            if "," in clean:
                parts = clean.split(",")
                int_part = parts[0].replace(".", "")
                dec_part = parts[1]
                return float(f"{int_part}.{dec_part}")
            return float(clean.replace(".", ""))

        for l in linhas:
            tipo_op = l[0]
            ativo_raw = l[1].strip()
            quantidade = int(l[2])
            preco_unitario = to_float(l[3])
            modalidade_raw = l[4].upper()
            valor_total = to_float(l[5])
            debito_credito = l[6]

            # Identifica Mercado
            mercado = "VISTA"
            if any(k in ativo_raw for k in ["WIN", "WDO", "FUT", "DOL", "IND", "BIT"]):
                mercado = "FUTURO"
            elif "OPC" in modalidade_raw or "OPCAO" in ativo_raw:
                mercado = "OPCOES"

            # Identifica Modalidade (Day Trade ou Swing Trade)
            modalidade = "DAY_TRADE"
            if "NORMAL" in modalidade_raw or "SWING" in modalidade_raw:
                modalidade = "SWING_TRADE"

            operacoes.append({
                "tipo_operacao": tipo_op,
                "mercado": mercado,
                "ativo": ativo_raw,
                "quantidade": quantidade,
                "preco_unitario": preco_unitario,
                "valor_total": valor_total,
                "debito_credito": debito_credito,
                "modalidade": modalidade
            })

        return operacoes

    def _parse_resumo_financeiro(self, text: str) -> Dict[str, float]:
        resumo = {
            "taxa_liquidacao": 0.0,
            "emolumentos": 0.0,
            "taxa_corretagem": 0.0,
            "iss": 0.0,
            "irrf_day_trade": 0.0,
            "irrf_swing_trade": 0.0,
            "valor_liquido_nota": 0.0
        }

        def to_float(val_str):
            if not val_str: return 0.0
            clean = re.sub(r"[^\d\,\.]", "", val_str)
            if not clean: return 0.0
            if "," in clean:
                parts = clean.split(",")
                int_part = parts[0].replace(".", "")
                dec_part = parts[1]
                return float(f"{int_part}.{dec_part}")
            return float(clean.replace(".", ""))

        linhas = text.split("\n")
        
        # Taxa de Registro / Liquidação e Emolumentos
        for i in range(len(linhas)-1, -1, -1):
            l = linhas[i]
            if "Taxa registro BM&F" in l and i+1 < len(linhas):
                next_l = linhas[i+1].strip()
                if re.search(r"\d", next_l):
                    tokens = re.findall(r"[\d\.\,]+", next_l)
                    tokens = [t for t in tokens if re.search(r"\d", t)]
                    if len(tokens) >= 2:
                        resumo["emolumentos"] = to_float(tokens[-1])
                        resumo["taxa_liquidacao"] = to_float(tokens[-2])
                        if len(tokens) >= 3 and "Taxa Corretora" in l:
                            resumo["taxa_corretagem"] = to_float(tokens[-3])
                        break

        # IRRF e ISS
        for i in range(len(linhas)-1, -1, -1):
            l = linhas[i]
            if ("I.R.R.F. Day Trade" in l or "IRRF Day Trade" in l) and i+1 < len(linhas):
                next_l = linhas[i+1].strip()
                if re.search(r"\d", next_l):
                    tokens = re.findall(r"[\d\.\,]+", next_l)
                    tokens = [t for t in tokens if re.search(r"\d", t)]
                    if tokens:
                        resumo["irrf_day_trade"] = to_float(tokens[0])
                        if len(tokens) >= 3 and ("I.S.S." in l or "I.S.S" in l):
                            resumo["iss"] = to_float(tokens[2])
                        break

        # Total Líquido da Nota e Corretagem (Caso Warren)
        for i in range(len(linhas)-1, -1, -1):
            l = linhas[i]
            if "Total líquido da nota" in l and i+1 < len(linhas):
                next_l = linhas[i+1].strip()
                if re.search(r"\d", next_l):
                    tokens = re.findall(r"[\d\.\,]+", next_l)
                    tokens = [t for t in tokens if re.search(r"\d", t)]
                    if tokens:
                        resumo["valor_liquido_nota"] = to_float(tokens[-1])
                        if resumo["taxa_corretagem"] == 0.0 and len(tokens) >= 3:
                            resumo["taxa_corretagem"] = to_float(tokens[2])
                        break

        return resumo
