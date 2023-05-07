import os
import sqlite3

from flask import (Flask, flash, g, redirect, render_template, request,
                   session, url_for, abort)
from flask_mail import Mail, Message

from FDataBase import FDataBase
import config

application = Flask(__name__)

# конфигурация
application.debug = True
application.config['SECRET_KEY'] = config.SECRET_KEY
application.config['MAIL_SERVER'] = config.MAIL_SERVER
application.config['MAIL_PORT'] = config.MAIL_PORT
# application.config['MAIL_USE_TLS'] =
application.config['MAIL_USE_SSL'] = config.MAIL_USE_SSL
# введите свой адрес электронной почты здесь
application.config['MAIL_USERNAME'] = config.MAIL_USERNAME
# и здесь
application.config['MAIL_DEFAULT_SENDER'] = config.MAIL_DEFAULT_SENDER
application.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD  # введите пароль

mail = Mail(application)

def sendMail(subject, body, users):
    with mail.connect() as conn:
        for user in users:
            msg = Message(recipients=[user],
                        body=body,
                        subject=subject)

            conn.send(msg)

def connect_db():
    """
    Функция для подключения к базе данных.

    Returns:
    conn: объект подключения к базе данных
    """
    db_path = os.path.join(
        '/home/rsb27/python3/ssc-books/ssc-books_db_volume', 'ssc-books.db')
    conn = sqlite3.connect(db_path)
    # Настраиваем, чтобы SQLite3 возвращал объект sqlite3.Row вместо обычного списка или кортежа,
    # потому что он предоставляет удобный способ доступа к данным в строке результата запроса.
    # Объект sqlite3.Row является объектом-контейнером,
    # который позволяет обращаться к элементам строки результата запроса с помощью их имен или индексов.
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    """Соединение с БД, если оно еще не установлено

    Returns:
        g.link_db: _Соединение с БД_
    """
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db

# хэндлер на событие - уничтожение контекста запроса


@application.teardown_appcontext
def close_db(error):
    """Закрываем соединение с БД, если оно было установлено

    Args:
        error: ошибка
    """
    if hasattr(g, 'link_db'):
        # создается дамп БД
        with open("sql_damp.sql", "w") as f:
            for sql in g.link_db.iterdump():
                f.write(sql)
        # закрывается соединение с БД
        g.link_db.close()


@application.route("/", methods=["POST", "GET"])
def index():
    if 'userLogged' in session:
        if request.method == "POST":
            pass
        else:
            db = get_db()
            dbase = FDataBase(db)
            user_id = dbase.getUser(session['userLogged'])
            return render_template('index.html', title='Полка "Книжного перекрестка"',
                                   avl_books=dbase.getAvailableBooks(), 
                                   #False, т.е. не для отображения в ЛК, а для Главной
                                   taken_books=dbase.getTakenBooks(user_id[0], False),
                                   menu=dbase.getMenu(), user=session['userLogged'].split('@')[0])
    else:
        return redirect(url_for('login'))


@application.route("/about")
def about():
    if 'userLogged' in session:
        db = get_db()
        dbase = FDataBase(db)
        return render_template('about.html', title='О проекте "Книжный перекресток"', menu=dbase.getMenu(),
                               user=session['userLogged'].split('@')[0])
    else:
        return redirect(url_for('login'))


@application.route("/add_book", methods=["POST", "GET"])
def add_book():
    db = get_db()
    dbase = FDataBase(db)
    if 'userLogged' in session:
        user_id = dbase.getUser(session['userLogged'])
        if request.method == "POST":
            # title, author, year, status, add_userid
            res = dbase.addBook(request.form["title-book"].strip(),
                                request.form["author-book"].strip(),
                                request.form["genre_id"].strip(),
                                request.form["year-book"].strip(),
                                user_id[0])
            if not res[0]:
                flash(f"Ошибка добавления книги в каталог: {res[1]}. Если не удается устранить ошибку самостоятельно, \n"
                      f"сообщите, пожалуйста, нам об ошибке через форму обратной связи.", category='error')
            else:
                flash((f"Книга успешно добавлена в каталог под номером #{res[1]}. "
                       f"Запишите или вклейте этот номер в книгу на видное место. "
                       f'Теперь можете поставить книгу на полку в зоне обмена "Книжного перекрестка".'), category='success')

        return render_template('add-book.html', title="Регистрация новой книги",
                               menu=dbase.getMenu(), genres=dbase.getGenres(),
                               user=session['userLogged'].split('@')[0])
    else:
        return redirect(url_for('login'))


