from flask import Flask, render_template, request, redirect, url_for, session
from sympy import Symbol, sympify, limit, oo, S
import sympy as sp
import traceback
import re

app = Flask(__name__)
app.secret_key = 'sushi'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'clear_all' in request.form:
            session.clear()
            return redirect(url_for('index'))

        try:
            expression = request.form['expression']
            variable = request.form['variable']
            to_value = request.form['to_value']
            limit_type = request.form['limit_type']

            session['expression'] = expression
            session['variable'] = variable
            session['to_value'] = to_value

            expression = expression.replace('√', 'sqrt')
            expression = expression.replace('^', '**')
            expression = expression.replace('e', 'E')

            expression = re.sub(r'(\d)([a-zA-Z\(])', r'\1*\2', expression)
            expression = re.sub(r'(\))(\d|[a-zA-Z\(])', r'\1*\2', expression)

            x = Symbol(variable)

            to_value_sym = {'∞': oo, '-∞': -oo}.get(to_value.strip(), to_value)
            to_value_sym = sympify(to_value_sym)

            expr = sympify(expression, evaluate=False)
            expr_symbols = expr.free_symbols

            if expr_symbols and any(sym.name != variable for sym in expr_symbols):
                raise ValueError(f"Expression contains variables other than '{variable}'.")

            result = limit(expr, x, to_value_sym)
            result = str(result).replace('E', 'e')

            if result in [oo, -oo, S.Infinity, S.NegativeInfinity, S.ComplexInfinity]:
                session['error'] = 'The limit results in infinity or is undefined.'
                session.pop('result', None)
                session.pop('limit_type', None)
            else:
                session['result'] = str(result)
                session['limit_type'] = limit_type
                session.pop('error', None)

                history = session.get('history', [])
                new_entry = {
                    'expression': expression,
                    'variable': variable,
                    'to_value': to_value,
                    'result': str(result)
                }

                history.insert(0, new_entry)
                history = history[:5]

                session['history'] = history

            session['from_post'] = True

        except ZeroDivisionError:
            session['error'] = 'Division by zero is undefined.'
            session.pop('result', None)
            session.pop('limit_type', None)
            session['from_post'] = True

        except sp.SympifyError:
            session['error'] = 'Invalid input format. Please check your expression.'
            session.pop('result', None)
            session.pop('limit_type', None)
            session['from_post'] = True

        except ValueError as ve:
            session['error'] = str(ve)
            session.pop('result', None)
            session.pop('limit_type', None)
            session['from_post'] = True

        except Exception:
            session['error'] = 'Server error occurred. Please try again later.'
            session.pop('result', None)
            session.pop('limit_type', None)
            session['from_post'] = True
            traceback.print_exc()

        return redirect(url_for('index'))

    else:
        if not session.pop('from_post', False):
            session.clear()

    result = session.get('result')
    limit_type = session.get('limit_type')
    error = session.get('error')
    expression = session.get('expression', '')
    variable = session.get('variable', '')
    to_value = session.get('to_value', '')

    return render_template('index.html',
                           result=result,
                           error=error,
                           limit_type=limit_type,
                           expression=expression,
                           variable=variable,
                           to_value=to_value)

if __name__ == '__main__':
    app.run(debug=True)