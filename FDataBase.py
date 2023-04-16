import sqlite3
import time
import math
from datetime import datetime
from typing import Tuple


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
    
    def __getEventType(self, event_type) -> Tuple[int]:
        """
        Получение id типа события по его названию
        """        
        try:
            self.__cur.execute('SELECT id FROM event_types WHERE event_type = ?', (event_type,))
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка типов событий из БД - {str(err)}')
        return []
    
    def addUser(self, email: str) -> Tuple[bool, int | str]:
        """
        Добавление нового пользователя в БД
        """
        try:
            now_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.__cur.execute("INSERT INTO users(email) VALUES(?)", (email,))
            user_id = self.__cur.lastrowid
            self.__db.commit()
        except sqlite3.Error as err:
            print(f'Ошибка добавления пользователя в БД - {str(err)}')
            return (False, str(err))
        return (True, user_id)
    
    def getUser(self, email: str) -> Tuple[int, int]:
        """
        Получение информации о пользователе по email

        :param email: электронный адрес пользователя
        :return: кортеж с информацией о пользователе (id, принадлежность к администратору(0 или 1))
        """
        sql = "SELECT id, is_admin FROM users WHERE email = ?"
        try:
            self.__cur.execute(sql, (email.lower(),))
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения пользователя из БД - {str(err)}')
        return ()    
    
    def addBook(self, title: str, author: str, year: int, genre_id: int, user_id: int) -> Tuple[bool, int | str]:        
        """
        Добавление новой книги в БД

        :params title: название книги, author: автор, year: год издания, status_id: id статуса (1), user_id: id владельца книги
        :return: кортеж с информацией о добавленной книге (статус добавления(True/False), id книги)
        """
        try: 
            self.__cur.execute("INSERT INTO books(title, author, public_year, genre_id, user_id) VALUES(?, ?, ?, ?, ?)", 
                            (title, author, year, genre_id, user_id))
            book_id = self.__cur.lastrowid
            self.__db.commit()            
        except sqlite3.Error as err:
            print(f'Ошибка добавления книги в БД - {str(err)}')
            return (False, str(err))
        return (True, book_id)
    
    def getBook(self, book_id: int) -> Tuple[str, str, int, str]:
        """
        Получает информацию о книге по ее идентификатору

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
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения книги из БД - {str(err)}')
        return ()
    
    def getAllBooks(self) -> list[Tuple[int, str, str, int, str, str, str]]:
        """
        Получает информацию о полном каталоге книг
        
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
        Получает справочник жанров литературы
        
        :return: список кортежей с информацией жанрах литературы
        (id жанра, название жанра)
        """   
        try:            
            self.__cur.execute("SELECT id, genre FROM book_genres WHERE is_on = 1")
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка жанров из БД - {str(err)}')
        return []
    
    def addFeedback(self, msg: str, user_id: int) -> Tuple[bool, int | str]:        
        """
        Добавление нового сообщения (обратной связи) в БД

        :params msg: текст сообщения от пользователя, user_id: id пользователя
        :return: кортеж с информацией о добавленной записи (статус добавления(True/False), id записи)
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
        Получает информацию о сообщениях пользователей
        
        :return: кортеж с информацией о статусе обращений пользователей
        (id сообщения, текст сообщения, email пользователя, дата обращения, статус обращения)
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
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка меню из БД - {str(err)}')
        return []
    
    def fixEvent(self, event_type: str, object_id: int, user_id: int) -> bool:
        type_id = self.__getEventType(event_type)[0]        
        try:            
            now_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")            
            self.__cur.execute("INSERT INTO events(type_id, object_id, user_id, dt) VALUES(?, ?, ?, ?)", 
                            (type_id, object_id, user_id, now_dt))            
            self.__db.commit()            
        except sqlite3.Error as err:
            print(f'Ошибка добавления события в БД - {str(err)}')
            return False
        return True
