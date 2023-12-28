from flask import Flask, request, jsonify
from flask.wrappers import Response

app = Flask(__name__)


employees = []
tasks = []

@app.route('/employee/', methods=['POST'])
def create_employee():
    data = request.json
    employees.append(data)
    return jsonify(data), 201

@app.route('/employee/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    for employee in employees:
        if employee['id'] == employee_id:
            return jsonify(employee)
    return 'Employee not found', 404

@app.route('/task/', methods=['POST'])
def create_task():
    data = request.json
    tasks.append(data)
    return jsonify(data), 201

@app.route('/assign-task/<int:task_id>/<int:employee_id>', methods=['PUT'])
def assign_task(task_id, employee_id):
    for task in tasks:
        if task['id'] == task_id:
            if 'assigned_to' in task and task['assigned_to'] is not None:
                return 'Task already assigned', 400
            for employee in employees:
                if employee['id'] == employee_id:
                    if employee['role'] != 'Lead':
                        task['assigned_to'] = employee_id
                        employee.setdefault('tasks', []).append(task)
                        return jsonify(task), 200
            return 'Employee not found', 404
    return 'Task not found', 404

@app.route('/unassign-task/<int:task_id>', methods=['PUT'])
def unassign_task(task_id):
    for task in tasks:
        if task['id'] == task_id:
            task['assigned_to'] = None
            for employee in employees:
                employee['tasks'] = [t for t in employee.get('tasks', []) if t['id'] != task_id]
            return jsonify(task), 200
    return 'Task not found', 404

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