@application.route('/take_book', methods=["POST"])
def take_book():
    db = get_db()
    dbase = FDataBase(db)
    if 'userLogged' in session:
        user_id = dbase.getUser(session['userLogged'])
        book_code = request.form['book_code'].strip()
        if book_code.isdigit() and len(book_code) == 5:
            res = dbase.takeBook(book_code, user_id[0])
            if not res[0]:
                flash(f"Ошибка при выдаче книги из каталога: {res[1]}. Если не удается устранить ошибку самостоятельно, \n"
                      f"сообщите, пожалуйста, нам об ошибке через форму обратной связи.", category='error')
            else:
                flash((f"Книга под номером #{request.form['book_code'].strip()} успешно выдана из каталога (заведено новых формуляров: {res[1]}). "
                       f'Возьмите, пожалуйста, книгу с полки в зоне обмена "Книжного перекрестка".'), category='success')
        else:
            flash(f"Ошибка при указании кода книги: код должен состоять из 5 цифр. Если не удается устранить ошибку самостоятельно, \n"
                  f"сообщите, пожалуйста, нам об ошибке через форму обратной связи.", category='error')
        return redirect(url_for('lk'))
    else:
        return redirect(url_for('login'))


@application.route('/return_book/<int:book_code>', methods=["GET"])
def return_book_get(book_code):
    db = get_db()
    dbase = FDataBase(db)
    if 'userLogged' in session:
        user_id = dbase.getUser(session['userLogged'])
        res = dbase.returnBook(book_code, user_id[0])
        if not res[0]:
            flash(f"Ошибка при возврате книги в каталог: {res[1]}. Если не удается устранить ошибку самостоятельно, \n"
                  f"сообщите, пожалуйста, нам об ошибке через форму обратной связи.", category='error')
        else:
            flash((f"Книга под номером #{book_code} успешно возвращена в каталог (закрыто формуляров книг: {res[1]}). "
                   f'Верните, пожалуйста, книгу на полку в зоне обмена "Книжного перекрестка".'), category='success')

        return redirect(url_for('lk'))
    else:
        return redirect(url_for('login'))


@application.route('/subscribe_book/<int:book_id>', methods=["GET"])
def subscribe_book(book_id):
    db = get_db()
    dbase = FDataBase(db)
    if 'userLogged' in session:
        user_id = dbase.getUser(session['userLogged'])
        res = dbase.subscribeBook(book_id, user_id[0])
        book = dbase.getBook(book_id)
        if not res[0] or not book:
            flash(f"Ошибка при подписке на книгу: {res[1]}. Если не удается устранить ошибку самостоятельно, \n"
                  f"сообщите, пожалуйста, нам об ошибке через форму обратной связи.", category='error')
        else: 
            msg = (f"Оформлена новая подписка на книгу: {res[1]}. Книга: #{book[0]}, название: '{book[1]}', "
                   f"автор: {book[2]}, год издания: {book[4]}." 
                   f'Теперь мы будем сообщать вам, если книга возвращается на полку в зоне обмена "Книжного перекрестка".')                    
            
            sendMail("Подписка на книгу", msg, users=[session['userLogged']])
            flash((f"Оформлено новых подписок: {res[1]}. Теперь мы будем сообщать вам, если книга возвращается на полку "
                   f'в зоне обмена "Книжного перекрестка".'), category='success')

        return redirect(url_for('lk'))
    else:
        return redirect(url_for('login'))


@application.route('/unsubscribe_book/<int:book_id>', methods=["GET"])
def unsubscribe_book(book_id):
    db = get_db()
    dbase = FDataBase(db)
    if 'userLogged' in session:
        user_id = dbase.getUser(session['userLogged'])
        res = dbase.unsubscribeBook(book_id, user_id[0])
        if not res[0]:
            flash(f"Ошибка при отписке от книги: {res[1]}. Если не удается устранить ошибку самостоятельно, \n"
                  f"сообщите, пожалуйста, нам об ошибке через форму обратной связи.", category='error')
        else:
            flash((f"Подписка на книгу прекращена. Теперь мы НЕ будем сообщать вам, если книга возвращается на полку "
                   f'в зоне обмена "Книжного перекрестка".'), category='success')

        return redirect(url_for('lk'))
    else:
        return redirect(url_for('login'))


