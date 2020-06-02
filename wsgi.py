"""
The WSGI portal for BlockPy Server
"""

from main import create_app

application = create_app()

if __name__ == '__main__':
    application.run()
