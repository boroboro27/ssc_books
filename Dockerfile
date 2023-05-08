FROM ubuntu:22
FROM python:3.10.6

# установить каталог для приложения
WORKDIR /ssc-books

# копировать все файлы в контейнер
COPY . .

# установка зависимостей
RUN pip3 install --no-cache-dir -r requirements.txt

# Установка пакетов tzdata для редактирования часового пояса
RUN apt update && apt install -y tzdata && rm -rf /var/lib/apt/lists/*

# Установка часового пояса Москвы
RUN ln -fs /usr/share/zoneinfo/Europe/Moscow /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

# какой порт должен экспоузить контейнер
EXPOSE 8080

# запуск команды
CMD [ "uwsgi", "--ini", "uwsgi.ini"]