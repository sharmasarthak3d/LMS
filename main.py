from flask import Flask, jsonify, request, render_template, redirect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db_session, init_db, populate_data
from tables import *
from datetime import date, datetime, timedelta
from sqlalchemy import or_
# from gmail import send_email

app = Flask(__name__)

init_db()
populate_data()


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return render_template('books_management.html', book_locations=['Circulation Room', 'Reading Room'])
        else:
            return render_template('login.html')
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']

        user = User.query.filter_by(id=user_id).first()
        print(user)
        if user:
            if user.password == password:
                login_user(user)
                user.is_authenticated = True
                db_session.commit()
                return redirect('/')
            else:
                return render_template('login.html', error='Wrong Passwords', user_id=user_id, password=password)
        else:
            return render_template('login.html', error='User does not exist', user_id=user_id, password=password)


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    db_session.commit()
    return redirect('/')


@app.route('/cip_books')
@login_required
def cip_books():
    return render_template('cip_books.html', data_url='books?isbn=%s' % request.args['isbn'], index=request.args['index'])


@app.route('/cips', methods=['GET'])
@login_required
def cips():
    isbn_prefix = request.args.get('isbn_prefix', None)

    if isbn_prefix:
        cips = CIP.query.filter(CIP.isbn.startswith(isbn_prefix))
    else:
        cips = CIP.query.all()

    properties = [cip.properties() for cip in cips]

    for index in range(len(properties)):
        cip = cips[index]
        properties[index]['deletable'] = all([book.status == BookStatus.available for book in cip.books])
        properties[index]['reservable'] = all([book.status != BookStatus.available for book in cip.books])

    return jsonify(properties)


@app.route('/readers', methods=['GET'])
@login_required
def readers():
    query_text = request.args.get('query_text')

    if query_text:
        readers = Reader.query.filter(or_(Reader.id.like('%' + query_text + '%'), Reader.name.like('%' + query_text + '%')))
    else:
        readers = Reader.query.all()
    return jsonify([reader.properties() for reader in readers])


@app.route('/cip', methods=['GET'])
@login_required
def cip():
    isbn = request.args.get('isbn', None)

    cip = CIP.query.get(isbn)

    return jsonify(cip.properties())


@app.route('/books', methods=['GET'])
@login_required
def books():
    isbn = request.args['isbn']
    books = Book.query.filter(Book.cip_id == isbn)
    return jsonify([book.properties() for book in books])


@app.route('/borrowed_info', methods=['GET'])
@login_required
def borrowed_info():
    book_id = request.args['book_id']
    book = Book.query.get(book_id)
    borrows = [borrow for borrow in book.borrows if borrow.actual_return_date is None]

    if len(borrows) > 0:
        return jsonify(borrows[0].properties())
    else:
        return jsonify([])


@app.route('/reservation_info', methods=['GET'])
@login_required
def reservation_info():
    book_id = request.args['book_id']
    book = Book.query.get(book_id)

    return jsonify(book.reservation.properties())


@app.route('/book_entry', methods=['POST'])
@login_required
def book_entry():
    isbn = request.form['isbn']
    librarian = current_user

    cip = CIP.query.get(isbn)
    if cip is None:
        book_name = request.form['book_name']
        author = request.form['author']
        publisher = request.form['publisher']
        publish_year_month = datetime.strptime(request.form['publish_date'], '%Y-%m').date()

        cip = CIP(isbn=isbn, book_name=book_name, author=author, publisher=publisher, publish_year_month=publish_year_month, librarian=librarian)

    location = request.form['location']
    book_ids = request.form.getlist('book_id')

    status = BookStatus.available if location == '图书流通室' else BookStatus.unborrowable
    books = [Book(id=book_id, cip=cip, location=location, status=status, librarian=librarian) for book_id in book_ids]

    db_session.add_all(books)
    db_session.commit()
    return jsonify({'success': True})


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


app.secret_key = 'com.jerome-tan.library'
if __name__ == "__main__":
    app.config['ENV'] = 'production'
    app.run(host='0.0.0.0', debug=False)
