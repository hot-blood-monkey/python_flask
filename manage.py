import os

from app import create_app,db
from app.models import User, Role
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=True

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)

@manager.command
def test():
    """run the unit test"""
    import unittest
    tests = unittest.TestLoader().discover('test')
    unittest.TextTestRunner(verbosity=2).run(tests)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)



if __name__ == '__main__':
    manager.run()


