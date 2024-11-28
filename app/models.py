from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db, login, app
from flask_login import UserMixin


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class rolepr(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rlname = db.Column(db.String(64), index=True, unique=True)
    users = db.relationship('User', backref='rolepr_bck', lazy='dynamic')

    def __repr__(self):
        return '<rolepr {}>'.format(self.rlname)

class Context(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    filehash = db.Column(db.Integer, db.ForeignKey('files.filehash'))
    isincntx = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return '<Context {}>'.format(self.isincntx)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    last_seen = db.Column(db.DateTime, default=datetime.now())
    rolepr_id = db.Column(db.Integer, db.ForeignKey('rolepr.id'), default=3)
    products = db.relationship('Products', backref='manager', lazy='dynamic')
    files = db.relationship('Files', backref='wholoadf', lazy='dynamic')
    context = db.relationship('Context', backref='whosecntx', lazy='dynamic')
    cntxstr = db.Column(db.String(440),default='{}') #100*20*22 (100 продуктов, 20 файлов, 20+2 знаков)
    faq = db.relationship('Faq', backref='author', lazy='dynamic')
    topic = db.relationship('Topic', backref='author_topic', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Faq(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(4000))
    answer = db.Column(db.String(4000))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    prdct_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    emb_q = db.Column(db.LargeBinary, nullable=False)  # тип данных BLOB
    emb_a = db.Column(db.LargeBinary, nullable=False)  # тип данных BLOB
    ispublic = db.Column(db.Boolean, default=False, nullable=False)
    answ_faq = db.relationship('Answ_faq', backref='whatfaq', lazy='dynamic')

    def __repr__(self):
        return '<Faq {}>'.format(self.id)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(8580)) #MAX_LENGHT_POST_TO_SAVE
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reply_id = db.Column(db.Integer) #reply_id = db.Column(db.Integer, db.ForeignKey('Post.id'))
    user_context = db.Column(db.String(440))
    is_satisfied = db.Column(db.Boolean, default=None, nullable=True)
    is_done = db.Column(db.Boolean, default=False, nullable=True)
    #answ_faq = db.relationship('Answ_faq', backref='whatpost', lazy='dynamic')
    #topic = db.Column(db.String(100))
    topic = db.Column(db.Integer, db.ForeignKey('topic.id'))
    #post_id_topic = db.relationship('Topic', backref='lastpost', lazy='dynamic')

    def __repr__(self):
        return '<Post {}>'.format(self.body)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer)
    posts = db.relationship('Post', backref='whypost', lazy='dynamic')

    def __repr__(self):
        return '<Topic {}>'.format(self.text)
class Answ_faq(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_quest = db.Column(db.Integer, db.ForeignKey('post.id'))
    id_faq = db.Column(db.Integer, db.ForeignKey('faq.id'))
    rltdns = db.Column(db.Numeric(precision=10, scale=2))
    prdct_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    is_done = db.Column(db.Boolean, default=False, nullable=True)

    def __repr__(self):
        return '<Answ_faq {}>'.format(self.id)

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prdctname = db.Column(db.String(64), index=True, unique=True)
    mngr_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    filespr = db.relationship('Files', backref='product_fl', lazy='dynamic')
    faq = db.relationship('Faq', backref='product', lazy='dynamic')

    def __repr__(self):
        return '<Product {}>'.format(self.prdctname)

catgr_files = db.Table('catgr_files',
    db.Column('cat_id', db.Integer, db.ForeignKey('catgr.id')),
    db.Column('file_id', db.Integer, db.ForeignKey('files.id')))

catgr_batches = db.Table('catgr_batches',
    db.Column('cat_id', db.Integer, db.ForeignKey('catgr.id')),
    db.Column('batch_id', db.Integer, db.ForeignKey('batch.id')))

prd_cat_faq = db.Table('prd_cat_faq',
    db.Column('prd_id', db.Integer, db.ForeignKey('products.id')),
    db.Column('cat_id', db.Integer, db.ForeignKey('catgr.id')),
    db.Column('faq_id', db.Integer, db.ForeignKey('faq.id')),
    db.Column('faq_shr_id', db.Integer, db.ForeignKey('faq.id')))

class Files(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(64), index=True, unique=True)
    filehash = db.Column(db.Integer, index=True, unique=True)
    filedateload = db.Column(db.DateTime, default=datetime.now())
    wholoadfile = db.Column(db.Integer, db.ForeignKey('user.id'))
    idfilegpt = db.Column(db.String(64), index=True, unique=False)
    ispublic = db.Column(db.Boolean, default=False, nullable=False)
    prdct_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    tokens = db.Column(db.Integer)
    bathes = db.Column(db.Integer, default=0)
    context = db.relationship('Context', backref='cntxfile', lazy='dynamic')
    batch = db.relationship('Batch', backref='file', lazy='dynamic')
    #Удалить этот столбец
    #cat_id = db.Column(db.Integer, db.ForeignKey('catgr.id'), index=True)
    #file_cat = db.relationship('Batch', backref='cat_file_', lazy='dynamic')
    # catgr_files = db.relationship('Catgr', secondary=catgr_files, lazy='subquery',
    #     backref=db.backref('files_', lazy=True))

    def __repr__(self):
        return '<File {}>'.format(self.filename)

class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(6600), index=True, unique=True) #Максимальное колиечество символов в батче
    embed = db.Column(db.LargeBinary, nullable=False)  # тип данных BLOB, embeddings
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'))
    #cat_id = db.Column(db.Integer, db.ForeignKey('catgr.id'))

    def __repr__(self):
        return '<Batch {}>'.format(self.text[:100])

class Catgr(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    #file = db.relationship('Files', backref='cat_file', lazy='dynamic')
    #batch = db.relationship('Batch', backref='cat_batch', lazy='dynamic')
    #cat_file = db.relationship('Batch', backref='file_cat_', lazy='dynamic')

    def __repr__(self):
        return '<Catgr {}>'.format(self.name)


