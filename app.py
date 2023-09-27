from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKeyConstraint, func
from sqlalchemy.orm import relationship


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
db = SQLAlchemy(app)

# Define models

# Define the Book model
class Book(db.Model):
    __tablename__ = 'books'

    bookID = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    publishedYear = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='available')
    bookType = db.Column(db.Integer, nullable=False)

    # Establish a one-to-many relationship with loans
    loans = relationship('Loan', backref='book', lazy=True)

    # Data integrity: ensure titles are unique
    __table_args__ = (db.UniqueConstraint('title', name='unique_title'),)

    def __init__(self, title, author, publishedYear, bookType):
        self.title = title
        self.author = author
        self.publishedYear = publishedYear
        self.status = 'available'
        self.bookType = bookType

# Define the Customer model
class Customer(db.Model):
    __tablename__ = 'customers'

    customerID = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    city = db.Column(db.String(255), nullable=False)

    # Establish a one-to-many relationship with loans
    loans = relationship('Loan', backref='customer', lazy=True)
    
    def __init__(self, customerID, name, age, city):
        self.customerID = customerID
        self.name = name
        self.age = age
        self.city = city

# Define the Loan model
class Loan(db.Model):
    __tablename__ = 'loans'

    loanID = db.Column(db.Integer, primary_key=True)
    loanDate = db.Column(db.Date, nullable=False)
    bookID = db.Column(db.Integer, db.ForeignKey('books.bookID'), nullable=False)
    customerID = db.Column(db.Integer, db.ForeignKey('customers.customerID'), nullable=False)
    returnDate = db.Column(db.Date, nullable=False)

    # Data Integrity: Define a ForeignKeyConstraint to enforce the relationship
    __table_args__ = (
        ForeignKeyConstraint(['bookID'], ['books.bookID']),
        ForeignKeyConstraint(['customerID'], ['customers.customerID']),
    )

    def __init__(self, loanDate, bookID, customerID):
        self.loanDate = loanDate
        self.bookID = bookID
        self.customerID = customerID
        
        
        # Set the 'returnDate' based on the book's type
        book = Book.query.get(bookID)
        if book:
            if book.bookType == 1:
                self.returnDate = loanDate + timedelta(days=10)
            elif book.bookType == 2:
                self.returnDate = loanDate + timedelta(days=5)
            elif book.bookType == 3:
                self.returnDate = loanDate + timedelta(days=2)

# Define routes

# Route to create a new book
@app.route('/books', methods=['POST'])
def create_book():
    data = request.get_json()
    
    # Validate that required fields are present in the request data
    if 'title' not in data or 'author' not in data or 'publishedYear' not in data or 'bookType' not in data:
        return jsonify({'error': 'Required fields are missing in the request data (must be: title, author, publisheadYear, and bookType)'}, 400)
    
    title = data['title']
    author = data['author']
    publishedYear = data['publishedYear']
    bookType = data['bookType']

    # Additional data validation for bookType
    if bookType not in [1, 2, 3]:
        return jsonify({'error': 'Invalid bookType. It must be 1, 2, or 3'}, 400)

    new_book = Book(title=title, author=author, publishedYear=publishedYear, bookType=bookType)
    db.session.add(new_book)
    db.session.commit()

    return jsonify({'message': 'Book created successfully!'})

# Route to retrieve all books
@app.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()

    book_list = [{'bookID': book.bookID, 'title': book.title, 'author': book.author, 'publication year': book.publishedYear, 'status': book.status, 'book Type': book.bookType} for book in books]

    return jsonify({'books': book_list})

# Route to search for a book by title
@app.route('/books/search', methods=['GET'])
def search_books_by_title():
    search_query = request.args.get('q')

    if search_query:
        books = Book.query.filter(Book.title.ilike(f'%{search_query}%')).all()

        if books:
            book_list = [{
                'bookID': book.bookID,
                'title': book.title,
                'author': book.author,
                'publishedYear': book.publishedYear,
                'status': book.status
            } for book in books]

            return jsonify({'books': book_list})
        else:
            return jsonify({'message': 'No books found matching the search query'})
    else:
        return jsonify({'error': 'Search query is missing'}, 400)

# Route to update a book
@app.route('/books/<int:bookID>', methods=['PUT'])
def update_book(bookID):
    data = request.get_json()
    new_title = data.get('title')
    new_author = data.get('author')
    new_publishedYear = data.get('publishedYear')
    new_bookType = data.get('bookType')

    book = Book.query.get(bookID)

    if book:
        if new_title is not None:
            book.title = new_title
        if new_author is not None:
            book.author = new_author
        if new_publishedYear is not None:
            book.publishedYear = new_publishedYear
        if new_bookType is not None:
            book.bookType = new_bookType

        db.session.commit()

        return jsonify({'message': 'Book updated successfully'})
    else:
        return jsonify({'error': 'Book not found'}, 404)

# Route to delete a book
@app.route('/books/<int:bookID>', methods=['DELETE'])
def delete_book(bookID):
    book = Book.query.get(bookID)

    if book:
        db.session.delete(book)
        db.session.commit()
        return jsonify({'message': 'Book deleted successfully'})
    else:
        return jsonify({'error': 'Book not found'}, 404)

