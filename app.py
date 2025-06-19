from flask import Flask, render_template, request, redirect, url_for
import json, os, datetime

app = Flask(__name__)
DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({'items': [], 'orders': []}, f)
    with open(DATA_FILE, encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def today_str():
    return datetime.datetime.now().strftime('%d/%m/%Y')

def month_str():
    return datetime.datetime.now().strftime('%m/%Y')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/items', methods=['GET', 'POST'])
def items():
    data = load_data()
    if request.method == 'POST':
        if len(data['items']) < 30:
            name = request.form['name']
            price = int(request.form['price'])
            img = request.form['img']
            data['items'].append({'name': name, 'price': price, 'img': img})
            save_data(data)
        return redirect(url_for('items'))
    return render_template('items.html', items=data['items'])

@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    data = load_data()
    if 0 <= item_id < len(data['items']):
        data['items'].pop(item_id)
        save_data(data)
    return redirect(url_for('items'))

@app.route('/orders', methods=['GET', 'POST'])
def orders():
    data = load_data()
    if request.method == 'POST':
        order = []
        total = 0
        for i, item in enumerate(data['items']):
            qty = int(request.form.get(f'qty_{i}', 0))
            if qty > 0:
                order.append({'name': item['name'], 'price': item['price'], 'qty': qty, 'img': item['img']})
                total += item['price'] * qty
        if order:
            payment = request.form.get('payment', 'Tiền mặt')
            paid = request.form.get('paid', 'no') == 'yes'
            data['orders'].append({
                'order': order,
                'total': total,
                'time': datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'payment': payment,
                'paid': paid
            })
            save_data(data)
        return redirect(url_for('bills'))
    return render_template('orders.html', items=data['items'])

@app.route('/bills')
def bills():
    data = load_data()
    return render_template('bills.html', orders=data['orders'])

@app.route('/bill/<int:bill_id>', methods=['GET', 'POST'])
def bill_detail(bill_id):
    data = load_data()
    if not (0 <= bill_id < len(data['orders'])):
        return "Không tìm thấy bill", 404
    bill = data['orders'][bill_id]
    if request.method == 'POST':
        # Sửa bill
        for i, it in enumerate(bill['order']):
            qty = int(request.form.get(f'qty_{i}', it['qty']))
            bill['order'][i]['qty'] = qty
        bill['total'] = sum(it['price'] * it['qty'] for it in bill['order'])
        bill['payment'] = request.form.get('payment', bill['payment'])
        bill['paid'] = request.form.get('paid', 'no') == 'yes'
        bill['time'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        save_data(data)
        return redirect(url_for('bill_detail', bill_id=bill_id))
    return render_template('bill_detail.html', bill=bill, bill_id=bill_id)

@app.route('/delete_bill/<int:bill_id>')
def delete_bill(bill_id):
    data = load_data()
    if 0 <= bill_id < len(data['orders']):
        data['orders'].pop(bill_id)
        save_data(data)
    return redirect(url_for('bills'))

@app.route('/stats')
def stats():
    data = load_data()
    today = today_str()
    month = month_str()
    stats_day = {'total': 0, 'sold': {}}
    stats_month = {'total': 0, 'sold': {}}
    for o in data['orders']:
        if o['time'].startswith(today):
            stats_day['total'] += o['total']
            for it in o['order']:
                stats_day['sold'][it['name']] = stats_day['sold'].get(it['name'], 0) + it['qty']
        if o['time'][3:10] == month:
            stats_month['total'] += o['total']
            for it in o['order']:
                stats_month['sold'][it['name']] = stats_month['sold'].get(it['name'], 0) + it['qty']
    return render_template('stats.html', stats_day=stats_day, stats_month=stats_month)

if __name__ == '__main__':
    app.run(debug=True)