from flask import render_template, flash, redirect, url_for, request, jsonify
from app import app, db
from app.files import split_strings_from_text, split_file, num_tokens
from app.forms import LoginForm, RegistrationForm, PostForm, ProductsForm, NewFAQ
from pgpt_python.client import PrivateGPTApi
from app.handler import ( response_json, topic_posts_f,
                         posts_to_view_to_handling, topics_f, prdct_id_nm,
                         dic_cat_file_f, cat_pr_faq_f, response_cat, serv_status)
from flask_login import current_user, login_user, logout_user, login_required
from app.models import (User, Post, Products, Files, rolepr, Faq, Batch, Catgr, Answ_faq,
                        catgr_files, catgr_batches, prd_cat_faq)
from datetime import datetime
from sqlalchemy import insert, delete
from os import remove
import ast, pickle


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now()
        db.session.commit()


@app.route('/test', methods=['GET', 'POST'])
@login_required
def test():
    return render_template('handl_answ.html')


@app.route('/product_files/<prdctid>', methods=['GET', 'POST'])
@login_required
def product_files(prdctid):
    cats = cat_pr_faq_f(prdctid)
    product = Products.query.filter_by(id=prdctid).first_or_404()
    files_db = Files.query.filter_by(prdct_id=prdctid)
    files = []
    for ef in files_db:
        username = User.query.filter_by(id=Files.query.filter_by(id=ef.id)[0].wholoadfile)[0].username
        files.append([ef, dic_cat_file_f(ef.id), username, ef.tokens, ef.bathes])
    return render_template('product_files_show.html', status=serv_status(), product=product,
                           files=files, cats=cats)


# Запрос GPT заполнить описание продукта перед сохранением этого описания в категории
@app.route('/askgpt', methods=['POST'])
@login_required
def askgpt():
    mess = request.json
    rsp = response_cat(mess)
    return jsonify(rsp)


# Запрос краткого описания продукта из формы index.html
@app.route('/getprshr', methods=['POST'])
@login_required
def getprshr():
    prd_id = int(request.json)
    cat_pr_faq = cat_pr_faq_f(prd_id)
    text = f''
    for ec in cat_pr_faq:
        text += f'{ec[1]}: {ec[7]}\n'
    return jsonify(text)


# Сохранение в faq описания категории продукта
@app.route('/svfaq', methods=['POST'])
@login_required
def svfaq():
    client = PrivateGPTApi(base_url=app.config['URL_PGPT'], timeout=None)
    mess = request.json
    # print(mess)
    id, qu, an = mess['faq_id'], mess['quest'], mess['answ']
    print('id', id)
    faq = Faq.query.filter_by(id=id)[0]
    emb_q = pickle.dumps(client.embeddings.embeddings_generation(input=qu).data[0].embedding)
    emb_a = pickle.dumps(client.embeddings.embeddings_generation(input=an).data[0].embedding)
    faq.question, faq.answer, faq.emb_q, faq.emb_a = qu, an, emb_q, emb_a
    db.session.commit()
    return jsonify({'error': '0'})


