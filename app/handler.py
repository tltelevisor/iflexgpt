from app import app, db
from app.models import Files, Post, Faq, Products, User, Answ_faq, Topic, catgr_files, Catgr, prd_cat_faq
from scipy import spatial
from pgpt_python.client import PrivateGPTApi
import pandas as pd
import pickle, ast
from sqlalchemy import select, and_
from numpy import round
from app.oai import result_context_oai, result_no_context_oai


def serv_status():
    if app.config['LLM'] == 'OpenAI':
        status = [0, f'(oai)']
    elif app.config['LLM'] == 'PrivateGPT':
        try:
            client = PrivateGPTApi(base_url=app.config['URL_PGPT'], timeout=10)
            if client.health.health().status == 'ok':
                status = [0, f'(pgpt)']
            else:
                status = [1, client.health.health()]
        except Exception as err:
            status = [1, f'Сервер PrivateGPT не отвечает']
            app.logger.error(f'29: {err}')
    else:
        status = [1, f'Нет обработчика для {app.config["LLM"]} модели.']
    app.logger.info(f"return status: {app.config['LLM']}, {status}")
    # logging.info(f"return status: {app.config['LLM']}, {status}")
    return status

#По id продкта возвращает список категорий и вопросов-ответов из FAQ, описывающих эти категории для данного прдукта
def cat_pr_faq_f(prd_id):
    cats = list(Catgr.query.all())
    with db.engine.connect() as conn:
        cat_faq = list(conn.execute(select(prd_cat_faq).where(prd_cat_faq.c.prd_id == prd_id)))
    cat_pr_faq = []
    for ec in cats:
        faq_id = [ecf[2] for ecf in cat_faq if ecf[1] == ec.id]
        if len(faq_id) != 0:
            if isinstance(faq_id[0], int):
                faq_id = faq_id[0]
                faq = Faq.query.filter_by(id=faq_id)[0]
                question = faq.question
                answer = faq.answer
            else:
                faq_id, question, answer = '','', ''
        else:
            faq_id, question, answer = '','', ''

        faq_id_shr = [ecf[3] for ecf in cat_faq if ecf[1] == ec.id]
        if len(faq_id_shr) != 0:
            if isinstance(faq_id_shr[0], int):
                faq_id_shr=faq_id_shr[0]
                faq = Faq.query.filter_by(id=faq_id_shr)[0]
                question_shr = faq.question
                answer_shr = faq.answer
            else:
                faq_id_shr, question_sht, answer_shr = '','', ''
        else:
            faq_id_shr, question_shr, answer_shr = '','', ''
        cat_pr_faq.append([ec.id, ec.name, faq_id, question, answer, faq_id_shr, question_shr, answer_shr])
    return cat_pr_faq

#По file_id возвращает список '1' и '0' - признаков есть такая категория у файла или нет (для формы Product.html)
def dic_cat_file_f(file_id):
    with db.engine.connect() as conn:
        cat_file = list(conn.execute(select(catgr_files).where(catgr_files.c.file_id == file_id)))
    cats_of_file = [ef[0] for ef in cat_file]
    cats = Catgr.query.order_by(Catgr.id).all()
    dic_cat_file = {}
    for ec in cats:
        dic_cat_file[ec.id] = '1' if ec.id in cats_of_file else '0'
    return dic_cat_file

#По выбранным в index.html контексам возвращает список id файлов для контекста запроса
def context_filter_id_f(context):
    #mess = {'gl_topic': '186', 'context': ['chkprd-1', 'chkprd-3', 'chkcat-2', 'chkfile-5', 'chkfile-6'], 'message': 'sfdf'}
    #context = mess['context']
    cat_lst,prd_lst,file_lst=[],[],[]
    for ec in context:
        ecprt = ec.partition('-')
        if ecprt[0] == 'chkcat':
            cat_lst.append(int(ecprt[2]))
        elif ecprt[0] == 'chkprd':
            prd_lst.append(int(ecprt[2]))
        elif ecprt[0] == 'chkfile':
            file_lst.append(int(ecprt[2]))
    cntxt_str = {}
    if len(prd_lst) : cntxt_str['prd'] = prd_lst
    if len(cat_lst): cntxt_str['cat'] = cat_lst
    if len(file_lst): cntxt_str['file'] = file_lst

    context_filter_file=[]
    for ef in Files.query.filter(Files.id.in_(file_lst)).all():
        if ef.id not in context_filter_file:
                context_filter_file.append(ef.id)
    context_filter_prd=[]
    for ef in Files.query.filter(Files.prdct_id.in_(prd_lst)).all():
        if ef.id not in context_filter_prd:
                context_filter_prd.append(ef.id)
    context_filter_id = context_filter_file
    for ef in context_filter_prd:
        if ef not in context_filter_id:
            ec_cat_sel = select(catgr_files).where(catgr_files.c.file_id == ef)
            with db.engine.connect() as conn:
                for ecf in conn.execute(ec_cat_sel):
                    if ecf[0] in cat_lst:
                        context_filter_id.append(ef)
                        break
    return context_filter_id, cntxt_str, prd_lst
