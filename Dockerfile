FROM python:3.10.6

WORKDIR /ssc-books

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "flask-books.py" ]