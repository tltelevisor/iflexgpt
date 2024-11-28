from app import app, db
from app.models import Batch, catgr_batches
import pickle
from pgpt_python.client import PrivateGPTApi
#https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2
from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
from mistral_common.protocol.instruct.messages import UserMessage
from sqlalchemy import insert, delete
from mistral_common.protocol.instruct.request import ChatCompletionRequest
tokenizer = MistralTokenizer.v1()


max_tokens = app.config['MAX_TOKENS_IN_BATCH']
delimiters = app.config['DELIMITERS']

client = PrivateGPTApi(base_url=app.config['URL_PGPT'], timeout=None)


def num_tokens(text: str):
    completion_request = ChatCompletionRequest(messages=[UserMessage(content=text)])
    tokens = tokenizer.encode_chat_completion(completion_request).tokens
    return len(tokens)

def tot_tokens(messages: list):
    total_tokens = 0
    for message in messages:
        total_tokens += num_tokens(message["role"])
        total_tokens += num_tokens(message["content"])
    return total_tokens

def trunc_string(string, max_tokens):
    if num_tokens(string) <= max_tokens:
        truncated_string = string
    else:
        completion_request = ChatCompletionRequest(messages=[UserMessage(content=string)])
        tokens = tokenizer.encode_chat_completion(completion_request).tokens
        truncated_string = tokenizer.decode(tokens[:max_tokens]).partition('[INST] ')[2].partition(' [/INST]')[
            0].lstrip().rstrip()
    return truncated_string


def del_string(string, max_tokens, delimiters):
    if num_tokens(string) <= max_tokens:
        left_str_out, right_str = string, ''
    else:
        truncated_string = trunc_string(string, max_tokens)
        for delimiter in delimiters:
            crt_str = truncated_string.rpartition(delimiter)
            dlm = delimiter
            left_str, right_str = crt_str[0], crt_str[2]
            if left_str == '' and delimiter == delimiters[-1]:
                left_str, right_str, dlm = crt_str[2], '', ''
            elif left_str == '':
                continue
            else:
                break
        rst, left_str_out, right_str = string.partition(left_str + dlm)
    return left_str_out.lstrip().rstrip(), right_str.lstrip().rstrip()


def split_strings_from_text(text, max_tokens=max_tokens, delimiters=delimiters):
    string = text
    num_tokens_in_string = num_tokens(string)
    if num_tokens_in_string <= max_tokens:
        return [string]
    else:
        left_str, right_str = del_string(string, max_tokens, delimiters)
        str_list = [left_str]
        while len(right_str) > 0:
            # print('--',right_str,'==')
            left_str, right_str = del_string(right_str, max_tokens, delimiters)
            str_list.append(left_str)
    return str_list

def split_file(file_id: object, str_list: object, lst_cat) -> object:
    for estr in str_list:
        embed = pickle.dumps(client.embeddings.embeddings_generation(input=estr).data[0].embedding)
        batch = Batch(text=estr,embed=embed,file_id=file_id)
        db.session.add(batch)
        db.session.commit()
        with db.engine.connect() as conn:
            for ec in lst_cat:
                conn.execute(insert(catgr_batches).values(cat_id=ec, batch_id=batch.id))
            conn.commit()
    return str_list


if __name__ == '__main__':
    with open('../utilits/text.txt') as f:
    #f'{app.config["UPLOAD_FOLDER"]}/{prdctid}/{filename}'
    #with open('.'+app.config['UPLOAD_FOLDER']+'/2/MG_recognized.txt') as f:
        text = f.read()
    #max_tokens = 1000
    #delimiters = ["\n\n", "\n", ". ", " "]
    str_list = split_strings_from_text(text, max_tokens, delimiters)
    print(f'Файл состоит из {num_tokens(text)} токенов. Разбит на {len(str_list)} блоков')

    for i,ee in enumerate(str_list):
        print(f'Блок {i}, {num_tokens(ee)}, {ee[:50]}')