#По id файлов возвращает список id-PrivateGPT файлов для контекста запроса
def context_filter_f(context_filter_id):
    context_filter =[]
    files = Files.query.filter(Files.id.in_(context_filter_id)).all()
    for ef in files:
        context_filter.append(ef.idfilegpt)
    return context_filter
#Сборка текста запроса из последнего сообщения и предыдущих из текущей темы
def collect_mess(user_id, topic, message):
    #user_id = 4
    #topic = 1
    sys_prompt = f'Ответь на русском языке'
    messages = [{"role": "user", "content": message}]
    if topic:
        pr_post = Topic.query.filter_by(id = topic)[0].post_id
        while pr_post:
            post = Post.query.filter_by(id = pr_post)[0]
            if post.user_id == 1:
                messages.insert(0, {"role": "assistant", "content": post.body})
            if post.user_id == user_id:
                messages.insert(0, {"role": "user", "content": post.body})
            pr_post = post.reply_id
    messages.insert(0,{"role": "system", "content": sys_prompt})
    return messages

#Пока не используется. Контроль длины запроса (вместиться ли в контекстное окно) и подготовка запроса.
def check_context_window_f(mess):
    if mess['topic']:
        int(mess['topic'])
    message = '9999'
    # ------
    return message

#Обработчик запросов к чатботу для заполнения описания продукта
def response_cat(mess):
    sys_prompt = f'Ответь на русском языке'
    messages = [{"role": "system", "content": sys_prompt}]
    messages.append({"role": "user", "content": mess['message']})
    if mess['context']:
        file_lst = []
        for ec in mess['context']:
            ecprt = ec.partition('-')
            if ecprt[0] == 'chkfile':
                file_lst.append(int(ecprt[2]))
        context_filter = context_filter_f(file_lst)
        try:
            if app.config['LLM'] == 'OpenAI':
                result = result_context_oai(messages, file_lst)
            elif app.config['LLM'] == 'PrivateGPT':
                result = result_context(messages, context_filter)
            else:
                result = f'Нет обработчика для выбранной LLM config.py модели.'
        except Exception as err:
            result = f'Выбранная в LLM config.py языковая модель недоступна.'
            app.logger.error(f"170 :{err}")
    else:
        try:
            if app.config['LLM'] == 'OpenAI':
                result = result_no_context_oai(messages)
            elif app.config['LLM'] == 'PrivateGPT':
                result = result_no_context(messages)
            else:
                result = f'Нет обработчика для выбранной LLM config.py модели.'
        except Exception as err:
            result = f'Выбранная в LLM config.py языковая модель недоступна.'
            app.logger.error(f'181 :{err}')

    return result

