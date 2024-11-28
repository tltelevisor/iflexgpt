import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # LLM = 'PrivateGPT'
    LLM = 'OpenAI'
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-3.5-turbo"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mail_to_snow'
    URL_PGPT = "http://5.180.174.86:8001/"
    #sockettimeout = 600 см. __init__.py
    #URL_PGPT = "http://127.0.0.1:8001/"
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FULL_ACCESS_ROLE = (1,2)
    CONTEXT_WINDDOW = 3900# из файла settings-ollama.yaml, кол-во токенов
    MAX_LENGHT_POST_TO_SAVE = 2.2*3900 #8580 среднее количество знаков в токене на макс. кол-во токенов
    UPLOAD_FOLDER = './products_files'
    ALLOWED_EXTENSIONS = {'txt', 'pdf','doc','docs','docx'}
    MAX_TOKENS_IN_BATCH = 2000 #3900 - 900 #максимальное количество токенов в батчах (частях), на который будет разделен
    # загружаемый файл. Макс. кол-во токенов - ожидаемое максимальное количество токенов в запросе
    # поле text таблицы Batch - String(MAX_TOKENS_IN_BATCH * 2.2 среднее количество знаков в токене)
    DELIMITERS = ["\n", ". ", " "] #разелители, по которым будет разделен файл (в порядке предпочтения)
    #["\n\n", "\n", ". ", " "]
    #MAX_CONTENT_LENGTH = 16 * 1024 * 1024 #максимальный размер загружаемого файла
    NUMBERS_FAQ_REPLY = 1 #Количество ответов из FAQ, которые выдаются как подходящие при запросе в чате
