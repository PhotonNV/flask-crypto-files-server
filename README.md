# flask-crypto-files-server
## Описание
Тестовый REST-API Flask сервер, позволяющий хранить файлы в MongoDB
в зашифрованном виде. Сервер поддерживает регистрацию пользователей и получение
JSON Web Token (JWT).

### Регистрация нового пользователя
Для регистрации нового пользователя необходимо отправить POST запрос к адресу
/registration содержащий JSON данные New_User_Name и New_User_Password
с именем нового пользователя и паролем соответственно.
Пример запроса через curl
```bash
curl -v -H "Content-Type: application/json" \
-X POST \
--data '{"New_User_Name":"User1", "New_User_Password":"Password"}' \
localhost:5000/registration
```

### Авторизация
Для авторизации ранее созданного пользователя необходимо отправить GET запрос
к адресу /login содержащий JSON данные User_Name и User_Password 
с именем пользователя и паролем соответственно. 
В ответ будет оправлен токен для дальнейшей авторизации
Пример запроса через curl
```bash
curl -v -H "Content-Type: application/json" \
-X GET \
--data '{"User_Name":"User1", "User_Password":"Password"}' \
localhost:5000/login
```

### Использование личного токена
После получения личного токена его необходимо использовать во всех запросах
к авторизированным эндпоинтам. Передавать его необходимо в поле
x-access-tokens:
Для проверки корректности токена реализован тестовый эндпоинт /test_login
Пример запроса через curl
```bash
curl -v -H "x-access-tokens:eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwdWJsaWNfaWQiOiI1NDRjMzBhYy03N2ExLTQ4MmEtYmM2Yi1mZjg1NWMyZjAyZDMiLCJleHAiOjE2MzEzNjQ4MzJ9.GkFnT7fnkVg51DtkEhdyf8n0CFSTy_UN0mCyJxjd8HA" \
-X GET  localhost:5000/test_login
```
В случае корректного токена вы получите сообщение с вашим логином
```
Token is OK, your name: User
```

### Загрузка файла
Загрузка файла на сервер может осуществляться авторизированными пользователями
с актуальным токеном через POST запрос.
Загрузка осуществляется через эндпоинт /load
В ответе будет содержаться уникальный идентификатор файла

```bash
curl -v -H "x-access-tokens:eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwdWJsaWNfaWQiOiI1NDRjMzBhYy03N2ExLTQ4MmEtYmM2Yi1mZjg1NWMyZjAyZDMiLCJleHAiOjE2MzE0MTA3NzF9.o9lBJrjegl534kXse1jtFL6i3Ha-jlR66e-_JrwfLSA" \
-H 'Content-Type: application/octet-stream' \
-X POST --data-binary @/path/to/file  localhost:5000/load
```

### Получение ключа шифрования
Получение ключа шифрования осуществляется через авторизованный GET запрос
к эндпоинту /get_crypto_key/<file_id> где <file_id> это полученный при
загрузке идентификатор файла. В ответ пользователь получит ключ шифрования.
Пользователь может получить ключ шифрования только для своих файлов,
при попытке получения ключа шифрования не своего файла будет получен ответ 404

```bash
curl -v -H "x-access-tokens:eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwdWJsaWNfaWQiOiI1NDRjMzBhYy03N2ExLTQ4MmEtYmM2Yi1mZjg1NWMyZjAyZDMiLCJleHAiOjE2MzE0MTA3NzF9.o9lBJrjegl534kXse1jtFL6i3Ha-jlR66e-_JrwfLSA" \
 -X GET  localhost:5000/get_crypto_key/a13c2e20-cc33-4659-8112-9b484009d29e 
```
### Получение зашифрованного файла
Получение зашифрованного файла осуществляется через авторизованный GET запрос
к эндпоинту /download/<file_id> где <file_id> это полученный при
загрузке идентификатор файла.
```bash
curl -v -O -H "x-access-tokens:eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwdWJsaWNfaWQiOiI1NDRjMzBhYy03N2ExLTQ4MmEtYmM2Yi1mZjg1NWMyZjAyZDMiLCJleHAiOjE2MzE0MTA3NzF9.o9lBJrjegl534kXse1jtFL6i3Ha-jlR66e-_JrwfLSA" \
 -X GET  localhost:5000/download/a13c2e20-cc33-4659-8112-9b484009d29e
```

### Дешифровка файла
Для проверки корректности полученного файла добавлен скрипт позволяющий 
дешифровать полученный файл. Скрипт принимает на вход путь к файлу и ключ.
Пример запуска скрипта:
```bash
python decrypt_file.py /path/to/file/62cf7f28-5c37-4a65-bc07-22de44992788 BRarbG31euS3kRtQ7Cs6Wu-QUWmpvR0kXXylLNTaCoM=
```
Полученный файл будет сохранён с префиксом '_decrypt'