#Главный обработчик запросов к чатботу
def response_json(user_id, mess):
    post_fu = Post(body=mess['message'], user_id=user_id)
    topic = mess['topic']
    if topic: post_fu.reply_id = Topic.query.filter_by(id=topic)[0].post_id
    messages = collect_mess(user_id, topic, mess['message'])
    if mess['context']:
        cf_id, cntxt_str, prd_lst = context_filter_id_f(mess['context'])
        post_fu.user_context = str(cntxt_str)
        context_filter = context_filter_f(cf_id)
        try:
            if app.config['LLM'] == 'OpenAI':
                result = result_context_oai(messages, cf_id)
            elif app.config['LLM'] == 'PrivateGPT':
                result = result_context(messages, context_filter)
            else:
                result = f'Нет обработчика для выбранной LLM config.py модели.'
        except Exception as err:
            result = f'Выбранная в LLM config.py языковая модель недоступна (VPN?).'
            app.logger.error(f'204: {err}')
        cf_id = str(cf_id)

    else:
        cf_id, prd_lst = None, None
        try:
            if app.config['LLM'] == 'OpenAI':
                result = result_no_context_oai(messages)
            elif app.config['LLM'] == 'PrivateGPT':
                result = result_no_context(messages)
            else:
                result = f'Нет обработчика для выбранной LLM config.py модели.'
        except Exception as err:
            result = f'Выбранная в LLM config.py языковая модель недоступна.'
            app.logger.error(f'218: {err}')
    #check_context_window_f(messages, context_filter)
    try:
        db.session.add(post_fu)
        db.session.commit()
        post_fu_id = post_fu.id
        if topic:
            db_topic = Topic.query.filter_by(id=topic)[0]
        else:
            db_topic = Topic(text = mess['message'][:64], user_id = user_id)
            db.session.add(db_topic)
            db.session.commit()
            topic = db_topic.id #, mess['message'][:64]]
        post_fu.topic = topic
        post = Post(body=f'{result}',user_id=1,reply_id=post_fu_id,user_context=cf_id,is_done = False, topic = topic)
        db.session.add(post)
        db.session.commit()
        db_topic.post_id = post.id
        db.session.commit()
        answ_faq = Answ_faq_f(mess['message'], prd_lst, user_id, post_fu_id) if prd_lst else None
    except Exception as e:
        print(f'Ошибка {e}')

    #return result, topic, answ_faq if answ_faq else result, topic
    if answ_faq: return result, topic, answ_faq
    else: return result, topic

#Устарело?
def prdct_id_nm(cntxstr):
    files = Files.query.all()
    prdct_ids, prdct_nms= [], []
    for ef in files:
        if str(ef.filehash) in cntxstr.keys():
            prdct_name = Products.query.filter(Products.id == ef.prdct_id).first().prdctname
            prdct_id = Products.query.filter(Products.id == ef.prdct_id).first().id
            if prdct_id not in prdct_ids:
                prdct_ids.append(prdct_id)
                prdct_nms.append(prdct_name)
    return prdct_ids, prdct_nms

#Строка контекста для отправки в index.html при выборе темы (./topic)
def context_lst_f(post_id):
    context_str = Post.query.filter_by(id = post_id)[0].user_context
    context = ast.literal_eval(context_str)
    context_lst = []
    for ep in context:
        epdic = {}
        epdic['id'] = ep[0]
        epdic['prdctname'] = Products.query.filter_by(id = ep[0])[0].prdctname
        file_lst = []
        for ef in ep[1]:
            efdic = {}
            efdic['filename'] = Files.query.filter_by(filehash = ef)[0].filename
            efdic['filehash'] = ef
            file_lst.append(efdic)
            # file_lst.append([ef, Files.query.filter_by(filehash = ef)[0].filename])
            #print(ef)
        epdic['files'] = file_lst
        context_lst.append(epdic)
    return context_lst

#Права доступа по id пользователя
def is_all(user_id):
    full_acces = True if User.query.filter(User.id == user_id).first().rolepr_id in app.config['FULL_ACCESS_ROLE'] else False
    return full_acces

#Инициация dataframe для обработки совпадений FAQ
def df_init(prd_id, user_id):
    if is_all(user_id):
        faqs = Faq.query.filter_by(prdct_id = prd_id).all()
    else:
        faqs = Faq.query.filter_by(prdct_id = prd_id).filter_by(ispublic = True).all()
    df = pd.DataFrame([eq.__dict__ for eq in faqs])
    if df.shape[0] > 0:
        df = df.drop('_sa_instance_state', axis=1)
    return df

#top_n первых ответа из FAQ с высшим рейтингом
def strings_ranked_by_relatedness(
            query: str,
            df: pd.DataFrame,
            relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
            top_n: int = app.config['NUMBERS_FAQ_REPLY']#1 #
    ) -> tuple[list[str], list[float]]:
    if df.shape[0] > 0:
        client = PrivateGPTApi(base_url=app.config['URL_PGPT'], timeout=None)
        """Returns a list of strings and relatednesses, sorted from most related to least."""
        embedding_result = client.embeddings.embeddings_generation(input=query)
        query_embedding = embedding_result.data[0].embedding
        strings_and_relatednesses = [
            (row["id"], row["question"], relatedness_fn(query_embedding, pickle.loads(row["emb_q"])))
            for i, row in df.iterrows()
        ]
        strings_and_relatednesses.sort(key=lambda x: x[2], reverse=True)
        id, strings, relatednesses = zip(*strings_and_relatednesses)
        return id[:top_n], strings[:top_n], round(relatednesses[:top_n], 2)
    else:
        return [], [], []

