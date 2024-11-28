from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SubmitField,FormField,
                     SelectField, TextAreaField,FieldList)
from wtforms.validators import Length
from flask_wtf.file import FileField
from app import app
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User, Products

class NewFAQ(FlaskForm):
    try:
        with app.app_context():
            products = Products.query.all()# исправить запрос учет прав пользователя
        products_list = [(ep.id, ep.prdctname) for ep in products]
    except:
        products_list = [(0, 'БД не доступна'), (1, 'БД не доступна')]

    df_question = 'Введите вопрос...'
    df_answer = 'Введите ответ...'
    product = SelectField('Выбрать продукт', coerce = int, choices = products_list)
    question = TextAreaField(label='',default=df_question)
    answer = TextAreaField(label='',default=df_answer) #label='Ответ',
    ispublic = BooleanField('Публичный доступ')
    submit_ad = SubmitField('Отправить в FAQ')


class PostForm(FlaskForm):
    post = TextAreaField(label='Вопрос к iFlexGPT', validators=[DataRequired(), Length(min=1, max=62400)])
    submit = SubmitField('Отправить')



class LoginForm(FlaskForm):
    username = StringField('Имя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class CheckboxForm(FlaskForm):
    iscat = BooleanField()

# Основная форма, содержащая список чекбоксов
# class Load_file(FlaskForm):
#     iscats = FieldList(FormField(CheckboxForm), min_entries=3)
#     filetold = FileField(label='Выбрать файл')
#     ispublic = BooleanField('Публичный доступ')
#     submit = SubmitField('Загрузить')


class RegistrationForm(FlaskForm):
    username = StringField('Имя', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField(
        'Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрировать')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Пожалуйста, введите другое имя.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Пожалуйста, введите другой емэйл.')

#users = User.query.all()
class ProductsForm(FlaskForm):
    ##закомментировать этот блок перед flask db init, flask db migrate, flask db upgrade
    try:
        with app.app_context():
            users = User.query.all()
        user_list = [(eu.id, eu.username) for eu in users]
    except:
        user_list = [(0, 'БД не доступна'), (1, 'БД не доступна')]
    ## закомментировать этот блок перед flask db init, flask db migrate, flask db upgrade
    #user_list = [(0,0),(1,1)]
    prdctname = StringField('Название продукта', validators=[DataRequired()])
    manager = SelectField('Менеджер продукта', coerce = int, choices = user_list)

    submit = SubmitField('Зарегистрировать')

    def validate_prdctname(self, prdctname):
        prdct = Products.query.filter_by(prdctname=prdctname.data).first()
        if prdct is not None:
            raise ValidationError('Пожалуйста, введите другое название продукта.')
