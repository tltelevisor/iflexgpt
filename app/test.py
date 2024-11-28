from app import app, db
from app.models import Files, Post, Faq, Products, Answ_faq, User, catgr_files, Topic, Catgr, Batch, prd_cat_faq
from sqlalchemy import select, and_, insert
from app.files import tot_tokens, num_tokens
from handler import prdct_id_nm, topics_f, context_filter_id_f, dic_cat_file_f
from pgpt_python.client import PrivateGPTApi
import pandas as pd
from flask import jsonify
import os, ast
from dotenv import load_dotenv, dotenv_values
load_dotenv()

with app.app_context():
    print(os.getenv("OPENAI_API_KEY"))
    # user_id, topic, prd_id, fileid, = 4, 2, 1, 6
    # lst_cat = [1, 2, 3]
    # file_id = [ef.id for ef in Files.query.filter_by(prdct_id = prd_id).all()]
    # batch_id = [eb.id for eb in Batch.query.filter(Batch.file_id.in_(file_id))]
    # answ_id = [ea.id for ea in Answ_faq.query.filter_by(prdct_id = prd_id).all()]
    # faq_id = [ef.id for ef in Faq.query.filter_by(prdct_id = prd_id).all()]
    # with db.engine.connect() as conn:
    #     cat_faq = list(conn.execute(select(prd_cat_faq).where(prd_cat_faq.c.prd_id == prd_id)))
    #
    # # prd_cat_faq
    #
    # print(file_id)
    # print(batch_id)
    # print(answ_id)
    # print(faq_id)
    # print(cat_faq)





    #print(nh_answ)
# print(topics) [(2, 1, 263, 260), (2, 2, 264, 261), (2, 3, 265, 262)]
#     user_id =4
#     cntxt='context'
#     mess = 'О чем рассказ?'
#     post_fu = Post(body=mess, author=user_id, user_context=cntxt)
#     post_fu = Post(body='О чем рассказ?', author=user_id, user_context=cntxt)
#     #db_topic = Topic(text=mess[:64], user_id=user_id)
#     print('----------')
#
# db.session.add(post_fu)
# db.session.commit()

# print(db_topic)
# print(u.topic.all())
# print(u[0].id)
# posts = Post.query.filter_by(user_id=user_id).order_by(Post.id.desc()).all()
# topics = []
# id_topics = []
# topics_id = {}
# topic_post = {}
# topic_post_id = {}
# for ep in posts:
#     if (ep.topic is not None) and (ep.topic != ''):
#         if ep.topic not in topics:
#             topics.append(ep.topic)
#             id_topics.append([ep.id,ep.topic])
#             topics_id[ep.topic] = ep.id
#             topic_post[ep.topic] = []
#             topic_post_id[ep.id] = []
#         topic_post[ep.topic].append(ep.id)
#         topic_post_id[topics_id[ep.topic]].append(ep.id)


# print(catgr_files.c.cat_id.in_([1,2]))
# print(posts)

# topic = 184
# user_id = 4
# posts = Post.query.filter_by(id=topic).order_by(Post.id).all()
# posts = Post.query.filter_by(user_id=user_id).order_by(Post.id.desc()).all()
#
# posts = Post.query.filter(Post.id.in_(lst_pst)).order_by(Post.id).all()
# user_assistant_content = []
# for ep in posts:
#     user_content = ep.body
#     assistant_content = Post.query.filter_by(reply_id=ep.id).first().body
#     user_assistant_content.append([user_content, assistant_content])

# context_filter_cat=[]
# for ef in Files.query.filter(Files.catgr_files.in_(cat_lst)).all():
#     if ef.id not in context_filter_cat:
#             context_filter_cat.append(ef.id)
# print(cat_lst)
# stmt = select(catgr_files).where(catgr_files.c.cat_id.in_(cat_lst))#.select().limit(1).select
# context_filter_cat=[]
# with db.engine.connect() as conn:
#     for ecf in conn.execute(stmt):
#         if ecf[1] not in context_filter_cat:
#                 context_filter_cat.append(ecf[1])
# print(context_lst[0])
#
# with (app.app_context()):
#     post_id = 182
#     context_str = Post.query.filter_by(id = post_id)[0].user_context
#     context = ast.literal_eval(context_str)
#     context_lst = []
#     for ep in context:
#         context_lst.append([ep[0],Products.query.filter_by(id = ep[0])[0].prdctname])
#         #print(ep[0])
#         file_lst = []
#         for ef in ep[1]:
#             file_lst.append([ef, Files.query.filter_by(filehash = ef)[0].filename])
#             #print(ef)
#         context_lst.append(file_lst)
#
# print(context_lst)
# print(context_lst[0])
#
