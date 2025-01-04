from flask import request, jsonify
from werkzeug.utils import secure_filename
from . import survey_bp
from app.model import db, Survey, Question, Option, Answer, QuestionConstraint
from app.schemas import survey_schema, answer_schema
import os

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'png', 'pdf', 'docx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@survey_bp.route('/', methods=['POST'])
def create_survey():
    data = request.json
    if not data or 'title' not in data or 'questions' not in data:
        return jsonify({"error": "Invalid request. 'title' and 'questions' are required"}), 400

    try:
        survey = Survey(title=data['title'], description=data.get('description'))
        db.session.add(survey)
        db.session.commit()

        for question_data in data['questions']:
            question = Question(
                survey_id=survey.id,
                text=question_data['text'],
                question_type=question_data['question_type'],
                is_required=question_data.get('is_required', True),
                default_value=question_data.get('default_value')
            )
            db.session.add(question)
            db.session.commit()

            if question_data['question_type'] in ['single-choice', 'multiple-choice']:
                for option_text in question_data.get('options', []):
                    option = Option(question_id=question.id, text=option_text)
                    db.session.add(option)

            for constraint in question_data.get('constraints', []):
                constraint_entry = QuestionConstraint(
                    question_id=question.id,
                    constraint_type=constraint['type'],
                    constraint_value=constraint['value']
                )
                db.session.add(constraint_entry)

        db.session.commit()
        return jsonify({"message": "Survey created successfully", "survey_id": survey.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@survey_bp.route('/', methods=['GET'])
def get_surveys():
    """Fetch all surveys"""
    surveys = Survey.query.all()
    return survey_schema.jsonify(surveys)

@survey_bp.route('/<int:survey_id>', methods=['GET'])
def get_survey(survey_id):
    """Fetch a specific survey by ID"""
    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({"error": "Survey not found."}), 404
    return survey_schema.jsonify(survey)


@survey_bp.route('/<int:survey_id>', methods=['PUT'])
def update_survey(survey_id):
    """Update an existing survey, including questions and options."""
    data = request.json
    survey = Survey.query.get(survey_id)
    
    if not survey:
        return jsonify({"error": "Survey not found."}), 404

    # Update the survey's title and description
    survey.title = data.get('title', survey.title)
    survey.description = data.get('description', survey.description)

    # Handle updating the questions
    if 'questions' in data:
        # Get all the existing questions for the survey
        existing_question_ids = [q.id for q in survey.questions]
        updated_question_ids = []

        for question_data in data['questions']:
            question_id = question_data.get('id')

            if question_id:
                # Check if the question already exists
                if question_id in existing_question_ids:
                    # Update existing question
                    question = Question.query.get(question_id)
                    question.text = question_data.get('text', question.text)
                    question.question_type = question_data.get('question_type', question.question_type)
                    question.is_required = question_data.get('is_required', question.is_required)
                    question.default_value = question_data.get('default_value', question.default_value)

                    # Handle options for the question
                    if question.question_type in ['single-choice', 'multiple-choice']:
                        # Remove existing options if any
                        Option.query.filter_by(question_id=question.id).delete()
                        db.session.commit()

                        # Add the new options
                        for option_text in question_data.get('options', []):
                            option = Option(question_id=question.id, text=option_text)
                            db.session.add(option)

                    # Handle constraints for the question
                    if 'constraints' in question_data:
                        # Remove existing constraints if any
                        QuestionConstraint.query.filter_by(question_id=question.id).delete()
                        db.session.commit()

                        # Add the new constraints
                        for constraint in question_data.get('constraints', []):
                            constraint_entry = QuestionConstraint(
                                question_id=question.id,
                                constraint_type=constraint['type'],
                                constraint_value=constraint['value']
                            )
                            db.session.add(constraint_entry)
                else:
                    # Add new question if the question doesn't already exist
                    question = Question(
                        survey_id=survey.id,
                        text=question_data['text'],
                        question_type=question_data['question_type'],
                        is_required=question_data.get('is_required', True),
                        default_value=question_data.get('default_value')
                    )
                    db.session.add(question)
                    db.session.commit()

                    # Handle options for the new question
                    if question.question_type in ['single-choice', 'multiple-choice']:
                        for option_text in question_data.get('options', []):
                            option = Option(question_id=question.id, text=option_text)
                            db.session.add(option)

                    # Handle constraints for the new question
                    if 'constraints' in question_data:
                        for constraint in question_data.get('constraints', []):
                            constraint_entry = QuestionConstraint(
                                question_id=question.id,
                                constraint_type=constraint['type'],
                                constraint_value=constraint['value']
                            )
                            db.session.add(constraint_entry)

            updated_question_ids.append(question.id)

        # Delete questions that were removed (questions not in the request)
        for existing_question in survey.questions:
            if existing_question.id not in updated_question_ids:
                db.session.delete(existing_question)

        db.session.commit()

    try:
        db.session.commit()
        return jsonify({"message": "Survey updated successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500



@survey_bp.route('/<int:survey_id>', methods=['DELETE'])
def delete_survey(survey_id):
    """Delete a survey"""
    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({"error": "Survey not found."}), 404

    try:
        db.session.delete(survey)
        db.session.commit()
        return jsonify({"message": "Survey deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500



@survey_bp.route('/<int:survey_id>/answers', methods=['POST'])
def submit_survey_answers(survey_id):
    data = request.json
    if not data or 'answers' not in data:
        return jsonify({"error": "Invalid request. 'answers' field is required."}), 400

    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({"error": "Survey not found."}), 404

    try:
        for answer_data in data['answers']:
            question_id = answer_data.get('question_id')
            question = Question.query.filter_by(id=question_id, survey_id=survey_id).first()

            if not question:
                return jsonify({"error": f"Question with ID {question_id} not found in this survey."}), 404

            if question.question_type == 'file' or question.question_type == 'image':
                if 'answer_file' not in answer_data:
                    return jsonify({"error": f"File upload is required for question ID {question_id}."}), 400
                file = answer_data['answer_file']
                if not allowed_file(file):
                    return jsonify({"error": "File type not allowed."}), 400
                filename = secure_filename(file)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                # Assuming the file has been saved to the correct location
            else:
                file_path = None

            answer = Answer(
                survey_id=survey_id,
                question_id=question_id,
                answer_text=answer_data.get('answer_text'),
                answer_file=file_path
            )
            db.session.add(answer)

        db.session.commit()
        return jsonify({"message": "Survey answers submitted successfully."}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@survey_bp.route('/<int:survey_id>/answers', methods=['GET'])
def get_answers(survey_id):
    """Fetch all answers for a specific survey"""
    survey = Survey.query.get_or_404(survey_id)
    answers = Answer.query.filter_by(survey_id=survey_id).all()
    return answer_schema.jsonify(answers)

@survey_bp.route('/<int:survey_id>/answers/<int:answer_id>', methods=['GET'])
def get_answer(survey_id, answer_id):
    """Fetch a specific answer for a survey"""
    survey = Survey.query.get_or_404(survey_id)
    answer = Answer.query.filter_by(survey_id=survey_id, id=answer_id).first()
    if not answer:
        return jsonify({"error": "Answer not found."}), 404
    return answer_schema.jsonify(answer)

@survey_bp.route('/<int:survey_id>/answers/<int:answer_id>', methods=['PUT'])
def update_answer(survey_id, answer_id):
    """Update a specific answer for a survey"""
    data = request.json
    answer = Answer.query.filter_by(survey_id=survey_id, id=answer_id).first()
    if not answer:
        return jsonify({"error": "Answer not found."}), 404

    # Update the fields with the provided data
    answer.answer_text = data.get('answer_text', answer.answer_text)
    answer.answer_file = data.get('answer_file', answer.answer_file)

    try:
        db.session.commit()
        return jsonify({"message": "Answer updated successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@survey_bp.route('/<int:survey_id>/answers/<int:answer_id>', methods=['DELETE'])
def delete_answer(survey_id, answer_id):
    """Delete a specific answer for a survey"""
    answer = Answer.query.filter_by(survey_id=survey_id, id=answer_id).first()
    if not answer:
        return jsonify({"error": "Answer not found."}), 404

    try:
        db.session.delete(answer)
        db.session.commit()
        return jsonify({"message": "Answer deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500



@survey_bp.route('/<int:survey_id>/question', methods=['POST'])
def add_or_update_question(survey_id):
    data = request.json
    if not data or 'text' not in data or 'question_type' not in data:
        return jsonify({"error": "Invalid request. 'text' and 'question_type' are required."}), 400

    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({"error": "Survey not found."}), 404

    question = Question(
        survey_id=survey_id,
        text=data['text'],
        question_type=data['question_type'],
        is_required=data.get('is_required', True),
        default_value=data.get('default_value')
    )
    db.session.add(question)

    db.session.commit()

    # Handle options if present
    for option_text in data.get('options', []):
        option = Option(question_id=question.id, text=option_text)
        db.session.add(option)

    # Handle constraints if present
    for constraint in data.get('constraints', []):
        constraint_entry = QuestionConstraint(
            question_id=question.id,
            constraint_type=constraint['type'],
            constraint_value=constraint['value']
        )
        db.session.add(constraint_entry)

    db.session.commit()

    return jsonify({"message": "Question added/updated successfully.", "question_id": question.id}), 201


@survey_bp.route('/<int:survey_id>/question/<int:question_id>', methods=['PUT'])
def update_question(survey_id, question_id):
    data = request.json
    question = Question.query.filter_by(id=question_id, survey_id=survey_id).first()

    if not question:
        return jsonify({"error": "Question not found."}), 404

    if 'text' in data:
        question.text = data['text']
    if 'question_type' in data:
        question.question_type = data['question_type']
    if 'is_required' in data:
        question.is_required = data['is_required']
    if 'default_value' in data:
        question.default_value = data.get('default_value')

    db.session.commit()

    # Update options if present
    if 'options' in data:
        # Remove existing options
        Option.query.filter_by(question_id=question.id).delete()
        for option_text in data['options']:
            option = Option(question_id=question.id, text=option_text)
            db.session.add(option)

    # Update constraints if present
    if 'constraints' in data:
        # Remove existing constraints
        QuestionConstraint.query.filter_by(question_id=question.id).delete()
        for constraint in data['constraints']:
            constraint_entry = QuestionConstraint(
                question_id=question.id,
                constraint_type=constraint['type'],
                constraint_value=constraint['value']
            )
            db.session.add(constraint_entry)

    db.session.commit()

    return jsonify({"message": "Question updated successfully."}), 200


@survey_bp.route('/<int:survey_id>/question/<int:question_id>', methods=['DELETE'])
def delete_question(survey_id, question_id):
    question = Question.query.filter_by(id=question_id, survey_id=survey_id).first()

    if not question:
        return jsonify({"error": "Question not found."}), 404

    try:
        db.session.delete(question)
        db.session.commit()
        return jsonify({"message": "Question deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@survey_bp.route('/<int:survey_id>/question/<int:question_id>/option', methods=['POST'])
def add_option_to_question(survey_id, question_id):
    data = request.json
    if 'text' not in data:
        return jsonify({"error": "'text' field is required for option."}), 400

    question = Question.query.filter_by(id=question_id, survey_id=survey_id).first()

    if not question:
        return jsonify({"error": "Question not found."}), 404

    option = Option(question_id=question.id, text=data['text'])
    db.session.add(option)
    db.session.commit()

    return jsonify({"message": "Option added successfully.", "option_id": option.id}), 201


@survey_bp.route('/<int:survey_id>/question/<int:question_id>/option/<int:option_id>', methods=['DELETE'])
def delete_option_from_question(survey_id, question_id, option_id):
    option = Option.query.filter_by(id=option_id, question_id=question_id).first()

    if not option:
        return jsonify({"error": "Option not found."}), 404

    try:
        db.session.delete(option)
        db.session.commit()
        return jsonify({"message": "Option deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
