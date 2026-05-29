class Settings:
    ENABLE_TRACE = True
    ENABLE_VALIDATION = True
    ENABLE_RETRY = True
    MAX_RETRY = 2
    LLM_MODEL = "gpt-4o-mini"
    ATTEMPT_THRESHOLD = 3
    DEBUG : bool = False

settings = Settings()