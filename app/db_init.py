from datetime import datetime
from flask import Flask
from flask.cli import with_appcontext
import click
from app.extensions import db
from app.model import User, Role, Survey, Question, Option, QuestionConstraint


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Initialize the database and populate it with default values."""
    click.echo("Dropping and recreating all tables...")
    db.drop_all()
    db.create_all()
    click.echo("Database initialized.")

    # Default roles
    roles = ["SUPERADMIN", "ADMIN", "TESTER"]
    for role_name in roles:
        role = Role(name=role_name)
        db.session.add(role)

    db.session.commit()

    # Default users
    user1 = User(
        first_name="Ravinder",
        middle_name="",
        last_name="Singh",
        dob= datetime.fromisoformat("1997-02-27"),
        mobile="9899378106",
        aadhar="755598103347",
        gender="Male",
    )
    db.session.add(user1)  # Add the user first

    admin_role = Role.query.filter_by(name="ADMIN").first()
    if admin_role:
        user1.roles.append(admin_role)  # Modify relationships after adding to session
    
    superadmin_role = Role.query.filter_by(name="SUPERADMIN").first()
    if superadmin_role:
        user1.roles.append(superadmin_role)  # Modify relationships after adding to session


    db.session.commit()
    click.echo("Default values inserted successfully.")
