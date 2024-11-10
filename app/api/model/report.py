from pydantic import BaseModel, Field
from typing import Any, List, Dict, Optional

class ReportRequest(BaseModel):
    urls: List[str] = Field(..., example=[
        "https://zakupki.mos.ru/auction/9864533",
        "https://zakupki.mos.ru/auction/9864708",
        "https://zakupki.mos.ru/auction/9864771",
        "https://zakupki.mos.ru/auction/9864863",
        "https://zakupki.mos.ru/auction/9864870",
        "https://zakupki.mos.ru/auction/9864884",
        "https://zakupki.mos.ru/auction/9864977",
        "https://zakupki.mos.ru/auction/9862417",
        "https://zakupki.mos.ru/auction/9862374",
        "https://zakupki.mos.ru/auction/9862366"
    ])
    
    criterion: Optional[List[int]] = Field(
        default_factory=lambda: [1, 2, 3, 4, 5, 6],
        example=[1, 2, 3, 4, 5, 6]
    )

class ReportResponse(BaseModel):
    report_id: int = Field(..., description="Идентификатор сгенерированного отчета")
    message: str = Field(..., description="Сообщение о статусе генерации отчета")
