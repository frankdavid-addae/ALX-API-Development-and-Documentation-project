import os
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    # Retrieve all categories
    @app.route('/categories', methods=['GET'])
    def get_categories():
        try:
            categories = Category.query.all()
            categories = [category.format() for category in categories]
            categories_dict = {}
            for category in categories:
                categories_dict[category['id']] = category['type']

            return jsonify({
                'success': True,
                'categories': categories_dict
            })
        except:
            abort(422)

    # Retrieve all questions
    @app.route('/questions', methods=['GET'])
    def get_questions():
        try:
            questions = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, questions)

            # Create a dictionary for the response containing the questions and categories
            categories = Category.query.all()

            categories_dict = {}

            for category in categories:
                categories_dict[category.id] = category.type
            
            categories = [category.format() for category in categories]
            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(questions),
                'categories': categories_dict,
                'current_category': None
            })
        except:
            abort(422)

    # Delete question
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.get(question_id)
            if question is None:
                abort(404)
            question.delete()
            questions = Question.query.all()
            current_questions = paginate_questions(request, questions)
            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(questions)
            })
        except:
            abort(422)

    # Create new question
    @app.route('/questions', methods=['POST'])
    def create_question():
        try:
            data = request.get_json()
            question = data.get('question', None)
            answer = data.get('answer', None)
            category = data.get('category', None)
            difficulty = data.get('difficulty', None)
            search = data.get('searchTerm', None)

            if search:
                questions = Question.query.filter(Question.question.ilike(f'%{search}%')).all()

                if len(questions) == 0:
                    abort(404)
            
                current_questions = paginate_questions(request, questions)
                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(questions)
                })
            else:
                # question = Question(question=question, answer=answer, category=category, difficulty=difficulty)
                question = Question(question, answer, category, difficulty)
                question.insert()
                questions = Question.query.all()
                current_questions = paginate_questions(request, questions)
                return jsonify({
                    'success': True,
                    'created': question.id,
                    'questions': current_questions,
                    'total_questions': len(questions)
                })
        except:
            abort(422)

    # Retrieve questions by category
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        try:
            questions = Question.query.filter(Question.category == category_id).all()
            current_questions = paginate_questions(request, questions)
            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(questions)
            })
        except:
            abort(422)

    # Retrieve a random question
    @app.route('/quizzes', methods=['POST'])
    def get_random_question():
        try:
            data = request.get_json()
            previous_questions = data.get('previous_questions', None)
            category = data.get('quiz_category', None)
            if category['id'] == 0:
                questions = Question.query.all()
            else:
                questions = Question.query.filter(Question.category == category['id']).all()
            if len(previous_questions) == 0:
                question = random.choice(questions)
            else:
                question = random.choice(questions)
                while question.id in previous_questions:
                    question = random.choice(questions)
            return jsonify({
                'success': True,
                'question': question.format()
            })
        except:
            abort(422)

    
    # Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource not found"
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method not allowed"
        }), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable"
        }), 422
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad Request"
        }), 400

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error"
        }), 500

    return app

