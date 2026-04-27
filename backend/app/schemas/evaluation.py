from pydantic import BaseModel


class EvaluationMetric(BaseModel):
    metric_name: str
    metric_value: float

