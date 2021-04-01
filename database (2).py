from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from tables import *
from datetime import date

engine = create_engine('sqlite:///database.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base.query = db_session.query_property()


def init_db():
    Base.metadata.create_all(bind=engine)


def book_entry(isbn, book_name, author, publisher, publish_year_month, librarian_id, book_id, location):
    librarian = db_session.query(Librarian).filter(Librarian.id == librarian_id).first()
    cip = db_session.query(CIP).filter(CIP.isbn == isbn).first()
    if cip is None:
        cip = CIP(isbn=isbn, book_name=book_name, author=author, publisher=publisher, publish_year_month=publish_year_month, librarian=librarian)

    status = BookStatus.available if location == 'Circulation room' else BookStatus.unborrowable
    book = Book(id=book_id, cip=cip, location=location, status=status, librarian=librarian)

    db_session.add(book)
    db_session.commit()


def populate_data():
    librarian1 = Librarian(id='lib0001', name='Ali', password='lib0001')
    librarian2 = Librarian(id='lib0002', name='Sarthak', password='lib0002')
    librarian3 = Librarian(id='lib0003', name='Virag', password='lib0003')

    db_session.add_all([librarian1, librarian2, librarian3,
    ])
    db_session.commit()

   
