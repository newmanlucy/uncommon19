from flask import Flask, jsonify, request, render_template, redirect, g, session, copy_current_request_context
from argparse import ArgumentParser
import threading
import requests
import logging
import ast
import json
from datetime import datetime
from time import mktime
import sqlite3
from threading import Timer
import sol_bets

# Instantiate our Node
app = Flask(__name__)
app.secret_key = b'1234567890'

weather_secret = "26a6ea3b1dbe501627ed1371db89558a"

######################### SENDING TO CONTRACT #################################

abi, contract_address = sol_bets.read_contract('data.json')

def send_new_bet(bet_id, temp, amount, creator_id):
    user_id = get_user_id(creator_id)
    sol_bets.sol_create_bet(bet_id, user_id, temp, amount, abi, contract_address)

def send_take_bet(bet_id, taker_id):
    user_id = get_user_id(taker_id)
    sol_bets.sol_take_bet(int(bet_id), user_id, abi, contract_address)

def send_end_bet(bet_id, second_arg):
    current_time = int(mktime(datetime.now().timetuple()))
    temp = get_weather(current_time)
    sol_bets.sol_reward_winner(bet_id, temp, abi, contract_address)

######################## WEATHER DATA FUNCTIONS ###########################

def get_weather(date):
    url = "https://api.darksky.net/forecast/%s/41.8781,-87.6290,%d" % (weather_secret, date)
    r = requests.get(url)
    if r.status_code == 200:
        j = r.json()
        temp = j['currently']['temperature']
        return float(temp)

######################### DATABASE FUNCTIONS #############################

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_user_id(username):
    conn = sqlite3.connect("weather_betting.db")
    c = conn.cursor()
    q = "SELECT * FROM users WHERE username='%s'" % username
    c.execute(q)
    conn.commit()
    conn.close()
    return c.lastrowid

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect("weather_betting.db")
        g.db.row_factory = dict_factory
    return g.db

def add_user_if_not_there(user):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username='%s'" % user)
    if c.fetchone() is None:
        c.execute("INSERT INTO users (username) VALUES ('%s')" % user) 
    conn.commit()
    conn.close()

def add_bet(user, atleast, dt_obj, amount):
    conn = get_db()
    c = conn.cursor()
    q = """
        INSERT INTO bets 
            (atleast, date, amount, creator_id)
        VALUES
            (%d, '%s', %d, '%s')
        """ % (atleast, str(dt_obj), amount, user)
    c.execute(q)
    conn.commit()
    conn.close()
    return c.lastrowid

def get_bets_for_user(user_id):
    conn = get_db()
    c = conn.cursor()
    q1 = "SELECT * FROM bets WHERE creator_id='%s'" % user_id
    c.execute(q1)
    my_created = c.fetchall()
    q2 = "SELECT * FROM bets WHERE taker_id='%s'" % user_id
    c.execute(q2)
    my_taken = c.fetchall()
    conn.commit()
    conn.close()
    return my_created, my_taken

def get_open_bets():
    conn = get_db()
    c = conn.cursor()
    q = "SELECT * FROM bets WHERE taker_id IS NULL"
    c.execute(q)
    open_bets= c.fetchall()
    conn.commit()
    conn.close()
    return open_bets

def get_bet(bet_id):
    conn = get_db()
    c = conn.cursor()
    q = "SELECT * FROM bets WHERE id=%s" % bet_id
    c.execute(q)
    bet = c.fetchone()
    conn.commit()
    conn.close()
    return bet

def take_bet(user_id, bet_id):
    conn = sqlite3.connect('weather_betting.db')
    c = conn.cursor()
    q = "UPDATE bets SET taker_id='%s' WHERE id=%s" % (user_id, bet_id)
    c.execute(q)
    conn.commit()
    conn.close()

def get_winners_and_losers(date, temp):
    conn = get_db()
    c = conn.cursor()
    q = "SELECT * FROM bets"# WHERE date=%s AND taker_id IS NOT NULL" % date
    c.execute(q)
    res = c.fetchall()
    conn.commit()
    conn.close()
    results = []
    for r in res:
        if r["date"] == date and r["taker_id"] is not None:            
            if r['atleast'] <= temp:
                r.update({"winner": r["creator_id"], "loser": r["taker_id"], "word": "over"})
            else:
                r.update({"loser": r["creator_id"], "winner": r["taker_id"], "word": "less than"})
            results.append(r)
    return results

# datetime.strptime(str(dt),'%Y-%m-%d %H:%M:%S.%f')
############################## FLASK FUNCTIONS ############################

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "GET":
        return render_template('index.html')
    elif request.method == "POST":
        user = request.form.get("username")
        # Just add the user if it's not in there
        add_user_if_not_there(user)
        # save user to global object
        session['username'] = user
        # Redirect to this user's mybets pate
        # TODO: validate user
        return redirect("/mybets/"+user)

@app.route('/newbet', methods=['GET', 'POST'])
def newbet():
    if request.method == "GET":
        return render_template('newbet.html')
    elif request.method == "POST":
        date = request.form.get("date")
        atleast = int(request.form.get("atleast"))
        amount = int(request.form.get("amount"))
        dt_obj = datetime.strptime(date, '%Y-%m-%d')
        if dt_obj < datetime.now():
            return render_template("failure.html", message="Bet must be in the future!")
        if int(amount) < 0:
            return render_template("failure.html", message="Bet must have a positive amount!")
        bet_id = add_bet(session['username'], atleast, date, amount)
        send_new_bet(bet_id, atleast, amount, session['username'])
        return render_template("added.html", message="Your bet has been added.")

@app.route('/mybets/<user_id>')
def mybets(user_id):
    my_created, my_taken = get_bets_for_user(user_id)
    return render_template('mybets.html', my_created=my_created, my_taken=my_taken, user_id=user_id)

@app.route('/bets')
def bets():
    open_bets = get_open_bets()
    return render_template('bets.html', open_bets=open_bets)

@app.route('/openbet/<bet_id>', methods=["GET", "POST"])
def openbet(bet_id):
    if request.method == "GET":
        bet = get_bet(bet_id)
        return render_template('openbet.html', open_bet=bet)
    elif request.method == "POST":
        bet = get_bet(bet_id)
        take_bet(session['username'], bet_id)
        @copy_current_request_context
        def set_send_event(bet):
            dt = datetime.strptime(bet['date'], '%Y-%m-%d')
            time_diff = int((dt - datetime.now()).total_seconds())
            Timer(1, send_end_bet, (bet_id, 3)).start()
        send_take_bet(bet_id, session["username"])
        set_send_event(bet)
        return render_template("added.html", message="You have taken the bet!")

@app.route('/winners', methods=["GET"])
def get_winners():
    date = request.args.get("date")
    if date is None:
        date = str(datetime.now().date())
    temp = None
    results = None
    message = None
    if date:
        unix_time = int(mktime(datetime.strptime(date, "%Y-%m-%d").timetuple()))
        if unix_time > int(mktime(datetime.now().timetuple())):
            message = "Choose a time in the past"
        else:
            temp = get_weather(unix_time)
            results = get_winners_and_losers(date, temp)
    return render_template("winners.html", date=date, temp=temp, results=results, message=message)

if __name__ == '__main__':
    app.run(host='0.0.0.0')#, port=int(args.address.split(":")[2]), debug=True)
