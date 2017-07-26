#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Нужно реализовать простое HTTP API сервиса скоринга. Шаблон уже есть в api.py, тесты в test.py.
# API необычно тем, что польщователи дергают методы POST запросами. Чтобы получить результат
# пользователь отправляет в POST запросе валидный JSON определенного формата на локейшн /method

# Структура json-запроса:

# {"account": "<имя компании партнера>", "login": "<имя пользователя>", "method": "<имя метода>",
#  "token": "<аутентификационный токен>", "arguments": {<словарь с аргументами вызываемого метода>}}

# account - строка, опционально, может быть пустым
# login - строка, обязательно, может быть пустым
# method - строка, обязательно, может быть пустым
# token - строка, обязательно, может быть пустым
# arguments - словарь (объект в терминах json), обязательно, может быть пустым

# Валидация:
# запрос валиден, если валидны все поля по отдельности

# Структура ответа:
# {"code": <числовой код>, "response": {<ответ вызываемого метода>}}
# {"code": <числовой код>, "error": {<сообщение об ошибке>}}

# Аутентификация:
# смотри check_auth в шаблоне. В случае если не пройдена, нужно возвращать
# {"code": 403, "error": "Forbidden"}

# Метод online_score.
# Аргументы:
# phone - строка или число, длиной 11, начинается с 7, опционально, может быть пустым
# email - строка, в которой есть @, опционально, может быть пустым
# first_name - строка, опционально, может быть пустым
# last_name - строка, опционально, может быть пустым
# birthday - дата в формате DD.MM.YYYY, с которой прошло не больше 70 лет, опционально, может быть пустым
# gender - число 0, 1 или 2, опционально, может быть пустым

# Валидация аругементов:
# аргументы валидны, если валидны все поля по отдельности и если присутсвует хоть одна пара
# phone-email, first name-last name, gender-birthday с непустыми значениями.

# Контекст
# в словарь контекста должна прописываться запись  "has" - список полей,
# которые были не пустые для данного запроса

# Ответ:
# в ответ выдается произвольное число, которое больше или равно 0
# {"score": <число>}
# или если запрос пришел от валидного пользователя admin
# {"score": 42}
# или если произошла ошибка валидации
# {"code": 422, "error": "<сообщение о том какое поле невалидно>"}


# $ curl -X POST  -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru", "first_name": "Стансилав", "last_name": "Ступников", "birthday": "01.01.1990", "gender": 1}}' http://127.0.0.1:8080/method/
# -> {"code": 200, "response": {"score": 5.0}}

# Метод clients_interests.
# Аргументы:
# client_ids - массив числе, обязательно, не пустое
# date - дата в формате DD.MM.YYYY, опционально, может быть пустым

# Валидация аругементов:
# аргументы валидны, если валидны все поля по отдельности.

# Контекст
# в словарь контекста должна прописываться запись  "nclients" - количество id'шников,
# переденанных в запрос


# Ответ:
# в ответ выдается словарь <id клиента>:<список интересов>. Список генерировать произвольно.
# {"client_id1": ["interest1", "interest2" ...], "client2": [...] ...}
# или если произошла ошибка валидации
# {"code": 422, "error": "<сообщение о том какое поле невалидно>"}

# $ curl -X POST  -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "admin", "method": "clients_interests", "token": "d3573aff1555cd67dccf21b95fe8c4dc8732f33fd4e32461b7fe6a71d83c947688515e36774c00fb630b039fe2223c991f045f13f24091386050205c324687a0", "arguments": {"client_ids": [1,2,3,4], "date": "20.07.2017"}}' http://127.0.0.1:8080/method/
# -> {"code": 200, "response": {"1": ["books", "hi-tech"], "2": ["pets", "tv"], "3": ["travel", "music"], "4": ["cinema", "geek"]}}

# Требование: в результате в git должно быть только два(2!) файлика: api.py, test.py.
# Deadline: следующее занятие

import abc
import json
import random
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class Field(object):
    def __init__(self, required, nullable=None):
        self._required = required
        self._nullable = nullable

    @property
    def required(self):
        return self._required

    def is_valid(self, value):
        raise Exception("Not Implemented")


