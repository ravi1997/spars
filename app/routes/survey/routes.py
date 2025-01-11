from pprint import pprint
from flask import current_app, request, jsonify
from flask_restx import Resource, Namespace, fields
from sqlalchemy.orm import joinedload
import jwt
from werkzeug.exceptions import Forbidden
from app.decorator import token_required, verify_superadmin
from app.model import db, Survey, Question, Option, Answer, QuestionConstraint, Role, User, SurveyAttempt
import datetime
from . import survey_ns
from app.schemas import surveys_schema,survey_schema,answers_schema

# Swagger Models
# Swagger Models with Complex Default Values
question_model = survey_ns.model('Question', {
    'id': fields.Integer(description="Question ID", default=1),
    'question': fields.String(required=True, description='Question text', default="What is your favorite programming language?"),
    'question_type': fields.String(required=True, description='Type of the question (e.g., single-choice, text)', default="single-choice"),
    'is_required': fields.Boolean(default=True, description='Is the question required?'),
    'default_value': fields.String(description='Default value for the question', default="Python"),
    'options': fields.List(fields.String, description='List of options for choice questions', default=["Python", "JavaScript", "C++", "Java"]),
    'constraints': fields.List(fields.Raw, description='List of constraints', default=[]),
    'parent_question_id': fields.Integer(description='ID of the parent question, if any',required=False, nullable=True),
    'parent_option_id': fields.Integer(description='ID of the parent option, if any', required=False,nullable=True)
})

survey_model = survey_ns.model('Survey', {
    'id': fields.Integer(description="Survey ID", default=0),
    'title': fields.String(required=True, description='Title of the survey', default="Programming Language Survey"),
    'description': fields.String(description='Description of the survey', default="A survey to collect user preferences on programming languages."),
    'state': fields.String(required=True, description='State of the survey (create, testing, release, close)', default="create"),
    'questions': fields.List(fields.Nested(question_model), description='List of questions', default=[
        {
            "id": 1,
            "question": "What is your favorite programming language?",
            "question_type": "single-choice",
            "is_required": True,
            "default_value": "Python",
            "options": ["Python", "JavaScript", "C++", "Java"],
            "constraints": [],
        },
        {
            "id": 2,
            "question": "What is your experience level?",
            "question_type": "single-choice",
            "is_required": True,
            "default_value": "Intermediate",
            "options": ["Beginner", "Intermediate", "Expert"],
            "constraints": [],
        }
    ]),
})

answer_model = survey_ns.model('Answer', {
    'question_id': fields.Integer(required=True, description='Question ID', default=1),
    'answer_text': fields.String(description='Answer text', default="Python"),
    'answer_file': fields.String(description='Path to the uploaded file (if applicable)', default=None),
    'selected_option_id': fields.Integer(description='Selected option ID for single-choice questions', default=None)
})

answer_submission_model = survey_ns.model('AnswerSubmission', {
    'answers': fields.List(fields.Nested(answer_model), required=True, description='List of answers to the survey questions')
})



# Utility functions
def validate_survey_edit_permission(survey, user):
    """Check if the user can edit the survey based on its state and user role."""
    if survey.state == "create" and survey.created_by_user_id == user.id:
        return True
    if survey.state not in ["create"]:
        raise Forbidden("Editing is not allowed in this state.")
    return False

def validate_survey_submission_permission(survey, user):
    """Check if the user can submit answers based on the survey state and their role."""
    if survey.status == "testing" and user.role.name != "tester":
        raise Forbidden("Only testers can submit answers for surveys in the testing phase.")
    if survey.status == "release" and user.role.name not in ["normal", "tester"]:
        raise Forbidden("Only normal or tester users can submit answers for surveys in the release phase.")
    if survey.status == "close":
        raise Forbidden("This survey is closed and cannot accept responses.")

# Resource Classes
@survey_ns.route('/')
class SurveyResource(Resource):
    @survey_ns.expect(survey_model, validate=True)
    @survey_ns.doc(
        summary="Create a new survey",
        description="Creates a new survey with questions and options.",
        responses={
            201: 'Survey created successfully',
            400: 'Bad request'
        }
    )
    @token_required
    def post(self,current_user):
        """Create a new survey"""
        data = request.json
        survey = Survey(
            title=data['title'],
            description=data.get('description'),
            status="create",
            created_by_user_id=current_user.id
        )
        db.session.add(survey)
        db.session.commit()

        for question_data in data['questions']:
            question = Question(
                survey_id=survey.id,
                text=question_data['question'],
                question_type=question_data['question_type'],
                is_required=question_data.get('is_required', True),
                default_value=question_data.get('default_value'),
                parent_question_id=question_data.get('parent_question_id'),
                parent_option_id=question_data.get('parent_option_id')
            )
            db.session.add(question)
            db.session.commit()

            if question.question_type in ['single-choice', 'multiple-choice']:
                for option_text in question_data.get('options', []):
                    option = Option(question_id=question.id, text=option_text)
                    db.session.add(option)

        db.session.commit()
        return {"message": "Survey created successfully", "survey_id": survey.id}, 201
        
    @survey_ns.doc(
        summary="Fetch all surveys",
        description="Returns a list of all surveys.",
        responses={
            200: 'List of surveys',
        }
    )
    def get(self):
        """Fetch all surveys"""
        surveys = Survey.query.all()
        
        return surveys_schema.dump(surveys), 200

