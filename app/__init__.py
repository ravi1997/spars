import os
from flask import Flask, jsonify, send_from_directory
from app.extensions import db,ma,migrate
from app.config import DevelopmentConfig,ProductionConfig,TestingConfig

from flask_restx import Api, Resource, fields

def create_app():
    myapp = Flask(__name__)

    # Load configuration
    ENV = os.getenv('FLASK_ENV', 'development')  # Set this environment variable to switch environments
    if ENV == 'production':
        myapp.config.from_object(ProductionConfig)
    elif ENV == 'testing':
        myapp.config.from_object(TestingConfig)
    else:
        myapp.config.from_object(DevelopmentConfig)


    if myapp.config['SWAGGER_SERVICE']:
        api = Api(myapp, version="1.0", title="Survey API",
          description="API documentation for the Survey project",
          security="BearerAuth",  # Default security scheme for the API
            authorizations={
                "BearerAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "Authorization",
                    "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer <your_token>'"
                }
            },)

        from flask_swagger_ui import get_swaggerui_blueprint

        SWAGGER_URL = '/spars/swagger'  # URL for exposing Swagger UI
        API_URL = '/spars/swagger.json'  # Path to the API documentation in JSON format

        swaggerui_blueprint = get_swaggerui_blueprint(
            SWAGGER_URL,
            API_URL,
            config={'app_name': "Survey API"}
        )

        myapp.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
        
        # Serve Swagger UI HTML from the 'static' directory
        @myapp.route('/spars/swagger_ui')
        def swagger_ui():
            return send_from_directory(os.path.join(myapp.root_path, 'static'), 'swagger_ui.html')



    db.init_app(myapp)
    ma.init_app(myapp)
    migrate.init_app(myapp,db)

    from app.db_init import init_db_command

    myapp.cli.add_command(init_db_command)


    from app.model import User

    if myapp.config['SWAGGER_SERVICE']:
        # Namespace for modular organization
        from app.routes.auth import auth_ns
        from app.routes.survey import survey_ns

        api.add_namespace(survey_ns, path='/spars/survey')
        api.add_namespace(auth_ns, path='/spars/auth')


    return myapp