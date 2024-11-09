from pydantic import BaseModel, Field
from typing import Any, List, Optional

class ReportRequest(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор запроса")
    turn_criteria: List[int] = Field(..., default_factory=lambda: [1, 2, 3, 4, 5, 6] )

class ReportResponse(BaseModel):
    report_id: int = Field(..., description="Идентификатор сгенерированного отчета")
    message: str = Field(..., description="Сообщение о статусе генерации отчета")
