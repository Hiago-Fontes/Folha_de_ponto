from app import app
from extensions import db
from models import Employee

# O script já importa `app` (entrypoint). A alteração principal no projeto foi mover a
# instância `db = SQLAlchemy()` para `extensions.py` e chamar `db.init_app(app)` em `app.py`.
with app.app_context():
    db.create_all()
    emp = Employee(name='TEST_CHECK', setor='diurno')
    db.session.add(emp)
    db.session.commit()
    found = Employee.query.filter_by(name='TEST_CHECK').first()
    print('found:', found)
    # cleanup
    db.session.delete(found)
    db.session.commit()
    print('teste concluido')
