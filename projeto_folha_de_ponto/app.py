from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import os
from utils.gerar_relatorio import gerar_pdf_relatorio
from extensions import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'troque_por_uma_chave_secreta'

# initialize db with app to avoid circular imports
db.init_app(app)


from models import Employee, TimeEntry


# Cria banco se não existir
with app.app_context():
    db.create_all()


# Map tipo de escala para horários esperados (12h)
ESCALAS = {
'diurno': {'entrada': time(7,0), 'saida': time(19,0)},
'noturno': {'entrada': time(19,0), 'saida': time(7,0)} # saída no dia seguinte
}


@app.route('/')
def index():
    employees = Employee.query.order_by(Employee.name).all()
    return render_template('index.html', employees=employees, escalas=ESCALAS)


@app.route('/funcionarios', methods=['GET', 'POST'])
def funcionarios():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        setor = request.form.get('setor', '').strip()
        if not nome:
            flash('Nome é obrigatório', 'danger')
            return redirect(url_for('funcionarios'))
        # evita duplicatas exatas por nome
        existing = Employee.query.filter_by(name=nome).first()
        if existing:
            flash('Funcionário já cadastrado', 'warning')
            return redirect(url_for('funcionarios'))
        emp = Employee(name=nome, setor=setor)
        try:
            db.session.add(emp)
            db.session.commit()
            flash('Funcionário cadastrado', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar funcionário: {}'.format(str(e)), 'danger')
        return redirect(url_for('funcionarios'))
    else:
        employees = Employee.query.order_by(Employee.name).all()
        return render_template('funcionarios.html', employees=employees)


@app.route('/registrar', methods=['GET','POST'])
def registrar():
    employees = Employee.query.order_by(Employee.name).all()
    if request.method == 'POST':
        emp_id_raw = request.form.get('employee_id')
        tipo = request.form.get('tipo', 'entrada') # 'entrada' ou 'saida'
        if not emp_id_raw:
            flash('Funcionário não selecionado', 'danger')
            return redirect(url_for('registrar'))
        try:
            emp_id = int(emp_id_raw)
        except ValueError:
            flash('ID de funcionário inválido', 'danger')
            return redirect(url_for('registrar'))

        emp = Employee.query.get(emp_id)
        if not emp:
            flash('Funcionário não encontrado', 'danger')
            return redirect(url_for('registrar'))

        now = datetime.now()

        # valida sequência: evita duas entradas seguidas ou duas saídas seguidas
        last_entry = TimeEntry.query.filter_by(employee_id=emp_id).order_by(TimeEntry.timestamp.desc()).first()
        if last_entry:
            if last_entry.entry_type == tipo:
                flash(f'Registro inválido: último registro já é "{tipo}"', 'danger')
                return redirect(url_for('registrar'))

        entry = TimeEntry(employee_id=emp_id, entry_type=tipo, timestamp=now)
        try:
            db.session.add(entry)
            db.session.commit()
            flash(f'{tipo.capitalize()} registrada com sucesso', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao registrar ponto: {}'.format(str(e)), 'danger')
        return redirect(url_for('registrar', employee_id=emp_id))  # mantém seleção após registrar

    # GET: suporta ?employee_id= para mostrar pontos do funcionário selecionado
    selected_emp = None
    selected_entries = []
    emp_id_param = request.args.get('employee_id')
    if emp_id_param:
        try:
            sel_id = int(emp_id_param)
            selected_emp = Employee.query.get(sel_id)
            if selected_emp:
                selected_entries = TimeEntry.query.filter_by(employee_id=sel_id).order_by(TimeEntry.timestamp.desc()).limit(100).all()
        except Exception:
            selected_emp = None
            selected_entries = []

    return render_template('registrar.html', employees=employees, selected_emp=selected_emp, selected_entries=selected_entries)


@app.route('/relatorio', methods=['GET','POST'])
def relatorio():
    # Formulário simples para gerar relatório
    employees = Employee.query.order_by(Employee.name).all()
    if request.method == 'POST':
        emp_id_raw = request.form.get('employee_id')
        start_raw = request.form.get('start_date')  # esperado 'YYYY-MM-DD'
        end_raw = request.form.get('end_date')      # esperado 'YYYY-MM-DD'

        try:
            emp_id = int(emp_id_raw) if emp_id_raw else None
        except (TypeError, ValueError):
            emp_id = None

        emp = Employee.query.get(emp_id) if emp_id else None
        if not emp:
            flash('Funcionário inválido para relatório', 'danger')
            return redirect(url_for('relatorio'))

        # parse datas com fallback para mês atual
        today = datetime.today()
        try:
            start = datetime.strptime(start_raw, '%Y-%m-%d') if start_raw else today.replace(day=1)
        except Exception:
            start = today.replace(day=1)
        try:
            end = datetime.strptime(end_raw, '%Y-%m-%d') if end_raw else (start + relativedelta(months=1) - timedelta(days=1))
        except Exception:
            end = start + relativedelta(months=1) - timedelta(days=1)

        # chama gerador de pdf (assume-se que retorna caminho para arquivo)
        try:
            pdf_path = gerar_pdf_relatorio(emp, start, end)
            if not pdf_path or not os.path.exists(pdf_path):
                flash('Relatório não foi gerado', 'danger')
                return redirect(url_for('relatorio'))
            return send_file(pdf_path, as_attachment=True)
        except Exception as e:
            flash('Erro ao gerar relatório: {}'.format(str(e)), 'danger')
            return redirect(url_for('relatorio'))

    return render_template('relatorio.html', employees=employees)