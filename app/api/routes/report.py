from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
from io import BytesIO
from api.model.report import ReportRequest, ReportResponse

router = APIRouter()

@router.post("/generate_report", response_model=ReportResponse)
async def generate_report(report_request: ReportRequest):
    """
    Эндпоинт для генерации PDF отчета на основе переданных чисел и идентификатора.
    Пока что возвращает моковый PDF.
    """
    # Валидация входных данных уже выполняется Pydantic моделями

    # Здесь должна быть логика генерации PDF на основе report_request.numbers и report_request.id
    # Пока что создадим моковый PDF как байтовый поток

    try:
        # Создаем простой PDF в памяти
        pdf_content = BytesIO()
        pdf_content.write(b"%PDF-1.4\n%Mock PDF content\n")
        pdf_content.seek(0)

        response = ReportResponse(
            report_id=report_request.id,
            message="Отчет успешно сгенерирован."
        )

        headers = {
            "Content-Disposition": f"attachment; filename=report_{report_request.id}.pdf"
        }

        return StreamingResponse(pdf_content, media_type="application/pdf", headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при генерации отчета.") from e
