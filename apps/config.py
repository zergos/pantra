from pantra.defaults import Config

class AppConfig(Config):
    # apps configs
    #DEFAULT_APP: str = 'demo'
    #WIPE_LOGGING = True
    LOG_LEVEL = 'info'

    MIN_TASK_THREADS=1
    MAX_TASK_THREADS=2

    #SESSION_TTL = 30

    #JS_SERIALIZER_LOGGING = True
    #JS_ADD_IDS = True