#Выборка необработанных для FAQ постов (запрос и отправки из формы handl_answ.html)
def posts_to_view_to_handling(user_id, prdctid):
    #prd = Products.query.filter_by(mngr_id=user_id).all()
    quest_answ, lst_apost = [], []
    if prdctid == 0:
        prd_lst = [epr.id for epr in Products.query.filter_by(mngr_id=user_id).all()]
    else:
        prd_lst = [epr.id for epr in Products.query.filter_by(id=prdctid).filter_by(mngr_id=user_id).all()]
    aposts = Answ_faq.query.filter(and_(Answ_faq.prdct_id.in_(prd_lst), Answ_faq.is_done != True)).order_by(Answ_faq.prdct_id, Answ_faq.id_quest.desc(),Answ_faq.id).all()
    for ep in aposts:
        if ep.id_quest not in lst_apost:
            quest = f'{Post.query.filter_by(id=ep.id_quest)[0].body}'
            answer = Post.query.filter_by(reply_id = ep.id_quest)[0].body
            faq_quest = Faq.query.filter_by(id=ep.id_faq)[0].question
            faq_answ = Faq.query.filter_by(id=ep.id_faq)[0].answer
            faq = f'FAQ({ep.id_faq}:{ep.rltdns}): { faq_quest} | {faq_answ} )'
            quest_answ.append([ep.id, quest, answer, faq])
            #lst_apost.append(ep.id_quest) #Если ответов из FAQ больше, чем 1, но надо ограничить одним
    return quest_answ


#Запрос в PrivateGPT
def result_context(text, context_filter):
    client = PrivateGPTApi(base_url=app.config['URL_PGPT'], timeout=None)
    result = client.contextual_completions.chat_completion(
        messages=text,
        use_context=True,
        context_filter={"docs_ids": context_filter},
        include_sources=True,
    ).choices[0].message.content.strip()
    return result

#Запрос в PrivateGPT
def result_no_context(text):
    client = PrivateGPTApi(base_url=app.config['URL_PGPT'], timeout=None)
    result = client.contextual_completions.chat_completion(
        messages=text,
        use_context=False,
    ).choices[0].message.content.strip()
    return result

#Запись в БД ответов из FAQ
def Answ_faq_f(text, prdct_ids, user_id, postid):
    #prdct_ids , prdct_nms = prdct_id_nm(cntxstr)
    answ_faq = []
    for ep in prdct_ids:
        id, reply_text, rlt = strings_ranked_by_relatedness(text, df_init(ep, user_id))
        for i, eid in enumerate(id):
            answ_text = Faq.query.filter_by(id=eid)[0].answer
            answ_faq.append([ep, rlt[i], answ_text])
            answ_f = Answ_faq(id_quest=postid, id_faq=eid, rltdns=rlt[i], prdct_id=ep)
            db.session.add(answ_f)
            db.session.commit()
    return answ_faq


# Выборка тем для пользователя для раздела навигации в index.html
def topics_f(user_id):
    topics = Topic.query.filter_by(user_id = user_id).order_by(Topic.post_id.desc()).limit(7)
    id_topics = []
    for et in topics:
        id_topics.append([et.id,et.text[:27]+'...'])
    return id_topics

def topic_posts_f(user_id, topic):
    topic_posts, context = [], None
    if topic:
        pr_post = Topic.query.filter_by(id = topic)[0].post_id
        context = Post.query.filter_by(id = Post.query.filter_by(id = pr_post)[0].reply_id)[0].user_context
        while pr_post:
            post = Post.query.filter_by(id = pr_post)[0]
            if post.user_id == 1:
                topic_posts.insert(0, {'assistant': post.body})
            if post.user_id == user_id:
                topic_posts.insert(0, {'user': post.body})
            pr_post = post.reply_id
    if context: return {'topic_posts': topic_posts, 'context': ast.literal_eval(context)}
    else: return {'topic_posts': topic_posts}