# Удалить файл из перечня в продукте
@app.route('/delete', methods=['POST'])
@login_required
def delete_file():
    client = PrivateGPTApi(base_url=app.config['URL_PGPT'], timeout=None)
    fileid = int(request.json)
    batch_lst = [eb.id for eb in Batch.query.filter_by(file_id=fileid)]
    row_to_delete = Files.query.get_or_404(fileid)
    # row_to_delete_batch = Batch.query.filter_by(file_id=fileid)
    prdctid = row_to_delete.prdct_id
    Files.query.filter_by(id=fileid).delete()
    Batch.query.filter_by(file_id=fileid).delete()
    filename_to_delete = f'{app.config["UPLOAD_FOLDER"]}/{prdctid}/{row_to_delete.filename}'
    try:
        remove(filename_to_delete)
    except FileNotFoundError:
        app.logger.error(f'Нет файла для удаления {filename_to_delete}')
        # rsp = f'Нет файла для удаления {filename_to_delete}'
        # return jsonify({'error': '1', 'message': rsp})
    try:
        if app.config['LLM'] == 'OpenAI':
            pass
        elif app.config['LLM'] == 'PrivateGPT':
            client.ingestion.delete_ingested(row_to_delete.idfilegpt)
        else:
            rsp = f'Нет обработчика для выбранной LLM config.py {app.config["LLM"]} модели.'
            return jsonify({'error': '1', 'message': rsp})
    except Exception as err:
        rsp = f'Выбранная в LLM config.py {app.config["LLM"]} языковая модель недоступна.'
        app.logger.error(f'120: {err}')
        return jsonify({'error': '1', 'message': rsp})

    # client.ingestion.delete_ingested(row_to_delete.idfilegpt)
    db.session.commit()
    with db.engine.connect() as conn:
        conn.execute(delete(catgr_files).where(catgr_files.c.file_id == fileid))
        conn.execute(delete(catgr_batches).where(catgr_batches.c.batch_id.in_(batch_lst)))
        conn.commit()

    # проверить что в catgr_files catgr_batches удаление произошло
    rsp = f'Файл {filename_to_delete} удалён'
    # return redirect(url_for('product',prdctid=prdctid))
    return jsonify({'error': '0', 'message': rsp})


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    client = PrivateGPTApi(base_url=app.config['URL_PGPT'], timeout=None)
    prdctid = int(request.form.get('prd_id'))
    product = Products.query.filter_by(id=prdctid).first_or_404()
    # print(dir(request.files))
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден в запросе'}), 400
    file = request.files['file']
    filename = file.filename
    ispublic = True if request.form.get('newpub') == '1' else False
    cats = Catgr.query.all()
    lst_cat = [ec.id for ec in cats if request.form.get(f'newcat-{ec.id}')]
    # print(lst_cat)
    if allowed_file(filename):
        filename_to_save = f'{app.config["UPLOAD_FOLDER"]}/{prdctid}/{filename}'
        file.save(filename_to_save)
        try:
            if app.config['LLM'] == 'OpenAI':
                ingested_file_doc_id = 0
            elif app.config['LLM'] == 'PrivateGPT':
                with open(filename_to_save, "rb") as f:
                    ingested_file_doc_id = client.ingestion.ingest_file(file=f).data[0].doc_id
            else:
                rsp = f'Нет обработчика для выбранной LLM config.py {app.config["LLM"]} модели.'
                ingested_file_doc_id = 0
                return jsonify({'error': '1', 'message': rsp})
        except Exception as err:
            rsp = f'Выбранная в LLM config.py {app.config["LLM"]} языковая модель недоступна.'
            app.logger.error(f'166: {err}')
            return jsonify({'error': '1', 'message': rsp})
        with open(filename_to_save, 'r') as f:
            text = f.read()
            file_hash = hash(text)
            tokens = num_tokens(text)
            bathes = split_strings_from_text(text)
        file = Files(filename=filename, filehash=file_hash, wholoadfile=int(current_user.id),
                     idfilegpt=ingested_file_doc_id, ispublic=ispublic, prdct_id=int(prdctid), tokens=tokens,
                     bathes=len(bathes))
        db.session.add(file)
        db.session.commit()
        with db.engine.connect() as conn:
            for ec in lst_cat:
                conn.execute(insert(catgr_files).values(cat_id=ec, file_id=file.id))
            conn.commit()
        split_file(file.id, bathes, lst_cat)
        access = 'публичного' if ispublic else 'ограниченного'
        flstr = f'Файл {filename} добавлен к описанию продукта {product.prdctname} в режиме {access} доступа.'
        if len(bathes) > 0:
            flstr = flstr + f'\nФайл составляет {tokens} токенов и разбит на {len(bathes)} частей.'
        return jsonify({'error': '0', 'message': flstr}), 200
    return jsonify({'error': 'Недопустимое имя файла или другая ошибка загрузки'}), 400


