import os
import sqlite3

from flask import (Flask, flash, g, redirect, render_template, request,
                   session, url_for, abort)

from FDataBase import FDataBase, Tuple



# конфигурация
SECRET_KEY = '%%%osfljsflef554454545sfefds^fsdf55'
DEBAG = True

application = Flask(__name__)
application.config.from_object(__name__)

def connect_db():
    """
    Функция для подключения к базе данных.

    Returns:
    conn: объект подключения к базе данных
    """
    db_path = os.path.join('/home/rsb27/python3/ssc-books/ssc-books_db_volume', 'ssc-books.db')
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

#хэндлер на событие - уничтожение контекста запроса
@application.teardown_appcontext
def close_db(error):
    """Закрываем соединение с БД, если оно было установлено

    Args:
        error: ошибка
    """    
    if hasattr(g, 'link_db'):
        #создается дамп БД
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
            return render_template('index.html', title='Каталог "Книжного перекрестка"',
                                   avl_books=dbase.getAvailableBooks(), taken_books=dbase.getTakenBooks(), 
                                   menu=dbase.getMenu(), user=session['userLogged'].split('@')[0])
    else:
        return redirect(url_for('login'))


@application.route("/about")
def about():
    if 'userLogged' in session:
        db = get_db()
        dbase = FDataBase(db)
        return render_template('about.html', title='О проекте "Книжный перекресток"', menu=dbase.getMenu(), \
                               user=session['userLogged'].split('@')[0])
    else:
        return redirect(url_for('login'))

@application.route("/add_book", methods=["POST", "GET"])
def add_book(): 
    db = get_db()
    dbase = FDataBase(db)

    if 'userLogged' in session:
        if request.method == "POST":            
                user_id = dbase.getUser(session['userLogged'])
                #title, author, year, status, add_userid
                res = dbase.addBook(request.form["title-book"].strip(), \
                                    request.form["author-book"].strip(), \
                                    request.form["genre_id"].strip(), \
                                    request.form["year-book"].strip(), \
                                    user_id[0])
                if not res[0]:
                    flash(f"Ошибка добавления книги в каталог: {res[1]}. Если ошибку не удается устранить, \n"
                          f"сообщите, пожалуйста, нам об ошибке через форму обратной связи.", category='error')
                else:                    
                    flash((f"Книга успешно добавлена в каталог под номером #{res[1]}. "
                           f"Запишите или вклейте этот номер в книгу на видное место. "
                           f'Теперь можете поставить книгу на полку в зоне обмена "Книжного перекрестка".'), category='success')
                       
        return render_template('add-book.html', title="Зарегистрировать новую книгу", \
                               menu=dbase.getMenu(), genres=dbase.getGenres(), \
                                user=session['userLogged'].split('@')[0])               
    else:
        return redirect(url_for('login'))
    
@application.route('/take_book', methods=["POST"])
def take_book():
    db = get_db()
    dbase = FDataBase(db)
    if 'userLogged' in session: 
        user_id = dbase.getUser(session['userLogged'])
        res = dbase.takeBook(request.form['book_code'].strip(), user_id[0])
        if not res[0]:
            flash(f"Ошибка при выдаче книги из каталога: {res[1]}. Если ошибку не удается устранить, \n"
                          f"сообщите, пожалуйста, нам об ошибке через форму обратной связи.", category='error')
        else:
            flash((f"Книга под номером #{request.form['book_code'].strip()} успешно выдана из каталога (открыт формуляр #{res[1]}). "                           
                   f'Возьмите книгу с полки в зоне обмена "Книжного перекрестка".'), category='success')        
            
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))
    
@application.route('/return_book', methods=["POST"])
def return_book():
    db = get_db()
    dbase = FDataBase(db)
    if 'userLogged' in session: 
        user_id = dbase.getUser(session['userLogged'])
        res = dbase.returnBook(request.form['book_code'].strip(), user_id[0])
        if not res[0]:
            flash(f"Ошибка при возврате книги в каталог: {res[1]}. Если ошибку не удается устранить, \n"
                          f"сообщите, пожалуйста, нам об ошибке через форму обратной связи.", category='error')
        else:
            flash((f"Книга под номером #{request.form['book_code'].strip()} успешно возвращена в каталог (возвращено книг: {res[1]}). "                           
                   f'Верните книгу на полку в зоне обмена "Книжного перекрестка".'), category='success')        
            
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@application.route("/rules", methods=["POST", "GET"])
def rules():
    abort(404)

@application.route("/lk", methods=["POST", "GET"])
def lk():
    if 'userLogged' in session:
        if request.method == "POST":
            pass
        else:
            db = get_db()
            dbase = FDataBase(db)
            user_id = dbase.getUser(session['userLogged'])
            return render_template('lk.html', title='Личный кабинет',
                                   taken_books=dbase.getTakenBooks(user_id[0]),menu=dbase.getMenu(), \
                                    user=session['userLogged'].split('@')[0])
    else:
        return redirect(url_for('login'))

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
                if not res[0]:
                    flash(f"Ошибка при добавлении пользователя: {res[1]}. \n"
                            f"Если не удается устранить ошибку, сообщите, пожалуйста, о ней через форму обратной связи.", \
                                category='error')   
                else:
                    session['userLogged'] = email 
                    return redirect(url_for('index'))
            else:
                session['userLogged'] = email
                return redirect(url_for('index'))
                    
    return render_template('login.html', title="Авторизация", menu=dbase.getMenu()) 

@application.route("/contact", methods=["POST", "GET"])
def contact():
    db = get_db()
    dbase = FDataBase(db)
    if 'userLogged' in session:
        if request.method == "POST":
            msg = request.form['message'].strip()
            user_id = dbase.getUser(session['userLogged'])
            #title, author, year, status, add_userid
            res = dbase.addFeedback(msg, user_id[0])
            if not res[0]:
                flash(f"Ошибка отправки обращения: {res[1]}.", category='error')
            else:
                flash((f"Обращение #{res[1]} успешно отправлено. "
                       f"Ожидайте ответа на адрес вашей эл. почты {session['userLogged']}"), category='success')  
        
        return render_template('contact.html', title="Обратная связь", menu=dbase.getMenu(), \
                               user=session['userLogged'].split('@')[0])
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
    return render_template('page403.html', title='Доступ к информации ограничен, т.к. вы не являетесь администратором ресурса.', \
                           menu=dbase.getMenu()), 403

if __name__ == "__main__":   application.run(host='0.0.0.0', debug=DEBAG)
    
