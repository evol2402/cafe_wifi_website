from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Email
#from flask_ckeditor import CKEditorField

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

class DeleteCafeForm(FlaskForm):
    cafe_name = StringField('Café Name', validators=[DataRequired()])
    location = StringField('Café Location', validators=[DataRequired()])  # New location field
    username = StringField('Your Name', validators=[DataRequired()])
    email = StringField('Your Email', validators=[DataRequired(), Email()])
    reason = TextAreaField('Reason for Updating/Deleting', validators=[DataRequired()])
    submit = SubmitField('Update/Request Deletion')


class AdminDeleteCafeForm(FlaskForm):
    cafe_id = StringField('Cafe ID', validators=[DataRequired()])
    reason = TextAreaField('Reason for Deleting', validators=[DataRequired()])
    submit = SubmitField('Confirm Deletion')