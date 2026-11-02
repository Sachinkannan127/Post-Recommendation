"""
Application Configuration and Settings Module.
Loads environment variables safely using Pydantic Settings.
"""
import os
from typing import Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")
    
    PROJECT_NAME: str = "NextGen AI Social Commerce Recommendation Engine"
    API_V1_STR: str = "/api"
    
    # MongoDB Atlas Connection Configuration
    MONGODB_URI: str = Field(
        default="mongodb+srv://Testusers:JyzhXqF0DxjhjllK@cluster0.947yt.mongodb.net/",
        description="MongoDB connection string"
    )
    MONGODB_DB_NAME: str = Field(
        default="social_commerce_db",
        description="Target database name"
    )
    
    # Default Hybrid Recommendation Weights (Section 5)
    WEIGHT_CONTENT: float = 0.30
    WEIGHT_ENGAGEMENT: float = 0.20
    WEIGHT_SOCIAL: float = 0.15
    WEIGHT_COMMERCE: float = 0.15
    WEIGHT_POPULARITY: float = 0.10
    WEIGHT_FRESHNESS: float = 0.10
    
    # Business Logic Hyperparameters
    RECENCY_HALF_LIFE_DAYS: float = 7.0
    FATIGUE_PENALTY: float = 0.30
    EXPLORATION_RATE: float = 0.12
    EMBEDDING_DIM: int = 64
    


settings = Settings()