@app.route('/product/<prdctid>', methods=['GET', 'POST'])
@login_required
def product(prdctid):
    cats = cat_pr_faq_f(prdctid)
    # flash(f'Здесь будут появляться flash-сообщения')
    # prdctid = 2
    product = Products.query.filter_by(id=prdctid).first_or_404()
    # cats = Catgr.query.all()
    files_db = Files.query.filter_by(prdct_id=prdctid)
    files = []
    for ef in files_db:
        username = User.query.filter_by(id=Files.query.filter_by(id=ef.id)[0].wholoadfile)[0].username
        files.append([ef, dic_cat_file_f(ef.id), username, ef.tokens, ef.bathes])
    nh_answ = Answ_faq.query.filter_by(prdct_id=prdctid).filter_by(is_done=False).count()
    return render_template('product.html', status=serv_status(), product=product,
                           files=files, cats=cats, nh_answ=nh_answ)


@app.route('/prod_view/<prdctid>', methods=['GET', 'POST'])
@login_required
def prod_view(prdctid):
    product = Products.query.filter_by(id=prdctid).first_or_404()
    cats = cat_pr_faq_f(prdctid)
    return render_template('prod_view.html', status=serv_status(), product=product, cats=cats)


# Отправка сообщений в чатбот из формы index.html
@app.route('/send', methods=['POST'])
@login_required
def send():
    mess = request.json
    rsp = response_json(current_user.id, mess)
    # print(rsp)
    # print(rsp['context'])
    return jsonify(rsp)


# Выбор темы из формы index.html
@app.route('/topic', methods=['POST'])
@login_required
def topic():
    topic = request.json
    rsp = topic_posts_f(current_user.id, topic)
    # print(rsp)
    return jsonify(rsp)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    id_topics = topics_f(current_user.id)
    cats = Catgr.query.all()
    # flash(f'Здесь будут появляться flash-сообщения')
    products = Products.query.all()
    if current_user.rolepr_id in app.config['FULL_ACCESS_ROLE']:
        files = Files.query.all()
    else:
        files = Files.query.filter(Files.ispublic).all()
    form = PostForm()
    cntxstr = ast.literal_eval(current_user.cntxstr)
    prdct_ids, prdct_nms = prdct_id_nm(cntxstr)
    if form.validate_on_submit():
        cntxstr = {}
        for ef in files:
            if request.form.get(f'{ef.filehash}') is not None: cntxstr[str(ef.filehash)] = '1'
        str_cntxstr = str(cntxstr)
        post = Post(body=form.post.data, author=current_user, user_context=str_cntxstr)
        row_to_change = User.query.get_or_404(current_user.id)
        row_to_change.cntxstr = str_cntxstr
        db.session.add(post)
        db.session.commit()
        # postid = Post.query.filter(Post.user_id == current_user.id).order_by(Post.id.desc()).first().id
        postid = post.id
        # response(form.post.data,cntxstr,current_user.id, postid)
        return redirect(url_for('index'))
    return render_template("index.html", status=serv_status(), title='iFlexGPT',
                           products=products, form=form,  files=files, cntxstr=cntxstr,
                            prdct_nms=prdct_nms, id_topics=id_topics, cats=cats)


@app.route('/handl_answ', methods=['GET', 'POST'])
@app.route('/handl_answ/<prdctid>', methods=['GET', 'POST'])
@login_required
def handl_answ(prdctid=0):
    client = PrivateGPTApi(base_url=app.config['URL_PGPT'], timeout=None)
    form = NewFAQ()
    form_id, form_name = "faq_add", "faq_add"
    posts = posts_to_view_to_handling(current_user.id, prdctid)
    prdcts = Products.query.all()
    # if len(posts) == 0:
    #     return render_template('handl_answ_0.html')

    if request.method == 'POST':
        lst_pst = []
        for ep in posts:
            if request.form.get(f'{ep[0]}-chk') is not None:
                lst_pst.append(ep[0])

        row_to_change = Post.query.filter(Post.id.in_(lst_pst))
        row_to_change = Answ_faq.query.filter(Answ_faq.id.in_(lst_pst))
        row_to_change.update({'is_done': True})
        question, answer = request.form.get(f'question'), request.form.get(f'answer')
        prd_id = request.form.get(f'product')
        prdctid = prd_id
        ispublic = True if request.form.get(f'ispublic') == 'y' else False
        if question is not None:
            emb_q = pickle.dumps(client.embeddings.embeddings_generation(input=question).data[0].embedding)
            emb_a = pickle.dumps(client.embeddings.embeddings_generation(input=answer).data[0].embedding)
            faq = Faq(question=question, answer=answer, emb_q=emb_q, emb_a=emb_a,
                      user_id=current_user.id, prdct_id=prd_id, ispublic=ispublic)
            db.session.add(faq)
        db.session.commit()
        return render_template('handl_answ.html', status=serv_status(), posts=posts, form=form, id=form_id,
                               name=form_name, prdcts=prdcts, prdctid=prdctid)
    return render_template('handl_answ.html', status=serv_status(), posts=posts, form=form, id=form_id, name=form_name,
                           prdcts=prdcts, prdctid=prdctid)


