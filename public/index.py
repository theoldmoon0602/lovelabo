from flask import Flask, render_template, request, redirect, url_for,flash, session
import sqlite3
import os
import sys
from hashlib import sha256
import logging


def filepath(path):
    abspath = os.path.abspath(__file__)
    dirname = os.path.dirname(abspath)
    dirname = os.path.dirname(dirname)
    return os.path.join(dirname, path)

def hashed(s):
    return sha256(s.encode()).hexdigest()


app = Flask(__name__)
app.secret_key = 'AAAAAAAAAAAA'
salt = 'AAAAAAAAAAAAA'
database = filepath('database.db')
logfile = filepath('error.log')
logging.basicConfig(filename=logfile, format="%(asctime)s %(message)s")


def connect():
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    db = sqlite3.connect(database)
    db.row_factory = dict_factory
    return db

def update_user(id,rank, first, second, third):
    query = "update users set rank=?, first=?, second=?, third=? where id=?"
    db = connect()
    db.execute(query, (rank, first, second, third, id))
    return db.commit()    

def register_user(username, password, realname, rank, first, second, third):
    query = "insert into users(username, password, realname, rank, first, second, third) values (?,?,?,?,?,?,?)"
    db = connect()
    db.execute(query, (username, hashed(password), realname, rank, first, second, third))
    return db.commit()

def login_user(username, password):
    query = "select id,password from users where username=?;"
    db = connect()
    cur = db.cursor()
    cur.execute(query, (username,))
    r = cur.fetchmany(size=1)[0]
    if r['password'] == hashed(password):
        session['id'] = r['id']
        session['name'] = username
        return True
    return False


def get_labs():
    db = connect()
    r = db.execute('select id,name from labs order by id asc')
    return list(r)


def is_user_login():
    return 'id' in session

def get_login_user_id():
    return session['id']

def get_user(id):
    db = connect()
    db = connect()
    cur = db.cursor()
    cur.execute("select * from users where id = ?",(id,))
    return list(cur.fetchall())[0]

def get_users():
    db = connect()
    cur = db.cursor()
    cur.execute("select * from users order by rank")
    return cur.fetchall()

def get_lab(user_id, lab_id):
    labname = "select name from labs where id=?"
    ranks = "select id from users where first=? or second=? or third=? order by rank"

    db = connect()
    cur = db.cursor()
    cur.execute(labname, (lab_id,))
    name = cur.fetchmany(1)[0]["name"]
    cur.execute(ranks, (lab_id,lab_id,lab_id))
    rank = [v['id'] for v in  cur.fetchall()]
    
    rank = list(rank)
    user_rank = rank.index(user_id)+1
    return {
        'name': name,
        'nums': len(rank),
        'rank': user_rank
    }



@app.route('/user')
def user():
    if not is_user_login():
        return redirect(url_for('index'))
    id = get_login_user_id()
    got = get_user(id)
    first = get_lab(id, got["first"])
    second = get_lab(id, got["second"])
    third = get_lab(id, got["third"])

    users = get_users()
    labs = get_labs()
    for i in range(len(labs)):
        labs[i]["capacity"] = 5
    
    lab=None
    remained = []
    for u in users:
        first_id = u["first"]-1
        if labs[first_id]["capacity"] > 0:
            labs[first_id]["capacity"]-=1
            if u["id"] == id:
                lab = labs[first_id]
                break
            continue
        second_id = u["first"]-1
        if labs[second_id]["capacity"] > 0:
            labs[second_id]["capacity"]-=1
            if u["id"] == id:
                lab = labs[second_id]
                break
            continue
        third_id = u["first"]-1
        if labs[third_id]["capacity"] > 0:
            labs[third_id]["capacity"]-=1
            if u["id"] == id:
                lab = labs[third_id]
                break
            continue
        remained.append(u)

    while lab is None:
        for l in labs:
            if l["capacity"] > 0:
                i += 1
                l["capacity"]-=1
                if remained[i]["id"] == id:
                    lab = l
                    break
            if lab:
                break
    return render_template("user.html", title="研究室配属競争", user=got, first=first, second=second, third=third,lab=lab,labs=labs)

