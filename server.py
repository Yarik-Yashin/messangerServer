from flask import *
import os
import hashlib
import sqlite3
import datetime

app = Flask(__name__)


@app.route('/login', methods=['GET', 'POST'])
def login():
    password = request.form['password']
    login = request.form['login']

    connection = sqlite3.connect('network_database.db', timeout=10)
    cursor = connection.cursor()
    salt = cursor.execute(f'SELECT salt FROM users WHERE login =="{login}"').fetchone()[0]
    password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                   salt, 20000)
    if password == cursor.execute(f'SELECT password FROM users WHERE login =="{login}"').fetchone()[0]:
        connection.close()
        return 'Ok'
    else:
        connection.close()
        return 'No'


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    password = request.form['password']
    login = request.form['login']
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                              salt, 20000)
    connection = sqlite3.connect('network_database.db', timeout=10)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO users (login, password, salt)"
                   "VALUES (?, ?, ?)", (login, key, salt))
    connection.commit()
    connection.close()
    return 'Ok'


@app.route('/contacts', methods=['POST', 'GET'])
def contacts():
    name = request.form['name']
    connection = sqlite3.connect('network_database.db', timeout=10)
    cursor = connection.cursor()
    query = f"""
                SELECT login FROM users where _id in (SELECT cont.contact_id FROM contacts AS cont
                WHERE cont._id == (SELECT _id FROM users WHERE login =='{name}'))

    """
    contacts_list = cursor.execute(query).fetchall()
    return_dict = dict()
    j = 0
    for i in contacts_list:
        return_dict[str(j)] = i
        j += 1
    connection.close()
    return return_dict


@app.route('/add_contact', methods=['POST', 'GET'])
def add_contact():
    name = request.form['name']
    contact_name = request.form['contact_name']
    connection = sqlite3.connect('network_database.db', timeout=10)
    cursor = connection.cursor()
    cursor.execute(f"""INSERT INTO contacts(_id, contact_id)
    VALUES ((SELECT _id FROM users WHERE login =='{name}'), (SELECT _id FROM users WHERE login =='{contact_name}'))
    """)
    cursor.execute(f"""INSERT INTO contacts(contact_id, _id)
        VALUES ((SELECT _id FROM users WHERE login =='{name}'), (SELECT _id FROM users WHERE login =='{contact_name}'))
        """)
    connection.commit()
    connection.close()
    return 'Ok'


@app.route('/getMessages', methods=['POST', 'GET'])
def getMessages():
    connection = sqlite3.connect('network_database.db', timeout=10)
    cursor = connection.cursor()
    name = request.form['name']
    contact_name = request.form['contact_name']
    messages_list = cursor.execute(
        f"""SELECT * FROM messages WHERE author_id in (SELECT _id FROM users WHERE login in ('{name}', 
                                                                                            '{contact_name}'))
            AND getter_id in (SELECT _id FROM users WHERE login in ('{name}', '{contact_name}'))
""").fetchall()
    j = 0
    return_dict = dict()
    for i in messages_list:
        return_dict[j] = i
        j += 1
    connection.close()
    return return_dict


@app.route('/sendMessage', methods=['POST', 'GET'])
def sendMessage():
    connection = sqlite3.connect('network_database.db', timeout=10)
    cursor = connection.cursor()
    text = request.form['text']
    sender = request.form['login']
    getter = request.form['contact_name']
    date = datetime.datetime.now()
    cursor.execute(f"""INSERT INTO messages(author_id, getter_id, text, datetime)
                    VALUES((SELECT _id FROM users WHERE login=='{sender}'), (SELECT _id FROM users WHERE login=='{getter}'),
                    '{text}', '{date}')""")
    connection.commit()
    connection.close()
    return 'Ok'


@app.route('/getName', methods=['POST', 'GET'])
def getName():
    connection = sqlite3.connect('network_database.db', timeout=10)
    cursor = connection.cursor()
    id = request.form['id']
    name = cursor.execute(f"""SELECT login FROM users WHERE _id == {id}""").fetchone()[0]
    connection.close()
    return name


@app.route('/getImages', methods=['POST'])
def getImages():
    id = request.form['id']
    image = request.files['image']
    name = image.filename
    image.save('profile_images/{0}'.format(name))
    connection = sqlite3.connect('network_database.db', timeout=10)
    cursor = connection.cursor()
    cursor.execute(f"""SET image='profile_images/{name} WHERE id=={id}'""")
    connection.close()
    return 'Ok'


if __name__ == '__main__':
    app.run(debug=True)
