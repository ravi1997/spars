from app.extensions import ma
from app.model import Answer, Survey, Question, Option, QuestionConstraint, User, Role, Otp

# Schemas

# Role Schema
class RoleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Role
        include_fk = True
        load_instance = True

    users = ma.Nested('UserSchema', many=True, exclude=('roles',))  # Prevent circular reference

# User Schema
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_fk = True
        load_instance = True

    roles = ma.Nested(RoleSchema, many=True)  # Include roles as nested objects

# Otp Schema
class OtpSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Otp
        include_fk = True
        load_instance = True

# Survey Schema
class SurveySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Survey
        include_fk = True
        load_instance = True

    questions = ma.Nested('QuestionSchema', many=True)  # Include related questions

# Question Schema
class QuestionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Question
        include_fk = True
        load_instance = True
        exclude = ('answers',)  # Exclude the answers field to prevent circular references

    survey = ma.Nested(SurveySchema, exclude=('questions',))  # Prevent circular reference
    options = ma.Nested('OptionSchema', many=True)  # Include related options
    constraints = ma.Nested('QuestionConstraintSchema', many=True)  # Include related constraints
    parent_question = ma.Nested('QuestionSchema', exclude=('parent_question', 'parent_option', 'survey'))  # Self-referencing
    parent_option = ma.Nested('OptionSchema', exclude=('question',))  # Prevent circular reference



# Option Schema
class OptionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Option
        include_fk = True
        load_instance = True

    question = ma.Nested(QuestionSchema, exclude=('options',))  # Prevent circular reference
    branching_questions = ma.Nested(QuestionSchema, many=True, exclude=('parent_option',))  # Questions linked to this option

# Question Constraint Schema
class QuestionConstraintSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = QuestionConstraint
        include_fk = True
        load_instance = True

    question = ma.Nested(QuestionSchema, exclude=('constraints',))  # Prevent circular reference

# Answer Schema
class AnswerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Answer
        include_fk = True
        load_instance = True

    survey = ma.Nested(SurveySchema, exclude=('answers',))  # Prevent circular reference
    question = ma.Nested(QuestionSchema, exclude=('answers',))  # Exclude answers to prevent circular reference


# Schema Instances
user_schema = UserSchema()
users_schema = UserSchema(many=True)

role_schema = RoleSchema()
roles_schema = RoleSchema(many=True)

otp_schema = OtpSchema()
otps_schema = OtpSchema(many=True)

survey_schema = SurveySchema()
surveys_schema = SurveySchema(many=True)

question_schema = QuestionSchema()
questions_schema = QuestionSchema(many=True)

option_schema = OptionSchema()
options_schema = OptionSchema(many=True)

constraint_schema = QuestionConstraintSchema()
constraints_schema = QuestionConstraintSchema(many=True)

answer_schema = AnswerSchema()
answers_schema = AnswerSchema(many=True)
