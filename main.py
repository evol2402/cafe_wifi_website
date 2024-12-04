from flask import Flask, jsonify, render_template, request,redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from forms import DeleteCafeForm, AdminDeleteCafeForm
from dotenv import load_dotenv
import smtplib
import os

app = Flask(__name__)


# CREATE DB connection
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CREATE TABLE
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


with app.app_context():
    db.create_all()

load_dotenv()
MAIL_ADDRESS = os.environ.get("EMAIL_KEY")
MAIL_APP_PW = os.environ.get("PASSWORD_KEY")
def send_email(name, email, subject, message):
    email_message = f"Subject: {subject}\n\nName: {name}\nEmail: {email}\nMessage: {message}"
    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(MAIL_ADDRESS, MAIL_APP_PW)
        connection.sendmail(MAIL_ADDRESS, MAIL_ADDRESS, email_message)
def clean_price(price_str):
    """Remove currency symbols and spaces, and convert to float."""
    cleaned_price = price_str.replace('£', '').replace(' ', '')
    return float(cleaned_price) if cleaned_price else None


# Define routes
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/add-cafe', methods=['GET', 'POST'])
def add_cafe():
    if request.method == 'POST':
        # Get form data from the request
        name = request.form.get('name')
        location = request.form.get('location')
        map_url = request.form.get('map_url')
        img_url = request.form.get('img_url')
        seats = request.form.get('seats')
        has_wifi = request.form.get('has_wifi') == 'true'
        has_sockets = request.form.get('has_sockets') == 'true'
        can_take_calls = request.form.get('can_take_calls') == 'true'
        coffee_price = request.form.get('coffee_price')

        # Validate the form data
        if not name or not location or not map_url or not img_url:
            flash("Please fill out all required fields", "error")  # Flash an error message
            return redirect(url_for('add_cafe'))  # Redirect to the add café page

        # Check if the café already exists in the database
        existing_cafe = Cafe.query.filter_by(name=name, location=location).first()
        if existing_cafe:
            flash("This café already exists in the database. Please check the name and location. If it's a different café, consider adding additional details or a different name", "error")  # Flash an error message
            return redirect(url_for('add_cafe'))  # Redirect to the add café page

        # Create a new Cafe object
        new_cafe = Cafe(
            name=name,
            map_url=map_url,
            img_url=img_url,
            location=location,
            seats=seats,
            has_toilet=request.form.get('has_toilet') == 'true',
            has_wifi=has_wifi,
            has_sockets=has_sockets,
            can_take_calls=can_take_calls,
            coffee_price=coffee_price
        )

        # Add the new café to the database
        try:
            db.session.add(new_cafe)
            db.session.commit()
            return render_template('success.html')  # Redirect to café listings page
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            flash(f"An error occurred: {e}", "error")  # Flash an error message
            return redirect(url_for('add_cafe'))  # Redirect to the add café page

    return render_template('add_cafe.html')



@app.route('/cafe_listings')
def cafe_listings():
    # Retrieve query parameters for filtering
    has_wifi = request.args.get('has_wifi', 'false') == 'true'
    has_sockets = request.args.get('has_sockets', 'false') == 'true'
    can_take_calls = request.args.get('can_take_calls', 'false') == 'true'
    affordable = request.args.get('affordable', 'false') == 'true'
    search_query = request.args.get('search', '').lower()  # Capture the search input

    # Fetch all cafes from the database
    result = db.session.execute(db.select(Cafe).order_by(Cafe.name))
    all_cafes = result.scalars().all()

    # Filter cafes based on selected features and search query
    filtered_cafes = []
    for cafe in all_cafes:
        # Clean the coffee price for comparison
        cleaned_price = clean_price(cafe.coffee_price) if cafe.coffee_price else None

        # Check if the cafe matches the search query
        matches_search = (search_query in cafe.name.lower() or
                          search_query in cafe.location.lower())

        # If there's no search query, simply add all cafes (or none based on filtering)
        if search_query == '':
            if (not has_wifi or cafe.has_wifi) and \
               (not has_sockets or cafe.has_sockets) and \
               (not can_take_calls or cafe.can_take_calls) and \
               (not affordable or (cleaned_price is not None and cleaned_price < 2.5)):
                filtered_cafes.append(cafe)
        else:
            # If there is a search query, apply the filtering conditions
            if (matches_search and
                (not has_wifi or cafe.has_wifi) and \
                (not has_sockets or cafe.has_sockets) and \
                (not can_take_calls or cafe.can_take_calls) and \
                (not affordable or (cleaned_price is not None and cleaned_price < 2.5))):
                filtered_cafes.append(cafe)

    # Check if any cafes were found after filtering
    no_cafes_found = len(filtered_cafes) == 0 and search_query != ''

    # Pass the filtered cafes data and no_cafes_found flag to the template
    return render_template('cafe_listings.html', cafes=filtered_cafes, no_cafes_found=no_cafes_found, search_query=search_query)

@app.route('/suggestions')
def suggestions():
    search_query = request.args.get('query', '').lower()  # Get the search query
    result = db.session.execute(db.select(Cafe).order_by(Cafe.name))
    all_cafes = result.scalars().all()

    # Filter cafés based on the search query
    suggestions = [cafe.name for cafe in all_cafes if search_query in cafe.name.lower()]

    return jsonify(suggestions=suggestions)  # Return suggestions as JSON


@app.route('/delete-suggest-cafe', methods=['GET', 'POST'])
def delete_cafe():
    form = DeleteCafeForm()

    if form.validate_on_submit():
        cafe_name = form.cafe_name.data
        location = form.location.data
        username = form.username.data
        email = form.email.data
        reason = form.reason.data

        print(f'{cafe_name},{location},{username},{email},{reason}')
        # Attempt to send the email and handle potential errors
        try:
            send_email(username, email, f'Cafe Name: {cafe_name}, Location: {location}', reason)
            flash('Your request has been sent to the admin for review. You will be contacted soon.', 'success')
            return redirect(url_for('delete_cafe'))
        except Exception as e:
            flash(f'An error occurred while sending your request: {str(e)}', 'danger')

    return render_template('delete_cafe.html', form=form)


@app.route('/admin-delete050504', methods=['GET', 'POST'])
def admin_delete_cafe():
    form = AdminDeleteCafeForm()
    if form.validate_on_submit():
        cafe_id = form.cafe_id.data
        reason = form.reason.data
        cafe = Cafe.query.get(cafe_id)

        if cafe:
            # Handle deletion logic here (notify admin, log the reason, etc.)
            db.session.delete(cafe)
            db.session.commit()

            flash(f'{cafe.name} has been deleted. Reason: {reason}', 'success')
        else:
            flash('Café not found!', 'error')

        return redirect(url_for('admin_delete_cafe'))

    return render_template('admin_delete.html', form=form)


# Start the Flask app
if __name__ == "__main__":
    app.run(debug=True, port=5001)
