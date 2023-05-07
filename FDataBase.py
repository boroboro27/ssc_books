import sqlite3

from typing import Optional


class FDataBase:
    def __init__(self, db: sqlite3.Connection) -> None:
        self.__db = db
        self.__cur = db.cursor()    
        
    def __getBookCode(self, book_id: int) -> tuple[int] | None:
        """
        Возвращает код книги по ее идентификатору

        :param book_id: идентификатор книги
        :return: кортеж с информацией о книге (код книги) или None
        """       
        try:
            # Передаем book_id в метод execute() в виде кортежа
            self.__cur.execute("SELECT code FROM books WHERE id = ? and is_on = 1", (book_id,))
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения книги из БД - {str(err)}')
        return ()
    
    def __getBookId(self, book_code: int) -> tuple[int]:
        """
        Возвращает идентификатор книги по коду

        :param book_code: код книги
        :return: кортеж с информацией о книге (идентификатор книги) или None
        """       
        try:
            # Передаем book_code в метод execute() в виде кортежа
            self.__cur.execute("SELECT id FROM books WHERE code = ? and is_on = 1", (book_code,))
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения книги из БД - {str(err)}')
        return ()
    
    def getMenu(self) -> list[tuple[str]]:
        """
        Получение списка пунктов меню из БД

        :return: список кортежей с пунктами главноего меню или пустой список
        """        
        try:
            self.__cur.execute('SELECT * FROM mainmenu')
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка меню из БД - {str(err)}')
        return []       
    
    def addUser(self, email: str) -> tuple[bool, int | str]:
        """
        Добавляет нового пользователя в БД

        :param: email:  адрес эл. почты
        :return: кортеж (true/false, кол-во добавленных строк или описание ошибки)
        """
        try:            
            self.__cur.execute("INSERT INTO users(email) VALUES(?)", \
                               (email,))
            rows = self.__cur.rowcount
            self.__db.commit()
        except sqlite3.Error as err:
            print(f'Ошибка при добавлении пользователя в БД - {str(err)}')
            return (False, str(err))
        return (True, rows)
    
    def getUser(self, email: str) -> tuple[int, int]:
        """
        Возвращает информацию о пользователе по его email

        :param: email: электронный адрес пользователя
        :return: кортеж (id пользователя, принадлежность к администратору(0 | 1))
        """        
        try:
            self.__cur.execute("SELECT id, is_admin FROM users WHERE email = ? AND is_on = 1", (email,))
            res = self.__cur.fetchone()
            if res: return res            
        except sqlite3.Error as err:
            print(f'Ошибка получения id пользователя из БД - {str(err)}')
        return ()    
    
    def addBook(self, title: str, author: str, genre_id: int, year: int, user_id: int) -> tuple[bool, int | str]:        
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
            if book_code: return (True, book_code['code'])  
        except sqlite3.Error as err:
            print(f'Ошибка добавления книги в БД - {str(err)}')            
        return (False, str(err))
    
    def takeBook(self, book_code: int, user_id: int) -> tuple[bool, int | str]:        
        """
        Создаёт пустой новый формуляр с датой выдачи книги = 'сегодня', заносит в лог инфо о выдаче книги

        :params title: user_id: id пользователя, book_code: код книги
        :return: кортеж с информацией о выданной книге (статус добавления(True/False), id формуляра или описание ошибки)
        """
        try: 
            book_id = self.__getBookId(book_code)
            if not book_id:
                return (False, f'В каталоге отсутствует книга с номером {book_code}. Проверьте и введите код еще раз.')            
            else: 
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
                {'book_id': book_id['id'], 'user_id': user_id})
                rows = self.__cur.rowcount
                if rows <= 0:
                    return (False, f"либо книга #{book_code} уже на руках у кото-то (найдите книгу в каталоге и проверьте её статус), "
                                f"либо у вас уже есть другая книга, и вы пока её не вернули (проверьте выданные книги в личном кабинете).")
                self.__db.commit() 
        except sqlite3.Error as err:
            print(f'Ошибка выдачи книги в БД - {str(err)}')
            return (False, str(err))
        return (True, rows)
    
    def returnBook(self, book_code: int, user_id: int) -> tuple[bool, int | str]:        
        """
        Закрывает открытый формуляр, проставляя дату возврата книги = 'сегодня', заносит в лог инфо о возврате книги

        :params title: user_id: id пользователя, book_code: код книги
        :return: кортеж с информацией о выданной книге (статус добавления(True/False), колличество возвращенных книг или описание ошибки)
        """
        try: 
            book_id = self.__getBookId(book_code)
            if not book_id:
                return (False, f'В каталоге отсутствует книга с номером {book_code}. Проверьте и введите код еще раз.')
            else:
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
                {'book_id': book_id['id'], 'user_id': user_id})

                rows = self.__cur.rowcount
                if rows <= 0:
                    return (False, f"либо книга #{book_code} не выдавалась (найдите книгу в каталоге и проверьте её статус), "
                                   f"либо выдавалась, но не ваше имя (проверьте выданные книги в личном кабинете).")
                self.__db.commit()                             

        except sqlite3.Error as err:
            print(f'Ошибка выдачи книги в БД - {str(err)}')
            return (False, str(err))
        return (True, rows)    
    
    def subscribeBook(self, book_id: int, user_id: int) -> tuple[bool, int | str]:        
        """
        Оформляет подписку на книгу, заносит в лог инфо о подписке на книгу

        :params title: user_id: id пользователя, book_id: id книги
        :return: кортеж с информацией о подписке на книгу (статус добавления(True/False), )
        """
        try:            
            
            self.__cur.execute("""
            -- Вставляем новую запись в таблицу subscriptions с полями user_id, book_id
            INSERT INTO subscriptions (user_id, book_id)
            -- Выбираем значения для вставки
            SELECT :user_id, :book_id
            -- Проверяем, что в таблице subscriptions нет записей с такими же значениями полей book_id и user_id,
            -- удовлетворяющими условиям dt_take <= datetime('now') и dt_return > datetime('now')
            WHERE NOT EXISTS (
                SELECT 1 FROM subscriptions 
                WHERE book_id = :book_id AND user_id = :user_id AND dt_new <= datetime('now', 'localtime') AND dt_delete > datetime('now', 'localtime')               
            ) 
            -- Проверяем, что в таблице forms есть записи с такими же значениями полей book_id и эта книга выдана, но не подписчику
            AND EXISTS (
                SELECT 1 FROM forms 
                WHERE book_id = :book_id AND dt_take <= datetime('now', 'localtime') AND dt_return > datetime('now', 'localtime')
                AND user_id != :user_id                                    
            )
            -- Проверяем, что в таблице books есть записи с такими же значениями полей book_id и книга активна
            AND EXISTS (
                SELECT 1 FROM books 
                WHERE id = :book_id AND is_on = 1)
            """, 
            {'book_id': book_id, 'user_id': user_id})

            rows = self.__cur.rowcount
            if rows <= 0:
                return (False, f"вы уже подписаны на эту книгу (проверьте ваши подписки в личном кабинете).")
            self.__db.commit()                             

        except sqlite3.Error as err:
            print(f'Ошибка при подписке на книгу в БД - {str(err)}')
            return (False, str(err))
        return (True, rows)

    def unsubscribeBook(self, book_id: int, user_id: int) -> tuple[bool, int | str]:        
        """
        Прекращает подписку на книгу, заносит в лог инфо о завершении подписки на книгу

        :params title: user_id: id пользователя, book_id: id книги
        :return: кортеж с информацией о подписке на книгу (статус добавления(True/False))
        """
        try:            
            
            self.__cur.execute("""
            UPDATE subscriptions 
            SET dt_delete = datetime('now', 'localtime')
            WHERE user_id = :user_id 
            AND book_id = :book_id
            AND dt_new <= datetime('now', 'localtime')  
            AND dt_delete > datetime('now', 'localtime')  
            """, 
            {'book_id': book_id, 'user_id': user_id})

            rows = self.__cur.rowcount
            if rows <= 0:
                return (False, f"вы еще не подписаны на эту книгу (проверьте подписки в личном кабинете).")
            self.__db.commit()                             

        except sqlite3.Error as err:
            print(f'Ошибка отписки на книгу в БД - {str(err)}')
            return (False, str(err))
        return (True, rows)   

    def getSubscriptions(self, user_id: Optional[int] = 0) -> list[tuple[int, int, str, str, int, int, str, str, str]]:
        """
        Возвращает информацию о подписках, которые есть у пользователя(ей)
        
        :param user_id: id пользователя (опционально)
        :return: кортеж (код книги, id книги, название книги, автор книги, год издания, 
        id пользователя(оформившего подписку), имя пользователя, 
        дата и время начала подписки книги, 
        дата и время срока подписки
        """
    
        try: 
            if user_id:           
                self.__cur.execute('SELECT * FROM vw_open_subs_wide WHERE user_id = ?', (user_id,))
            else:
                self.__cur.execute('SELECT * FROM vw_open_subs_wide')
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения оформленных подписок из БД - {str(err)}')
        return []      

    def getRules(self) -> list[tuple[int, str]]:
        """
        Возвращает список правил проекта      
        
        :return: кортеж (id правила, описание правила)
        """    
        try: 
            self.__cur.execute('SELECT * FROM rules WHERE is_on = 1')
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтении свода правил проекта из БД - {str(err)}')
        return []  
    
    
    def getBook(self, book_id: int) -> tuple[int, str, str, str, int]:
        """
        Возвращает информацию о книге по ее идентификатору

        :param book_id: идентификатор книги
        :return: кортеж с информацией о книге (код, название, автор, жанр, год издания)
        """
        # Параметризованный запрос с использованием знака вопроса вместо book_id
        sql = (f"SELECT t1.code, t1.title, t1.author, g.genre, t1.public_year \n" 
              f"FROM books as t1 JOIN genres as g ON t1.genre_id = g.id \n"
              f"WHERE t1.id = ?")
        try:
            # Передаем book_id в метод execute() в виде кортежа
            self.__cur.execute(sql, (book_id,))
            res = self.__cur.fetchone()            
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения книги из БД - {str(err)}')
        return ()
    
    
    def getAvailableBooks(self) -> list[tuple[int, str, str, str, int, str, str]]:
        """
        Возвращает информацию обо всех доступных к выдаче книгах в каталоге
        
        :return: кортеж (код книги, название книги, автор книги, жанр, год издания, 
        владелец книги, дата и время добавления книги в каталог)
        """
        
        try:            
            self.__cur.execute('SELECT * FROM vw_available_books')
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка доступных книг из БД - {str(err)}')
        return []
    
    def getTakenBooks(self, user_id: int, for_lk: bool) -> list[tuple[int, int, str, str, str, int, int, str, str, str]]:
        """
        Возвращает информацию о книгах, которые сейчас у пользователя(ей) на руках
        
        :param user_id: id пользователя, for_lk: указатель(true/false) о том, что запрос делается для отображения в ЛК или нет
        :return: кортеж (код книги, id книги, название книги, автор книги, жанр, год издания, 
        id пользователя(взявшего книгу), имя пользователя, дата и время выдачи книги, дата и время срока возврата
        """
    
        try: 
            if for_lk:           
                self.__cur.execute('SELECT * FROM vw_taken_books WHERE user_id = ?', (user_id,))
            else:
                self.__cur.execute("""
                SELECT tb.*, 
                    CASE WHEN s.subs_book_id IS NULL THEN 0
                    ELSE 1
                    END AS subs_status
                FROM vw_taken_books as tb
                LEFT JOIN vw_open_subs_trim as s ON tb.book_id = s.subs_book_id
                AND s.subs_user_id = :user_id
                """, {'user_id': user_id})
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка выданных книг из БД - {str(err)}')
        return []
    
    def getBookLog(self, user_id: Optional[int] = 0) -> list[tuple[int, int, str, str, int, int, str, str, str]]:
        """
        Возвращает информацию о всех действиях пользователя(ей) с книгами
        
        :param user_id: id пользователя (опционально)
        :return: кортеж (код книги, id книги, название книги, автор книги, год издания, 
        id пользователя, имя пользователя, тип операции, дата и время операции
        """
    
        try: 
            if user_id:           
                self.__cur.execute('SELECT * FROM vw_book_log WHERE user_id = ?', (user_id,))
            else:
                self.__cur.execute('SELECT * FROM vw_book_log')
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка операций(лога) из БД - {str(err)}')
        return []
    
    def getGenres(self) -> list[tuple[int, str]]:
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
    
    def addFeedback(self, msg: str, user_id: int) -> tuple[bool, int | str]:        
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
            print(f'Ошибка при добавлении обращения ТП в БД - {str(err)}')
            return (False, str(err))
        return (True, feedback_id)
    
    def closeFeedback(self, fb_id: int) -> tuple[bool, int | str]:        
        """
        Закрывает обращение пользователя в ТП

        :params title: user_id: id пользователя, fb_id: id обращения
        :return: кортеж с информацией о смене статуса по обращению (статус изменения(True/False), 
        кол-во закрытых обращений)
        """
        try:            
            
            self.__cur.execute("""
            UPDATE feedbacks 
            SET dt_delete = datetime('now', 'localtime')
            WHERE id = :fb_id
            AND dt_new <= datetime('now', 'localtime')  
            AND dt_delete > datetime('now', 'localtime')    
            """, 
            {'fb_id': fb_id})

            rows = self.__cur.rowcount
            if rows <= 0:
                return (False, f"отсутствует обращение с таким id или оно уже закрыто")
            self.__db.commit()                             

        except sqlite3.Error as err:
            print(f'Ошибка при закрытии обращения пользователя в БД - {str(err)}')
            return (False, str(err))
        return (True, rows) 
    
    def getAllFeedbacks(self) -> list[tuple[int, str, str, str, str]]:
        """
        Возвращает информацию обо всех обращениях пользователей
        
        :return: кортеж (id обращения, текст сообщения, email пользователя, дата обращения, 
        тип последнего события, связанного с обращением)
        """        
        try:            
            self.__cur.execute('SELECT * FROM vw_feedbacks')
            res = self.__cur.fetchall() 
            if res: return res           
        except sqlite3.Error as err:
            print(f'Ошибка чтения списка меню из БД - {str(err)}')            
        return []


    