@survey_ns.route('/<int:survey_id>')
@survey_ns.param('survey_id', 'The Survey ID')
class SingleSurveyResource(Resource):
    @survey_ns.doc(
        summary="Fetch a specific survey",
        description="Fetch details of a survey by its ID.",
        responses={
            200: 'Survey details',
            404: 'Survey not found'
        }
    )
    def get(self, survey_id):
        """Fetch a specific survey"""
        survey = Survey.query.get_or_404(survey_id)

        return survey_schema.dump(survey), 200

    @survey_ns.expect(survey_model, validate=True)
    @survey_ns.doc(
        summary="Update an existing survey",
        description="Update the title and description of an existing survey.",
        responses={
            200: 'Survey updated successfully',
            400: 'Bad request',
            404: 'Survey not found'
        }
    )
    def put(self, survey_id):
        """Update a survey"""
        data = request.json
        survey = Survey.query.get_or_404(survey_id)

        # Check permissions
        validate_survey_edit_permission(survey, request.user)

        survey.title = data.get('title', survey.title)
        survey.description = data.get('description', survey.description)

        db.session.commit()
        return {"message": "Survey updated successfully"}, 200

    @survey_ns.doc(
        summary="Delete a survey",
        description="Delete a survey by its ID.",
        responses={
            200: 'Survey deleted successfully',
            404: 'Survey not found'
        }
    )
    def delete(self, survey_id):
        """Delete a survey"""
        survey = Survey.query.get_or_404(survey_id)
        db.session.delete(survey)
        db.session.commit()
        return {"message": "Survey deleted successfully"}, 200

@survey_ns.route('/<int:survey_id>/answers')
@survey_ns.param('survey_id', 'The Survey ID')
class SurveyAnswersResource(Resource):
    @survey_ns.expect(answer_submission_model, validate=True)
    @survey_ns.doc(
        summary="Submit answers for a survey",
        description="Submit answers for the specified survey.",
        responses={
            201: 'Answers submitted successfully',
            400: 'Bad request',
            403: 'Forbidden'
        }
    )
    @token_required
    def post(self, current_user, survey_id):
        """Submit multiple answers for different questions in a survey"""
        data = request.json
        survey = Survey.query.get_or_404(survey_id)

        # Validate submission permissions
        validate_survey_submission_permission(survey, current_user)

        # Record the survey attempt
        attempt = SurveyAttempt(
            user_id=current_user.id,
            survey_id=survey.id,
            attempt_date=datetime.datetime.utcnow()
        )
        db.session.add(attempt)
        db.session.flush()  # Generate `attempt.id` before adding answers

        # Batch insert answers
        answers_to_insert = []
        for answer_data in data['answers']:
            question = Question.query.filter_by(
                id=answer_data['question_id'], survey_id=survey_id
            ).first_or_404()
            
            answers_to_insert.append(Answer(
                survey_id=survey.id,
                question_id=question.id,
                answer_text=answer_data.get('answer_text'),
                answer_file=answer_data.get('answer_file'),
                attempt_id=attempt.id
            ))

        # Add all answers at once
        db.session.bulk_save_objects(answers_to_insert)
        db.session.commit()

        return {
            "message": "Answers submitted successfully",
            "attempt_id": attempt.id,
            "answers_count": len(answers_to_insert)
        }, 201

    @survey_ns.doc(
        summary="Fetch all answers for a survey",
        description="Fetch a list of all answers submitted for the specified survey.",
        responses={
            200: 'List of answers'
        }
    )
    @token_required
    def get(self,current_user, survey_id):
        """Fetch all answers for a survey"""
        answers = (
            Answer.query
                .join(SurveyAttempt, SurveyAttempt.id == Answer.attempt_id)
                .filter(SurveyAttempt.user_id == current_user.id, SurveyAttempt.survey_id == survey_id)
                .options(joinedload(Answer.question))  # Optional: Load related question data
                .all()
        )
        return answers_schema.dump(answers), 200


