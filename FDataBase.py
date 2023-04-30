import sqlite3
import time
import math
from datetime import datetime
from typing import Tuple, Optional


class FDataBase:
    def __init__(self, db: sqlite3.Connection) -> None:
        self.__db = db
        self.__cur = db.cursor()

    def getMenu(self) -> list[Tuple]:
        """
        Получение списка пунктов меню из БД
        """        
        try:
            self.__cur.execute('SELECT * FROM mainmenu')
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка меню из БД - {str(err)}')
        return []
    
    def __getEventType(self, event_type: str) -> Tuple[int]:
        """
        Возвращает id типа события по его названию
        (внутренний метод)

        :param: event_type:  название типа события
        :return: кортеж (id типа события)
        """         
        try:
            self.__cur.execute('SELECT id FROM event_types WHERE event_type = ?', (event_type,))
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка типов событий из БД - {str(err)}')
        return []
    
    def __getBookCode(self, book_id: int) -> Tuple[int]:
        """
        Возвращает код книги по ее идентификатору

        :param book_id: идентификатор книги
        :return: кортеж с информацией о книге (код книги)
        """       
        try:
            # Передаем book_id в метод execute() в виде кортежа
            self.__cur.execute("SELECT code FROM books WHERE id = ? and is_on = 1", (book_id,))
            res = self.__cur.fetchone()
            rows = self.__cur.rowcount
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения книги из БД - {str(err)}')
        return ()
    
    def __getBookId(self, book_code: int) -> Tuple[int]:
        """
        Возвращает идентификатор книги по коду

        :param book_code: код книги
        :return: кортеж с информацией о книге (идентификатор книги)
        """       
        try:
            # Передаем book_code в метод execute() в виде кортежа
            self.__cur.execute("SELECT id FROM books WHERE code = ? and is_on = 1", (book_code,))
            res = self.__cur.fetchone()
            rows = self.__cur.rowcount
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения книги из БД - {str(err)}')
        return ()
    
    
    def addUser(self, email: str, event_id: int) -> Tuple[bool, int | str]:
        """
        Добавляет нового пользователя в БД

        :param: email:  адрес эл. почты, event_id: id события о добавлении нового пользователя
        :return: кортеж (true/false, id нового пользователя | описание ошибки)
        """
        try:            
            self.__cur.execute("INSERT INTO users(email, last_event_id) VALUES(?, ?)", \
                               (email.lower().strip(), event_id))
            user_id = self.__cur.lastrowid
            self.__db.commit()
        except sqlite3.Error as err:
            print(f'Ошибка добавления пользователя в БД - {str(err)}')
            return (False, str(err))
        return (True, user_id)
    
    def getUser(self, email: str) -> Tuple[int, int]:
        """
        Возвращает информацию о пользователе по его email

        :param email: электронный адрес пользователя
        :return: кортеж (id пользователя, принадлежность к администратору(0 | 1))
        """        
        try:
            self.__cur.execute("SELECT id, is_admin FROM users WHERE email = ? AND is_on = 1", (email.lower().strip(),))
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения пользователя из БД - {str(err)}')
        return ()    
    
    def addBook(self, title: str, author: str, genre_id: int, year: int, user_id: int) -> Tuple[bool, int | str]:        
        """
        Добавляет новую книгу в каталог, создаёт пустой новый формуляр, заносит в лог инфо о создании книги

        :params title: название книги, author: автор, genre_id: id жанра, year: год издания, user_id: id владельца книги
        :return: кортеж с информацией о добавленной книге (статус добавления(True/False), код книги)
        """
        try: 
            self.__cur.execute("INSERT INTO books(title, author, genre_id, public_year, owner_id) VALUES(?, ?, ?, ?, ?)", 
                            (title, author, genre_id, year, user_id))
            book_id = self.__cur.lastrowid
            self.__db.commit()
            book_code = self.__getBookCode(book_id)                 

        except sqlite3.Error as err:
            print(f'Ошибка добавления книги в БД - {str(err)}')
            return (False, str(err))
        return (True, book_code['code'])
    
    def takeBook(self, book_code: int, user_id: int) -> Tuple[bool, int | str]:        
        """
        Создаёт пустой новый формуляр с датой выдачи книги = 'сегодня', заносит в лог инфо о выдаче книги

        :params title: user_id: id пользователя, book_code: код книги
        :return: кортеж с информацией о выданной книге (статус добавления(True/False), id формуляра или описание ошибки)
        """
        try: 
            book_id = self.__getBookId(book_code)['id']
            if not book_id:
                return (False, f'В каталоге отсутствует книга с номером {book_code}. Проверьте и введите код еще раз.')
            self.__cur.execute("""
            -- Вставляем новую запись в таблицу forms с полями user_id, book_id и dt_take
            INSERT INTO forms (user_id, book_id, dt_take)
            -- Выбираем значения для вставки
            SELECT :user_id, :book_id, datetime('now', 'localtime')
            -- Проверяем, что в таблице forms нет записей с такими же значениями полей book_id и user_id,
            -- удовлетворяющими условиям dt_take <= datetime('now') и dt_return > datetime('now')
            WHERE NOT EXISTS (
                SELECT 1 FROM forms 
                WHERE (book_id = :book_id AND dt_take <= datetime('now', 'localtime') AND dt_return > datetime('now', 'localtime'))
                OR (user_id = :user_id AND dt_take <= datetime('now', 'localtime') AND dt_return > datetime('now', 'localtime'))
            ) AND EXISTS (
                SELECT 1 FROM books 
                WHERE id = :book_id AND is_on = 1
            );
            """, 
            {'book_id': book_id, 'user_id': user_id})
            form_id = self.__cur.lastrowid
            if form_id == 0:
                return (False, f"либо книга #{book_code} уже выдана (найдите книгу в каталоге и проверьте её статус), "
                               f"либо у вас уже есть на руках другая книга из каталога (проверьте выданные книги в личном кабинете).")
            self.__db.commit()                             

        except sqlite3.Error as err:
            print(f'Ошибка выдачи книги в БД - {str(err)}')
            return (False, str(err))
        return (True, form_id)
    
    def returnBook(self, book_code: int, user_id: int) -> Tuple[bool, int | str]:        
        """
        Закрывает открытый формуляр, проставляя дату возврата книги = 'сегодня', заносит в лог инфо о возврате книги

        :params title: user_id: id пользователя, book_code: код книги
        :return: кортеж с информацией о выданной книге (статус добавления(True/False), колличество возвращенных книг или описание ошибки)
        """
        try: 
            book_id = self.__getBookId(book_code)['id']
            if not book_id:
                return (False, f'В каталоге отсутствует книга с номером {book_code}. Проверьте и введите код еще раз.')
            self.__cur.execute("""
            UPDATE forms 
            SET dt_return = datetime('now', 'localtime')
            WHERE user_id = :user_id 
            AND book_id = :book_id
            AND dt_return > datetime('now', 'localtime')
            AND dt_take <= datetime('now', 'localtime')
            AND dt_new > datetime('now', 'localtime')
            AND dt_delete > datetime('now', 'localtime')
            """, 
            {'book_id': book_id, 'user_id': user_id})

            rows = self.__cur.rowcount
            if rows == 0:
                return (False, f"либо книга #{book_code} на данный момент не выдана (найдите книгу в каталоге и проверьте её статус), "
                               f"либо вам ранее не выдавалась (проверьте выданные книги в личном кабинете).")
            self.__db.commit()                             

        except sqlite3.Error as err:
            print(f'Ошибка выдачи книги в БД - {str(err)}')
            return (False, str(err))
        return (True, rows)
    
    def setStatusBook(self, book_id: int, event_id: int) -> Tuple[bool, str]:        
        """
        Устанавливает статус книги в БД

        :params title: book_id: id книги, event_id: id события, которое сменило статус книги, 
        :return: кортеж (статус смены статуса(True/False), описание ошибки | пустая строка)
        """
        try: 
            self.__cur.execute("UPDATE books SET last_event_id = ? WHERE id = ?", 
                               (event_id, book_id))            
            self.__db.commit()            
        except sqlite3.Error as err:
            print(f'Ошибка смены статуса книги в БД - {str(err)}')
            return (False, str(err))
        return (True, "")
    
    def getBook(self, book_id: int) -> Tuple[str, str, int, str]:
        """
        Возвращает информацию о книге по ее идентификатору

        :param book_id: идентификатор книги
        :return: кортеж с информацией о книге (название, автор, год издания, email пользователя, который добавил книгу)
        """
        # Параметризованный запрос с использованием знака вопроса вместо book_id
        sql = (f"SELECT t1.title, t1.author, t1.year, t2.email \n" 
              f"FROM books as t1 JOIN users as t2 ON t1.user_id = t2.id \n"
              f"WHERE t1.id = ?")
        try:
            # Передаем book_id в метод execute() в виде кортежа
            self.__cur.execute(sql, (book_id,))
            res = self.__cur.fetchone()
            rows = self.__cur.rowcount
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения книги из БД - {str(err)}')
        return ()
    
    
    def getAllBooks(self) -> list[Tuple[int, str, str, int, str, str, str]]:
        """
        Возвращает информацию обо всех книгах в каталоге
        
        :return: кортеж (id книги, название книги, автор книги, год издания, 
        жанр, дата добавления книги в каталог, тип последнего события, связанного с книгой)
        """
        # запрос
        sql = (f"SELECT b.id, b.title, b.author, b.public_year, g.genre, ev.dt, s.status \n" 
              f"FROM books as b \n"
              f"JOIN book_statuses as s ON b.status_id = s.id \n"
              f"JOIN book_genres as g ON b.genre_id = g.id \n"
              f"JOIN (SELECT e.object_id, e.dt \n" 
	          f"FROM events as e \n"
	          f"JOIN event_types as et ON e.type_id = et.id \n"
	          f"WHERE et.event_type LIKE 'add_book') as ev ON b.id = ev.object_id \n"
              f"ORDER BY ev.dt DESC")
        try:            
            self.__cur.execute(sql)
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка книг из БД - {str(err)}')
        return []
    
    def getTakenBooks(self, user_id: Optional[int]) -> list[Tuple[int, str, str, int, str, str, str]]:
        """
        Возвращает информацию о книгах, которые сейчас у пользователя(ей) на руках
        
        :param user_id: id пользователя (опционально)
        :return: кортеж с каталогом книг
        (id книги, название книги, автор книги, год издания, жанр, , 
        дата добавления книги, статус книги)
        """
        # запрос
        sql = (f"SELECT b.id, b.title, b.author, b.public_year, g.genre, ev.dt, s.status \n" 
              f"FROM books as b \n"
              f"JOIN book_statuses as s ON b.status_id = s.id \n"
              f"JOIN book_genres as g ON b.genre_id = g.id \n"
              f"JOIN (SELECT e.object_id, e.dt \n" 
	          f"FROM events as e \n"
	          f"JOIN event_types as et ON e.type_id = et.id \n"
	          f"WHERE et.event_type LIKE 'add_book') as ev ON b.id = ev.object_id \n"
              f"ORDER BY ev.dt DESC")
        try:            
            self.__cur.execute(sql)
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка меню из БД - {str(err)}')
        return []
    
    def getGenres(self) -> list[Tuple[int, str]]:
        """
        Возвращает справочник жанров литературы
        
        :return: список кортежей с информацией о жанрах литературы
        (id жанра, название жанра)
        """   
        try:            
            self.__cur.execute("SELECT id, genre FROM genres WHERE is_on = 1")
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка жанров из БД - {str(err)}')
        return []
    
    def addFeedback(self, msg: str, user_id: int) -> Tuple[bool, int | str]:        
        """
        Добавляет новое обращение пользователя (сообщение об обратной связи) в БД

        :params msg: текст сообщения от пользователя, event_id: id события о регистрации нового обращения в ТП.
        :return: кортеж (статус добавления(True/False), id обращения)
        """
        try:                                
            self.__cur.execute("INSERT INTO feedbacks(msg, user_id) VALUES(?, ?)", 
                            (msg, user_id))
            feedback_id = self.__cur.lastrowid
            self.__db.commit()            
        except sqlite3.Error as err:
            print(f'Ошибка добавления сообщения в БД - {str(err)}')
            return (False, str(err))
        return (True, feedback_id)
    
    def getAllFeedbacks(self) -> list[Tuple[int, str, str, str, str]]:
        """
        Возвращает информацию обо всех обращениях пользователей
        
        :return: кортеж (id обращения, текст сообщения, email пользователя, дата обращения, 
        тип последнего события, связанного с обращением)
        """
        # запрос
        sql = (f"SELECT fb.id, fb.msg, u.email, fb.dt, s.status \n" 
              f"FROM feedbacks as fb \n"
              f"JOIN users as u ON fb.user_id = u.id \n"
              f"JOIN fb_statuses as s ON fb.status_id = s.id \n"
              f"ORDER BY fb.dt DESC")
        
        try:            
            self.__cur.execute(sql)
            res = self.__cur.fetchall()            
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка меню из БД - {str(err)}')
            return ()
        if res: return res


    
