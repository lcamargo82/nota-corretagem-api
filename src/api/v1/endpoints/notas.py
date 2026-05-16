import os
import tempfile
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from src.core.config import settings
from src.core.security import get_current_authorized_system
from src.schemas.nota import NotaCorretagemResponse
from src.services.processor import NoteProcessorService, PDFDecryptionError

router = APIRouter()
processor_service = NoteProcessorService()

@router.post(
    "/processar",
    response_model=NotaCorretagemResponse,
    status_code=status.HTTP_200_OK,
    summary="Processar nota de corretagem em PDF",
    description="Recebe um arquivo PDF de nota de corretagem (padrão SINACOR) e extrai os dados financeiros estruturados. Requer autenticação JWT."
)
async def processar_nota(
    file: UploadFile = File(..., description="Arquivo PDF da nota de corretagem"),
    password: Optional[str] = Form(None, description="Senha de descriptografia do PDF (se protegido)"),
    current_system: dict = Depends(get_current_authorized_system)
) -> NotaCorretagemResponse:
    """
    Endpoint principal para extração de dados da nota de corretagem.
    Valida a extensão do arquivo, gerencia o armazenamento temporário,
    executa a extração via NoteProcessorService e retorna o contrato Pydantic.
    """
    logging.info(f"Requisição de processamento recebida do sistema: {current_system.get('sub', 'desconhecido')}")
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo enviado não é um PDF válido. Envie um arquivo com extensão .pdf."
        )

    # Cria arquivo temporário para processamento seguro no sistema de arquivos
    temp_file_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Executa o serviço de processamento
        dto = processor_service.process_note(temp_file_path, password=password)

        response = NotaCorretagemResponse(
            sucesso=True,
            ambiente=settings.ENVIRONMENT,
            dados=dto
        )
        return response

    except PDFDecryptionError as e:
        logging.warning(f"Erro de descriptografia no endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        logging.warning(f"Erro de validação nos dados extraídos: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logging.error(f"Erro interno ao processar nota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no servidor ao processar a nota: {str(e)}"
        )
    finally:
        # Garante a limpeza do arquivo temporário
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logging.error(f"Falha ao remover arquivo temporário {temp_file_path}: {e}")