@app.route('/test_register', methods=['GET', 'POST'])
def test_register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('test_register.html', title='Register', form=form)


@app.route('/test_login', methods=['GET', 'POST'])
def test_login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя или пароль')
            return redirect(url_for('login'))
        login_user(user, remember=True)  # form.remember_me.data
        return redirect(url_for('index'))
    return render_template('test_login.html', title='Sign In', form=form)


@app.route('/products', methods=['GET', 'POST'])
@login_required
def products():
    form = ProductsForm()
    products = Products.query.all()

    if form.validate_on_submit():
        product = Products(prdctname=form.prdctname.data, mngr_id=form.manager.data)
        db.session.add(product)
        db.session.commit()
        p_id, u_id = product.id, current_user.id
        ques_shr = f'Опиши коротко, не более чем в трех предложениях, характеристику продукта по категории '
        ques_long = f'Опиши подробно характеристику продукта по категории '
        for ec in Catgr.query.all():
            faq = Faq(question=ques_shr, answer='', prdct_id=p_id, user_id=u_id, ispublic=True)
            db.session.add(faq)
            db.session.commit()
            faq_id_shr = faq.id
            faq = Faq(question=ques_long, answer='', prdct_id=p_id, user_id=u_id, ispublic=True)
            db.session.add(faq)
            db.session.commit()
            faq_id_long = faq.id
            with db.engine.connect() as conn:
                conn.execute(
                    insert(prd_cat_faq).values(prd_id=p_id, cat_id=ec.id, faq_id=faq_id_long, faq_shr_id=faq_id_shr))
                conn.commit()
        # flash(f'Вы ввели новый продукт {form.prdctname.data}!')
        return redirect(url_for('products'))
    return render_template("products.html", status=serv_status(), title='Products', form=form, products=products)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', status=serv_status(), title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):  #
    rols = rolepr.query.all()
    print(app.config['OPENAI_API_KEY'])
    return render_template('user.html', status=serv_status(), user=current_user, username=username, rols=rols)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя или пароль')
            return redirect(url_for('login'))
        login_user(user, remember=True)  # form.remember_me.data
        return redirect(url_for('index'))
    return render_template('login.html', status=serv_status(), title='Sign In', form=form)


@app.route('/chngisp/<fileid>', methods=['GET', 'POST'])
@login_required
def chngisp(fileid):
    row_to_change = Files.query.get_or_404(fileid)
    prdctid = row_to_change.prdct_id
    ispublic = request.form.get(f'{fileid}')
    ispublic = True if ispublic == '1' else False
    row_to_change.ispublic = ispublic
    # row_to_change.ispublic = not row_to_change.ispublic
    db.session.commit()
    return redirect(url_for('product', prdctid=prdctid))


@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    users = User.query.all()
    rols = rolepr.query.all()
    return render_template('users.html', status=serv_status(), users=users, rols=rols)


@app.route('/chngrl/<userid>', methods=['GET', 'POST'])
@login_required
def chngrl(userid):
    row_to_change = User.query.get_or_404(userid)
    rols = rolepr.query.all()
    selected_role = rols[row_to_change.rolepr_id]
    if request.method == "POST":
        selected_role = request.form.get(f'{row_to_change.username}')
        row_to_change.rolepr_id = selected_role
        db.session.commit()
        return redirect(url_for('users', userid=userid))