# Route to create a new customer
@app.route('/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    
    # Validate that required fields are present in the request data
    if 'customerID' not in data or 'name' not in data or 'age' not in data or 'city' not in data:
        return jsonify({'error': 'Required fields are missing in the request data (must be: customerID, name, age, city)'}, 400)
    
    customerID = data['customerID']
    name = data['name']
    age = data['age']
    city = data['city']
    
    # Check if a customer with the same customerID already exists
    existing_customer = Customer.query.filter_by(customerID=customerID).first()
    
    if existing_customer:
        return jsonify({'error': 'CustomerID is already in use'}), 400

    new_customer = Customer(customerID=customerID, name=name, age=age, city=city)
    db.session.add(new_customer)
    db.session.commit()

    return jsonify({'message': 'Customer created successfully!'})

# Route to retrieve all customers
@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()

    customer_list = [{'customerID': customer.customerID, 'name': customer.name, 'age': customer.age, 'city': customer.city} for customer in customers]

    return jsonify({'customers': customer_list})

# Route to search for a customer by name
@app.route('/customers/search', methods=['GET'])
def search_customers_by_name():
    search_query = request.args.get('q')

    if search_query:
        customers = Customer.query.filter(Customer.name.ilike(f'%{search_query}%')).all()

        if customers:
            # Create a list of dictionaries containing customer details
            customer_list = [{
                'customerID': customer.customerID,
                'name': customer.name,
                'age': customer.age,
                'city': customer.city
            } for customer in customers]

            return jsonify({'customers': customer_list})
        else:
            return jsonify({'message': 'No customers found matching the search query'})
    else:
        return jsonify({'error': 'Search query is missing'}, 400)

# Route to update a customer
@app.route('/customers/<string:customerID>', methods=['PUT'])
def update_customer(customerID):
    data = request.get_json()
    new_name = data.get('name')
    new_age = data.get('age')
    new_city = data.get('city')

    customer = Customer.query.get(customerID)

    if customer:
        if new_name is not None:
            customer.name = new_name
        if new_age is not None:
            customer.age = new_age
        if new_city is not None:
            customer.city = new_city

        db.session.commit()

        return jsonify({'message': 'Customer updated successfully'})
    else:
        return jsonify({'error': 'Customer not found'}, 404)

# Route to delete a customer
@app.route('/customers/<string:customerID>', methods=['DELETE'])
def delete_customer(customerID):
    customer = Customer.query.get(customerID)

    if customer:
        db.session.delete(customer)
        db.session.commit()
        return jsonify({'message': 'Customer deleted successfully'})
    else:
        return jsonify({'error': 'Customer not found'}, 404)

# Route to create a new loan
@app.route('/loans', methods=['POST'])
def create_loan():
    data = request.get_json()
    
    # Validate that required fields are present in the request data
    if 'loanDate' not in data or 'bookID' not in data or 'customerID' not in data:
        return jsonify({'error': 'Required fields are missing in the request data (must be: loanDate, bookID, and customerID)'}, 400)
    
    loanDate_str = data['loanDate']
    bookID = data['bookID']
    customerID = data['customerID']
    
    # Validate the loanDate format
    try:
        loanDate = datetime.strptime(loanDate_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Please use the format YYYY-MM-DD'}), 400

    # Convert the loanDate string to a Python date object
    loanDate = datetime.strptime(loanDate_str, '%Y-%m-%d').date()

    # Check if the book with the specified bookID exists
    book = Book.query.get(bookID)

    # Check if the customer with the specified customerID exists
    customer = Customer.query.get(customerID)
    
    if book and book.status == 'available' and customer:
        # Update the book status to "unavailable"
        book.status = 'unavailable'

        # Create a new loan
        new_loan = Loan(loanDate=loanDate, bookID=bookID, customerID=customerID)
        db.session.add(new_loan)

        db.session.commit()

        return jsonify({'message': 'Loan created successfully!'})
    elif not customer:
        return jsonify({'error': 'Customer not found'}, 404)
    elif book and book.status == 'unavailable':
        return jsonify({'error': 'Book is already loaned'}, 400)
    else:
        return jsonify({'error': 'Book not found'}, 404)

# Route to retrieve all loans
@app.route('/loans', methods=['GET'])
def get_loans():
    loans = Loan.query.all()
    
    # Validation for when there are no activate loans
    if not loans:
        return jsonify({'error': 'There are no active loans'}), 404
    
    loan_list = [{'loanID': loan.loanID, 'loanDate': loan.loanDate, 'returnDate': loan.returnDate, 'bookID': loan.bookID, 'customerID': loan.customerID} for loan in loans]

    return jsonify({'loans': loan_list})

# Route to end a loan by book title
@app.route('/loans', methods=['DELETE'])

def end_loan():
    book_title = request.args.get('q')
    if book_title:

        # Check if there is a book with a title that matches (case-insensitive)
        book = Book.query.filter(func.lower(Book.title) == func.lower(book_title)).first()

        if book:
            # Check if there is a loan for this book
            loan = Loan.query.filter_by(bookID=book.bookID).first()

            if loan:
                
                book.status = 'available'
                db.session.delete(loan)
                db.session.commit()

                return jsonify({'message': 'Loan ended successfully'})
            else:
                return jsonify({'error': 'No loan found for this book'}, 400)
        else:
            return jsonify({'error': 'Book not found'}, 404)
    else:
        return jsonify({'error': 'search quary is missing (parameter: q)'})

# Route to retrieve all late loans
@app.route('/loans/late', methods=['GET'])
def get_late_loans():
    current_date = datetime.now().date()

    late_loans = Loan.query.filter(Loan.returnDate < current_date).all()

    late_loan_list = [{'loanID': loan.loanID, 'loanDate': loan.loanDate, 'returnDate': loan.returnDate, 'bookID': loan.bookID, 'customerID': loan.customerID} for loan in late_loans]

    return jsonify({'late_loans': late_loan_list})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
