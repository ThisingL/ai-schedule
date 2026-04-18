from sqlalchemy import Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AiConfig(Base):
    __tablename__ = "ai_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    api_key: Mapped[str] = mapped_column(Text, nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False, default="https://api.siliconflow.cn/v1")
    model: Mapped[str] = mapped_column(String(200), nullable=False, default="deepseek-ai/DeepSeek-V3")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
