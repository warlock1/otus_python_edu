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


class ValidationError(ValueError):
    pass


class Field(object):
    ASSERTS_LIST = (lambda v: True, )
    ERROR_TEXT = 'value is not valid'

    def __init__(self, required, nullable=False):
        self._required = required
        self._nullable = nullable

    @property
    def required(self):
        return self._required

    @property
    def nullable(self):
        return self._nullable

    def _get_value(self, value):
        return value

    def _has_value(self, value):
        return bool(value)

    def parse(self, value):
        v = self._get_value(value)
        if self._has_value(v):
            if not any(a(v) for a in self.ASSERTS_LIST):
                raise ValidationError(self.ERROR_TEXT)
        else:
            if not self.nullable:
                raise ValidationError(self.ERROR_TEXT)
        return v


class CharField(Field):
    ERROR_TEXT = 'value is not Charfield'
    ASSERTS_LIST = (lambda v: isinstance(v, basestring), )


class ArgumentsField(Field):
    ERROR_TEXT = 'value is not ArgumentsField'
    ASSERTS_LIST = (lambda v: isinstance(v, dict), )


class EmailField(CharField):
    ERROR_TEXT = 'value is not EmailField'
    ASSERTS_LIST = (lambda v: '@' in v, )

    def parse(self, value):
        v = CharField(self.required, self.nullable).parse(value)
        return super(CharField, self).parse(v)


class PhoneField(Field):
    ERROR_TEXT = 'value is not PhoneField'
    ASSERTS_LIST = (lambda v: len(v) == 11 and v.startswith('7') and all(c.isdigit() for c in v), )

    def _get_value(self, value):
        return unicode(value)


class DateField(Field):
    ERROR_TEXT = 'value is not DateField'

    def _get_value(self, value):
        try:
            return datetime.datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            raise ValidationError(self.ERROR_TEXT)


class BirthDayField(DateField):
    DAYS_IN_YEAR = 365
    MAX_AGE = 70

    ERROR_TEXT = 'value is not BirthDayField'
    ASSERTS_LIST = (lambda v: (((datetime.datetime.now() - v).days / BirthDayField.DAYS_IN_YEAR) <= BirthDayField.MAX_AGE), )

    def parse(self, value):
        DateField(self.required, self.nullable).parse(value)
        return super(DateField, self).parse(value)


class GenderField(Field):
    ERROR_TEXT = 'value is not GenderField'
    ASSERTS_LIST = (lambda v: isinstance(v, int) and v in GENDERS, )

    def _has_value(self, value):
        return bool(value) or (value == 0)


class ClientIDsField(Field):
    ERROR_TEXT = 'value is not ClientIDsField'
    ASSERTS_LIST = (lambda v: isinstance(v, list) and all(isinstance(e, int) for e in v), )


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
        self._errors = []

    def is_valid(self):
        self.check()
        return not self._errors

    def get_errors(self):
        return '; '.join(self._errors)

    def check(self):
        self.errors = []
        try:
            for f, v in self._fields.items():
                if f not in self._values:
                    if v.required:
                        self._errors.append('%s not exists' % f)
                else:
                    try:
                        _v = v.parse(self._values[f])
                        setattr(self, f, _v)
                    except ValidationError as E:
                        self._errors.append('%s has error %s' % (f, E))
        except Exception as E:
            self._errors.append('Unknown error %s' % E)

    def _field_has_value(self, field):
        if field in self._values:
            return self._fields[field]._has_value(self._values[field])
        return False


class ClientsInterestsRequest(Struct):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(Struct):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def check(self):
        super(OnlineScoreRequest, self).check()
        flag_has_pair = False
        for field1, field2 in (('phone', 'email'), ('first_name', 'last_name'), ('gender', 'birthday')):
            if self._field_has_value(field1) and self._field_has_value(field2):
                flag_has_pair = True
                break
        if not flag_has_pair:
            self._errors.append('Valid fields pairs not found')


class MethodRequest(Struct):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=True)

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


def online_score_proc(request_type, args, method_request, context):
    req_obj = request_type(args)
    if req_obj.is_valid():
        context['has'] = [f for f in req_obj._values if req_obj._field_has_value(f)]
        result = {}
        if method_request.is_admin:
            result['score'] = 42
        else:
            result['score'] = 8
        return result, OK
    return req_obj.get_errors(), INVALID_REQUEST


def clients_interests_proc(request_type, args, method_request, context):
    req_obj = request_type(args)
    if req_obj.is_valid():
        context['nclients'] = len(req_obj.client_ids)
        result = {'client_id' + str(c): ['a', 'b'] for c in req_obj.client_ids}
        return result, OK
    return req_obj.get_errors(), INVALID_REQUEST


def method_handler(request, ctx):
    METHODS = {
        'online_score': (online_score_proc, OnlineScoreRequest),
        'clients_interests': (clients_interests_proc, ClientsInterestsRequest),
    }

    method_request = MethodRequest(request['body'])
    if not method_request.is_valid():
        return method_request.get_errors(), INVALID_REQUEST
    if not check_auth(method_request):
        return None, FORBIDDEN
    method_proc = METHODS.get(method_request.method)
    if not method_proc:
        return 'Method proc not found', NOT_FOUND
    response, code = method_proc[0](method_proc[1], request['body']['arguments'], method_request, ctx)
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