class CharField(Field):
    def is_valid(self, value):
        if not self._nullable:
            return bool(value) and isinstance(value, basestring)
        return True


class ArgumentsField(Field):
    def is_valid(self, value):
        if not self._nullable:
            return bool(value)
        return True


class EmailField(CharField):
    def is_valid(self, value):
        r = super(EmailField, self).is_valid(value)
        if value:
            return '@' in value
        return r


class PhoneField(Field):
    def is_valid(self, value):
        if value:
            phone = str(value)
            if len(phone) == 11 and phone.startswith('7'):
                return True
            else:
                return False
        else:
            return self._nullable


class DateField(Field):
    def is_valid(self, value):
        if value:
            try:
                return datetime.datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return False
        else:
            return self._nullable


class BirthDayField(Field):
    DAYS_IN_YEAR = 365
    MAX_AGE = 70
    def is_valid(self, value):
        if value:
            try:
                return ((datetime.datetime.now() -
                         datetime.datetime.strptime(value, '%d.%m.%Y')).days / self.DAYS_IN_YEAR) <= self.MAX_AGE
            except ValueError:
                return False
        else:
            return self._nullable


class GenderField(Field):
    def is_valid(self, value):
        if value:
            try:
                return int(value) in (0, 1, 2)
            except ValueError:
                return False
        else:
            return self._nullable


class ClientIDsField(Field):
    def is_valid(self, value):
        return bool(value)


class StructMeta(type):
    def __new__(cls, name, bases, dct):
        fields = {}
        for k, v in dct.items():
            if isinstance(v, Field):
                fields[k] = v
        dct['_fields'] = fields
        return type.__new__(cls, name, bases, dct)


class Struct(object):
    __metaclass__ = StructMeta

    def __init__(self, values):
        self._values = values

    def process(self):
        pass

    def values_as_object(self):
        class Record:
            pass
        r = Record()
        for f, v in self._values.items():
            setattr(r, f, v)
        return r

    def is_valid(self):
        return not bool(self.errors())

    def errors(self):
        errors = []
        try:
            for f, v in self._fields.items():
                if f not in self._values:
                    if v.required:
                        errors.append('%s not exists' % f)
                else:
                    if not v.is_valid(self._values[f]):
                        errors.append('%s not valid' % f)
        except Exception as E:
            errors.append('Unknown error %s' % E)
        return errors


class ClientsInterestsRequest(Struct):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def process(self):
        if self.is_valid():
            result = {'client_id' + str(c): ['a', 'b']  for c in self._values['client_ids']}
            return OK, result
        else:
            return INVALID_REQUEST, '; '.join(self.errors())


class OnlineScoreRequest(Struct):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def errors(self):
        errors = super(OnlineScoreRequest, self).errors()
        flag_has_pair = False
        for field1, field2 in (('phone', 'email'), ('first_name', 'last_name'), ('gender', 'birthday')):
            if (field1 in self._values and self._values[field1]) and \
               (field2 in self._values and self._values[field2]):
                flag_has_pair = True
                break
        if not flag_has_pair:
            errors.append('Valid fields pairs not found')
        return errors

    def process(self):
        if self.is_valid():
            method_request = MethodRequest(self._values)
            if method_request.is_admin:
                return OK, {'score': 42}
            else:
                return OK, {'score': 8}
        else:
            return INVALID_REQUEST, '; '.join(self.errors())


class MethodRequest(Struct):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    def process(self):
        if self.is_valid():
            return OK, 'OK'
        else:
            return INVALID_REQUEST, '; '.join(self.errors())

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.login == ADMIN_LOGIN:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx):
    REQUESTS = {
        'online_score': OnlineScoreRequest,
        'clients_interests': ClientsInterestsRequest
    }

    method_request = MethodRequest(request['body'])
    code, response = method_request.process()
    if code == 200:
        if not check_auth(method_request.values_as_object()):
            response, code = "Forbidden", 403
        else:
            if method_request.values_as_object().method in REQUESTS:
                code, response = REQUESTS[method_request.values_as_object().method](request['body']['arguments']).process()
            else:
                response, code = ERRORS[NOT_FOUND], NOT_FOUND
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context)
                except Exception, e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return

if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
