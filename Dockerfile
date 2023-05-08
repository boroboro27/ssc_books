FROM python:3.10.6

# установить каталог для приложения
WORKDIR /ssc-books

# копировать все файлы в контейнер
COPY . .

# установка зависимостей
RUN pip3 install --no-cache-dir -r requirements.txt

# какой порт должен экспоузить контейнер
EXPOSE 8080

# запуск команды
CMD [ "uwsgi", "--ini", "uwsgi.ini"]