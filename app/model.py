from app.extensions import db
import uuid
from datetime import datetime, timedelta
import random
import string

# Association table for many-to-many relationship between User and Role
user_roles = db.Table('user_roles',
    db.Column('user_id', db.String(36), db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

# Association table for survey editors
survey_editors = db.Table('survey_editors',
    db.Column('survey_id', db.Integer, db.ForeignKey('survey.id'), primary_key=True),
    db.Column('user_id', db.String(36), db.ForeignKey('user.id'), primary_key=True)
)

class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # Name of the role (SUPERADMIN, ADMIN, USER, TESTER)

    # Many-to-many relationship with User
    users = db.relationship('User', secondary=user_roles, back_populates='roles')

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Role {self.name}>"


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # UUID as primary key
    first_name = db.Column(db.String(50), nullable=True)
    middle_name = db.Column(db.String(50), nullable=True)  # Middle name is optional
    last_name = db.Column(db.String(50), nullable=True)
    dob = db.Column(db.Date, nullable=True)  # Date of Birth
    mobile = db.Column(db.String(15), unique=True, nullable=False)  # Unique mobile number
    aadhar = db.Column(db.String(12), unique=True, nullable=True)  # Unique Aadhar number
    gender = db.Column(db.String(10), nullable=True)  # Gender field, e.g., "Male", "Female", etc.

    # Many-to-many relationship with Role
    roles = db.relationship('Role', secondary=user_roles, back_populates='users')

    # Surveys the user can edit
    editable_surveys = db.relationship(
        'Survey',
        secondary=survey_editors,
        back_populates='editors'
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User {self.first_name} {self.last_name}>"


class Survey(db.Model):
    __tablename__ = 'survey'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by_user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)  # Foreign key to User
    status = db.Column(db.String(20), default='draft', nullable=False)  # Survey status (draft, published, closed)

    # Relationships
    created_by = db.relationship('User', backref=db.backref('created_surveys', lazy='dynamic'))
    editors = db.relationship(
        'User',
        secondary=survey_editors,
        back_populates='editable_surveys'
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Survey {self.title} by {self.created_by.first_name}>"


class Question(db.Model):
    __tablename__ = 'question'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # E.g., text, multiple_choice, etc.
    is_required = db.Column(db.Boolean, default=True)
    default_value = db.Column(db.Text, nullable=True)
    parent_question_id = db.Column(
        db.Integer, 
        db.ForeignKey('question.id', use_alter=True, name='fk_parent_question_id'), 
        nullable=True  # Allow NULL values
    )
    parent_option_id = db.Column(
        db.Integer, 
        db.ForeignKey('option.id', use_alter=True, name='fk_parent_option_id'), 
        nullable=True  # Allow NULL values
    )

    # Relationships
    survey = db.relationship('Survey', backref=db.backref('questions', cascade='all, delete-orphan'))
    parent_question = db.relationship('Question', remote_side=[id])
    parent_option = db.relationship(
        'Option',
        foreign_keys=[parent_option_id],
        backref=db.backref('branching_questions', lazy='dynamic')
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)


class Option(db.Model):
    __tablename__ = 'option'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id', use_alter=True, name='fk_question_id'), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer, nullable=False, default=0)  # Order of the option

    # Relationship
    question = db.relationship(
        'Question',
        backref=db.backref('options', cascade='all, delete-orphan'),
        foreign_keys=[question_id]  # Specify the foreign key explicitly
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class QuestionConstraint(db.Model):
    __tablename__ = 'question_constraint'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    constraint_type = db.Column(db.String(50), nullable=False)  # E.g., max_length, regex
    constraint_value = db.Column(db.Text, nullable=False)  # Value for the constraint

    # Relationship
    question = db.relationship('Question', backref=db.backref('constraints', cascade='all, delete-orphan'))

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Answer(db.Model):
    __tablename__ = 'answer'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answer_text = db.Column(db.Text, nullable=True)  # For text, number, date, etc.
    answer_file = db.Column(db.String(255), nullable=True)  # File/image path
    response_id = db.Column(db.Integer, db.ForeignKey('response.id'), nullable=True)  # Link to Response
    selected_option_id= db.Column(db.Integer, db.ForeignKey('option.id'), nullable=True)

    question = db.relationship('Question', backref=db.backref('answers', cascade='all, delete-orphan'))

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    attempt_id = db.Column(db.Integer, db.ForeignKey("survey_attempts.id"), nullable=False)

class SurveyAttempt(db.Model):
    __tablename__ = "survey_attempts"
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("survey.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    attempt_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Response(db.Model):
    __tablename__ = 'response'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)  # Nullable for anonymous responses
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    survey = db.relationship('Survey', backref=db.backref('responses', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('responses', lazy='dynamic'))

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Otp(db.Model):
    __tablename__ = 'otp'

    id = db.Column(db.Integer, primary_key=True)
    mobile = db.Column(db.String(15), nullable=False)  # Unique mobile number
    otp = db.Column(db.String(6), nullable=False)  # OTP should be 6 digits
    expiration_time = db.Column(db.DateTime, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)


    def __repr__(self):
        return f"<Otp {self.otp} for User {self.mobile}>"

    @staticmethod
    def generate_otp():
        return ''.join(random.choices(string.digits, k=6))

    @staticmethod
    def create_otp(mobile):
        otp_value = Otp.generate_otp()
        expiration_time = datetime.utcnow() + timedelta(minutes=5)  # OTP expires in 5 minutes
        otp = Otp(mobile=mobile, otp=otp_value, expiration_time=expiration_time)
        db.session.add(otp)
        db.session.commit()
        return otp_value


