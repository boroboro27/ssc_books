FROM ubuntu:22.04
FROM python:3.10.6

LABEL author="ruslan.borodin"
LABEL version="1.0.2"
LABEL type="prod."

# установить каталог для приложения
WORKDIR /ssc-books

# копировать все файлы в контейнер
COPY ./conf/* .
COPY ./static/* .
COPY ./templates/* .
COPY ./uwsgi/* .
COPY ./FDataBase.py .
COPY ./flask-books.py .
COPY ./requirements.txt .
COPY ./uwsgi.ini .

# установка зависимостей
RUN pip3 install --no-cache-dir -r requirements.txt

# Установка пакетов tzdata для редактирования часового пояса
RUN apt-get update && apt-get -y install tzdata && rm -rf /var/lib/apt/lists/* 
RUN apt-get update && apt-get -y install sqlite3 && apt-get -y install nano

# Установка часового пояса Москвы
RUN ln -fs /usr/share/zoneinfo/Europe/Moscow /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

# какой порт должен экспоузить контейнер
EXPOSE 8080
EXPOSE 8081

# запуск команды
CMD [ "uwsgi", "--ini", "uwsgi.ini"]