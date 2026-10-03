import sqlite3
import webbrowser
from threading import Timer
from flask import Flask, render_template_string, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = 'assem_ultimate_secret_key'

# 1. إعداد قاعدة البيانات المحدثة لتشمل الأسعار والفواتير
def init_db():
    conn = sqlite3.connect('secret_restaurant_v3.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY, password TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, meal TEXT, price INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 2. تصميم الواجهات البرمجية (HTML) مدمج بها حساب الفاتورة ومسح البيانات
LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول</title>
    <style>
        body { font-family: sans-serif; background-color: #faf6f0; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin:0; }
        .card { background: white; width: 90%; max-width: 360px; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); text-align: center; border: 1px solid #f0eae1; }
        h2 { color: #bd4c4c; margin-bottom: 10px; }
        p { color: #7f8c8d; font-size: 14px; }
        input { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #e0e0e0; border-radius: 8px; box-sizing: border-box; background: #fafafa; }
        button { width: 100%; padding: 12px; border: none; border-radius: 8px; font-weight: bold; background-color: #d9534f; color: white; cursor: pointer; margin-top: 10px; }
        .error { color: red; font-size: 13px; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔐 تسجيل الدخول للمطعم</h2>
        <p>قم بكتابة اسمك وكلمة مرورك لفتح المطعم السري وتخزين بياناتك</p>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">دخول الحساب / إنشاء جديد</button>
        </form>
    </div>
</body>
</html>
'''

RESTAURANT_HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مطعمك السري</title>
    <style>
        body { font-family: sans-serif; background-color: #faf6f0; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin:0; padding: 20px 0; }
        .card { background: white; width: 90%; max-width: 380px; padding: 25px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); text-align: center; border: 1px solid #f0eae1; }
        h2 { color: #333; margin: 0; font-size: 20px; }
        .welcome-user { color: #e67e22; font-weight: bold; font-size: 24px; margin: 5px 0 15px 0; }
        .menu-preview { background-color: #fffcf7; border: 1px dashed #f39c12; padding: 10px; border-radius: 8px; margin: 15px 0; color: #d35400; font-size: 14px; }
        select { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #e0e0e0; border-radius: 8px; background: #fafafa; }
        .btn-group { display: flex; gap: 10px; margin-top: 15px; }
        button { flex: 1; padding: 12px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; color: white; }
        .btn-order { background-color: #d9534f; }
        .btn-logout { background-color: #f0ad4e; text-decoration: none; display: flex; justify-content: center; align-items: center; border-radius: 8px; font-size: 14px; font-weight: bold; }
        .database-box { margin-top: 15px; text-align: right; background: #f9f9f9; padding: 12px; border-radius: 8px; border-right: 4px solid #d9534f; max-height: 180px; overflow-y: auto; font-size: 13px; }
        .order-item { border-bottom: 1px solid #eee; padding: 6px 0; color: #555; }
        .invoice-box { background-color: #eef9f1; color: #27ae60; padding: 10px; border-radius: 8px; font-weight: bold; margin-top: 15px; border: 1px solid #c2eabd; }
        .btn-clear { background-color: #7f8c8d; width: 100%; padding: 10px; border: none; border-radius: 8px; color: white; font-weight: bold; margin-top: 10px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h2>مرحباً بك في مطعمك السري يا</h2>
        <div class="welcome-user">🍕 ! {{ username }}</div>
        
        <p style="color: #7f8c8d; font-size: 14px;">📖 قائمة الطعام المميزة لدينا اليوم:</p>
        <div class="menu-preview">
            ✨ بيتزا إيطالية (80ج) - برجر مشوي (60ج) - باستا رائعة (50ج) ✨
        </div>

        <form action="/add_order" method="POST">
            <select name="meal">
                <option value="🍕 بيتزا إيطالية">🍕 بيتزا إيطالية (80 جنيه)</option>
                <option value="🍔 برجر مشوي">🍔 برجر مشوي (60 جنيه)</option>
                <option value="🍝 باستا رائعة">🍝 باستا رائعة (50 جنيه)</option>
            </select>
            <div class="btn-group">
                <button type="submit" class="btn-order">💾 اطلب الآن</button>
                <a href="/logout" class="btn-logout" style="color: white; flex: 1;">🚪 تسجيل الخروج</a>
            </div>
        </form>

        {% if total_price > 0 %}
        <!-- صندوق حساب الفاتورة الكلي المسترجع بذكاء -->
        <div class="invoice-box">
            💰 الفاتورة الإجمالية لطلباتك: {{ total_price }} جنيه مصري
        </div>
        {% endif %}

        <h4 style="text-align: right; margin: 20px 0 5px 0; color: #555;">📊 طلباتك المسترجعة من قاعدة بيانات بايثون:</h4>
        <div class="database-box">
            {% if orders %}
                {% for order in orders %}
                    <div class="order-item">• تم حفظ <b>{{ order[0] }}</b> بسعر ({{ order[1] }}ج) في قاعدة البيانات.</div>
                {% endfor %}
            {% else %}
                لا توجد طلبات مخزنة بعد لهذا الحساب.
            {% endif %}
        </div>

        {% if orders %}
        <!-- زر مسح قاعدة البيانات وإعادة التصفير -->
        <form action="/clear_orders" method="POST">
            <button type="submit" class="btn-clear">🗑️ مسح جميع بيانات الطلبات</button>
        </form>
        {% endif %}
    </div>
</body>
</html>
'''

# 3. توجيهات والتحكم في التطبيق وحساب الحسابات (Flask Routes)
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('restaurant'))
        
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        conn = sqlite3.connect('secret_restaurant_v3.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        
        if user:
            if user[0] == password:
                session['username'] = username
                conn.close()
                return redirect(url_for('restaurant'))
            else:
                error = "كلمة المرور خاطئة لهذا الحساب!"
                conn.close()
        else:
            cursor.execute("INSERT INTO users VALUES (?, ?)", (username, password))
            conn.commit()
            session['username'] = username
            conn.close()
            return redirect(url_for('restaurant'))
            
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/restaurant')
def restaurant():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('secret_restaurant_v3.db')
    cursor = conn.cursor()
    # جلب الوجبات والأسعار معاً للمستخدم الحالي
    cursor.execute("SELECT meal, price FROM orders WHERE username=?", (session['username'],))
    user_orders = cursor.fetchall()
    
    # حساب مجموع الفاتورة تلقائياً عبر SQL
    cursor.execute("SELECT SUM(price) FROM orders WHERE username=?", (session['username'],))
    total_price = cursor.fetchone()[0] or 0
    conn.close()
    
    return render_template_string(RESTAURANT_HTML, username=session['username'], orders=user_orders, total_price=total_price)

@app.route('/add_order', methods=['POST'])
def add_order():
    if 'username' in session:
        meal = request.form['meal']
        
        # تحديد السعر بناءً على نوع الوجبة المحددة
        price = 50
        if "بيتزا" in meal: price = 80
        elif "برجر" in meal: price = 60
            
        conn = sqlite3.connect('secret_restaurant_v3.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (username, meal, price) VALUES (?, ?, ?)", (session['username'], meal, price))
        conn.commit()
        conn.close()
    return redirect(url_for('restaurant'))

@app.route('/clear_orders', methods=['POST'])
def clear_orders():
    if 'username' in session:
        conn = sqlite3.connect('secret_restaurant_v3.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE username=?", (session['username'],))
        conn.commit()
        conn.close()
    return redirect(url_for('restaurant'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

def open_browser():
    webbrowser.open_new('http://127.0.0')

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(host='127.0.0.1', port=5000, debug=False)
