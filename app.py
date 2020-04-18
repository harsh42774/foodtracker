from flask import Flask, render_template, url_for, request, g, redirect
from datetime import datetime
from database import connect_db, get_db

app = Flask(__name__)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/', methods = ['GET', 'POST'])
def index():
    db = get_db()
    if request.method == 'POST':
        date = request.form['date'] #Assuming the date is in YYYY-MM-DD format

        dt = datetime.strptime(date, '%Y-%m-%d')
        database_date = datetime.strftime(dt, '%Y%m%d')

        db.execute('INSERT INTO log_date (entry_date) VALUES (?)', [database_date])
        db.commit()

        return redirect(url_for('view', date=database_date))

    cur = db.execute('''SELECT log_date.entry_Date, sum(food.protein) AS protein, sum(food.carbohydrates) AS carbohydrates, sum(food.fats) AS fats, sum(food.calories) AS calories 
                    FROM log_date
                    LEFT JOIN food_date ON food_date.log_date_id = log_date.id
                    LEFT JOIN food ON food.id = food_date.food_id
                    group by log_date.id ORDER BY log_date.entry_date DESC''')
    results = cur.fetchall()

    date_results  = []

    for i in results:
        single_date = {}

        single_date['entry_date'] = i['entry_date']
        single_date['protein'] = i['protein']
        single_date['carbohydrates'] = i['carbohydrates']
        single_date['fats'] = i['fats']
        single_date['calories'] = i['calories']

        d = datetime.strptime(str(i['entry_date']), '%Y%m%d')
        single_date['pretty_date'] = datetime.strftime(d,'%B %d, %Y')

        date_results.append(single_date)

    return render_template('home.html', results = date_results)

@app.route('/view/<date>', methods = ['GET', 'POST']) #date passed here will be like 20200417
def view(date):
    db = get_db()

    cur = db.execute('SELECT id, entry_date FROM log_date WHERE entry_date = ?', [date])
    date_result = cur.fetchone()

    if request.method == 'POST':
        db.execute('INSERT INTO food_date (food_id, log_date_id) VALUES (?,?)', [request.form['food-select'], date_result['id']])
        db.commit()

    d = datetime.strptime(str(date_result['entry_date']), '%Y%m%d')
    pretty_date = datetime.strftime(d, '%B %d, %Y')

    food_cur = db.execute('SELECT id, name FROM food')
    food_results = food_cur.fetchall()

    log_cur =  db.execute('''SELECT food.name, food.protein, food.carbohydrates, food.fats, food.calories
                            FROM log_date
                            JOIN food_date ON food_date.log_date_id = log_date.id
                            JOIN food ON food.id = food_date.food_id
                            WHERE log_date.entry_date = ?''', [date])
    log_results = log_cur.fetchall()

    totals = {}
    totals['protein'] = 0
    totals['carbohydrates'] = 0
    totals['fats'] = 0
    totals['calories'] = 0

    for food in log_results:
        totals['protein'] += food['protein']
        totals['carbohydrates'] += food['carbohydrates']
        totals['fats'] += food['fats']
        totals['calories'] += food['calories']

    return render_template('day.html', entry_date = date_result['entry_date'], pretty_date = pretty_date, \
                            food_results = food_results, log_results = log_results, totals = totals)

@app.route('/food', methods = ['GET', 'POST'])
def food():
    db = get_db()
    if request.method == 'POST':
        name = request.form['food-name']
        protein = int(request.form['protein'])
        carbohydrates = int(request.form['carbohydrates'])
        fat = int(request.form['fat'])

        calories = protein*4 + carbohydrates*4 + fat*9

        db.execute('INSERT INTO food (name, protein, carbohydrates, fats, calories) VALUES (?, ?, ?, ?, ?)',\
            [name, protein, carbohydrates, fat, calories])
        db.commit()

    cur = db.execute('SELECT name, protein, carbohydrates, fats, calories FROM food')
    results = cur.fetchall()

    return render_template('add_food.html', results = results)

if __name__ == '__main__':
    app.run(debug=True)