@application.route("/rules", methods=["POST", "GET"])
def rules():
    if 'userLogged' in session:
        db = get_db()
        dbase = FDataBase(db)
        return render_template('rules.html', title='Правила проекта "Книжный перекрёсток"',
                               rules=dbase.getRules(),
                               menu=dbase.getMenu(),
                               user=session['userLogged'].split('@')[0])
    else:
        return redirect(url_for('login'))


@application.route("/lk", methods=["POST", "GET"])
def lk():
    if 'userLogged' in session:
        db = get_db()
        dbase = FDataBase(db)
        user_id = dbase.getUser(session['userLogged'])
        return render_template('lk.html', title='Личный кабинет',
                               #True - т.е. для отображения в ЛК, а не на главной
                               taken_books=dbase.getTakenBooks(user_id[0], True), 
                               subscriptions=dbase.getSubscriptions(
                                   user_id[0]),
                               book_log=dbase.getBookLog(user_id[0]),
                               menu=dbase.getMenu(),
                               user=session['userLogged'].split('@')[0], user_id=user_id[0])
    else:
        return redirect(url_for('login'))

# для ввода кода подтверждения отправляй код на почту
# и перенаправляй на спец страницу с формой для ввода полученного кода


@application.route("/login", methods=["POST", "GET"])
def login():
    if 'userLogged' in session:
        return redirect(url_for('index'))
    else:
        db = get_db()
        dbase = FDataBase(db)

        if request.method == 'POST':
            email = request.form['email'].lower().strip()
            is_user = dbase.getUser(email)
            if not is_user:
                res = dbase.addUser(email)
                if res[0] and res[1] > 0:
                    session['userLogged'] = email
                    return redirect(url_for('index'))
                else:
                    flash(f"Ошибка при добавлении пользователя: {res[1]}. \n"
                          f"Если не удается устранить ошибку самостоятельно, сообщите, пожалуйста, о ней через форму обратной связи.",
                          category='error')
            else:
                session['userLogged'] = email
                return redirect(url_for('index'))

        return render_template('login.html', title="Авторизация", menu=dbase.getMenu())


@application.route("/contact", methods=["POST", "GET"])
def contact():
    db = get_db()
    dbase = FDataBase(db)
    if 'userLogged' in session:
        user_id = dbase.getUser(session['userLogged'])
        if request.method == "POST":
            msg = request.form['message'].strip()
            res = dbase.addFeedback(msg, user_id[0])
            if not res[0]:
                flash(
                    f"Ошибка отправки обращения: {res[1]}.", category='error')
            else:
                flash((f"Обращение #{res[1]} принято в работу. "
                       f"Ожидайте ответа на адрес вашей эл. почты {session['userLogged']}"), category='success')

        return render_template('contact.html', title="Обратная связь", menu=dbase.getMenu(),
                               feedbacks=dbase.getAllFeedbacks(), user=session['userLogged'].split('@')[0],
                               is_admin=user_id[1])
    else:
        return redirect(url_for('login'))


@application.route('/close_feedback/<int:fb_id>', methods=["GET"])
def close_feedback(fb_id):
    db = get_db()
    dbase = FDataBase(db)
    if 'userLogged' in session:
        user_id = dbase.getUser(session['userLogged'])
        if user_id[1] != 1:
            return redirect(url_for('contact'))

        res = dbase.closeFeedback(fb_id)
        if not res[0]:
            flash(
                f"Ошибка при закрытии обращения #{fb_id}: {res[1]}.", category='error')
        else:
            flash(
                (f'Обращение #{fb_id} закрыто (закрыто обращений в БД: {res[1]})'), category='success')

        return redirect(url_for('contact'))
    else:
        return redirect(url_for('login'))


@application.route("/exit", methods=["GET"])
def exit():
    session.clear()
    return redirect(url_for('login'))


@application.errorhandler(404)
def page_not_found(error):
    db = get_db()
    dbase = FDataBase(db)
    return render_template('page404.html', title='Страница не найдена', menu=dbase.getMenu()), 404


@application.errorhandler(403)
def forbidden(error):
    db = get_db()
    dbase = FDataBase(db)
    return render_template('page403.html', title='Доступ к информации ограничен, т.к. вы не являетесь администратором ресурса.',
                           menu=dbase.getMenu()), 403


if __name__ == "__main__":
    application.run(host='0.0.0.0')