@app.route("/")
@app.route("/index")
def index():
    if is_user_login():
        return redirect(url_for('user'))
    return render_template("index.html", title="研究室配属競争", labs=get_labs())

@app.route('/login', methods=['post'])
def login():
    values = request.form
    params = ['username', 'password']
    if any([p not in values for p in params]):
        flash('なーんかまちがってますね', category='login')
        return redirect(url_for('index'))
    
    try:
        r = login_user(values['username'], values['password'])
        if not r:
            raise Exception("invalid username password")
    except Exception as e:
        logging.error(e)
        logging.error(values)
        flash('ログインしっぱーい', category='login')
        return redirect(url_for('index'))
            
    flash('ログイン成功')
    return redirect(url_for('user'))
    
@app.route('/register', methods=['post'])
def register():
    values = request.form
    params = ['username', 'password', 'realname', 'rank', '1st', '2nd', '3rd']
    if any([p not in values for p in params]):
        flash('なーんかまちがってますね', category='register')        
        return redirect(url_for('index'))
    rank = None
    try:
        rank = int(values['rank'])
        if not (1 <= rank <= 38):
            raise Exception("rank range invalid")
    except Exception as e:
        logging.error(e)
        logging.error(values)
        flash('席次がまちがってますね', category='register')        
        return redirect(url_for('index'))

    choices = []
    try:
        choices.append(int(values['1st']))
        choices.append(int(values['2nd']))
        choices.append(int(values['3rd']))
        labs = get_labs()
        if any([not(1<=v<=len(labs)) for v in choices]):
            raise Exception()
        if len(choices) != len(set(choices)):
            raise Exception()
    except Exception as e:
        logging.error(e)
        logging.error(values)
        flash('配属希望がまちがってますね', category='register')        
        return redirect(url_for('index'))

    try:
        register_user(values['username'], values['password'], values['realname'], rank, choices[0], choices[1], choices[2])
    except Exception as e:
        logging.error(e)
        logging.error(values)
        flash('ユーザ名かぶりとかありそう', category='register')
        return redirect(url_for('index'))

    flash('登録成功')
    return redirect(url_for('index'))

@app.route('/update', methods=['post'])
def update():
    if not is_user_login():
        return redirect(url_for('index'))
    values = request.form
    params = ['rank', '1st', '2nd', '3rd']
    if any([p not in values for p in params]):
        flash('なーんかまちがってますね', category='update')        
        return redirect(url_for('user'))
    rank = None
    try:
        rank = int(values['rank'])
        if not (1 <= rank <= 38):
            raise Exception("rank range invalid")
    except Exception as e:
        logging.error(e)
        logging.error(values)
        flash('席次がまちがってますね', category='update')        
        return redirect(url_for('user'))

    choices = []
    try:
        choices.append(int(values['1st']))
        choices.append(int(values['2nd']))
        choices.append(int(values['3rd']))
        labs = get_labs()
        if any([not(1<=v<=len(labs)) for v in choices]):
            raise Exception()
        if len(choices) != len(set(choices)):
            raise Exception()
    except Exception as e:
        logging.error(e)
        logging.error(values)
        flash('配属希望がまちがってますね', category='update')        
        return redirect(url_for('user'))

    try:
        id = get_login_user_id()
        update_user(id, rank, choices[0], choices[1], choices[2])
    except Exception as e:
        logging.error(e)
        logging.error(values)
        flash('席次かぶりとかユーザ名かぶりとかありそう', category='update')
        return redirect(url_for('userindex'))

    flash('更新成功')
    return redirect(url_for('user'))

if __name__ == '__main__':

    if not os.path.exists(database):
        db = connect()
        db.executescript(open(filepath('schema.sql'), encoding='utf-8').read())
        db.commit()
        db.close()
    app.run(port=8080, debug=True)