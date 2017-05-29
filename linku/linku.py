import os
import base64
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE= os.path.join(app.root_path, 'linku.db'),
    SECRET_KEY= 'development key',
    USERNAME= 'admin',
    PASSWORD= 'admindefault'
    ))
app.config.from_envvar('LINKU_SETTINGS', silent=True)

def connect_db():
    '''Connects to db'''
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    '''Opens new db connection if none exist yet.'''
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    '''closes db at the end of request.'''
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    '''Initialize db.'''
    init_db()
    print('Initialized the database.')

@app.route('/')
def index():
    db = get_db()
    cur = db.execute('select id, link from links order by id asc')
    link_entries = cur.fetchall()
    return render_template('index.html', link_entries=link_entries)

@app.route('/add', methods=['POST'])
def add_link():
    db = get_db()
    cur = db.execute('insert into links (link) values (?)',[request.form['link']])
    db.commit()
    db_id = cur.lastrowid
    
    shorted_url = encodes(db_id).decode()
    domain = url_for('index', _external=True)
    link = domain + '{}'.format(shorted_url)

    flash('link added. visit at {}'.format(link))
    return redirect(url_for('index'))

@app.route('/<link_byte>')
def gotolink(link_byte):
    db=get_db()
    link_id = decodes(link_byte)
    cur = db.execute('select link from links where id=?', (link_id,))
    link = cur.fetchone()
    if link:
        return redirect('http://' + link[0], code=302)
    else:
        abort(404)

def encodes(i):
    s = str(i).encode()
    return base64.urlsafe_b64encode(s)

def decodes(s):
    ss= s.encode()
    i = base64.urlsafe_b64decode(ss)
    return int(i.decode())
