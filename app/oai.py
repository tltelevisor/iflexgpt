import app
from app import app
from app.models import Files
from openai import OpenAI

client = OpenAI(api_key = app.config['OPENAI_API_KEY'])
openai_model = app.config['OPENAI_MODEL']

def result_context_oai(messages, cf_id):
    files = Files.query.filter(Files.id.in_(cf_id)).all()
    file_content = ''
    for ef in files:
        file_path = f'{app.config["UPLOAD_FOLDER"]}/{ef.prdct_id}/{ef.filename}'
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file_content + '\n' + file.read()
    new_messages = []
    for idx, em in enumerate(messages):
        if idx == (len(messages) - 1):
            new_mess = {"role": "user",
                        "content": f"Здесь контекст из файлов:\n{file_content}\n\nПожалуйста, ответь на вопрос: {em['content']}"}
        else:
            new_mess = em
        new_messages.append(new_mess)

    response = client.chat.completions.create(
        messages=new_messages,
        model = openai_model
    )
    app.logger.info(f'prompt_tokens: {response.usage.prompt_tokens}, completion_tokens: {response.usage.completion_tokens}')
    return response.choices[0].message.content.strip()

def result_no_context_oai(messages):
    response = client.chat.completions.create(
        messages=messages,
        model = openai_model
    )
    app.logger.info(f'prompt_tokens: {response.usage.prompt_tokens}, completion_tokens: {response.usage.completion_tokens}')
    return response.choices[0].message.content.strip()