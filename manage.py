"""
Various command-line utilities for controlling the application.
"""
import os
import json
import click
from flask.cli import FlaskGroup
from flask import current_app

from main import create_app


def create_cli_app(info):
    """
    Create a special version of the create_app function that has an unused `info` parameter.
    :param info:
    :return:
    """
    return create_app()


@click.group(cls=FlaskGroup, create_app=create_cli_app)
@click.option('--debug', is_flag=True, default=False)
def cli(debug):
    """
    Create the `cli` function that will manage all the custom scripts.
    :param debug:
    :return:
    """
    if debug:
        os.environ['FLASK_DEBUG'] = '1'
    os.environ['FLASK_ENV'] = 'development'


@cli.command('print_hello')
def hello():
    """
    Example command
    :return:
    """
    print("Hello world")


@cli.command('build_api_docs')
def build_api_docs():
    """
    Example command
    :return:
    """
    click.echo("Generating the latest API documentation")
    #docs = current_app.config['SWAGGER'].spec.to_dict()
    from controllers import generator, registry
    with current_app.app_context():
        docs = generator.generate(registry)
    click.echo("Writing the API to a file")
    with open(current_app.config['API_DOCUMENTATION_PATH'], 'w') as f:
        json.dump(docs, f, indent=2)


if __name__ == '__main__':
    cli()
