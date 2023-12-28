from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
import json

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')  # Update MongoDB URI if necessary
db = client.your_database_name  # Replace with your actual database name
employees_collection = db.employees
tasks_collection = db.tasks

# Helper function to convert ObjectId to str for JSON serialization
def mongo_to_dict(obj):
    try:
        return json.loads(json.dumps(obj, default=lambda o: str(o) if isinstance(o, ObjectId) else o))
    except InvalidId:
        return jsonify({"error": "Invalid ObjectId format"}), 400

@app.route('/employee/', methods=['POST'])
def create_employee():
    data = request.json
    result = employees_collection.insert_one(data)
    data['_id'] = result.inserted_id
    return jsonify(mongo_to_dict(data)), 201

@app.route('/employee/<string:employee_id>', methods=['GET'])
def get_employee(employee_id):
    employee = employees_collection.find_one({'id': employee_id})
    if employee:
        return jsonify(mongo_to_dict(employee))
    return 'Employee not found', 404

@app.route('/task/', methods=['POST'])
def create_task():
    data = request.json
    result = tasks_collection.insert_one(data)
    data['_id'] = result.inserted_id
    return jsonify(mongo_to_dict(data)), 201

@app.route('/assign-task/<string:task_id>/<string:employee_id>', methods=['PUT'])
def assign_task(task_id, employee_id):
    try:
        # Find the task by its string ID
        task = tasks_collection.find_one({'id': task_id})
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        # Check if the task is already assigned
        if task.get('assigned_to') is not None:
            return jsonify({'error': 'Task already assigned'}), 400

        # Find the employee by its string ID
        employee = employees_collection.find_one({'id': employee_id})
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        # Check if the employee is not a Lead
        if employee.get('role') == 'Boss':
            return jsonify({'error': 'Cannot assign task to Lead'}), 400

        # Assign the task to the employee
        tasks_collection.update_one({'id': task_id}, {'$set': {'assigned_to': f"{employee_id} - {employee.get('name')}"}})
        #tasks_collection.update_one({'id': task_id}, {'$set': {'assigned_to': {'id': employee_id, 'name': employee.get('name')}}})
        employees_collection.update_one({'id': employee_id}, {'$push': {'tasks': task['_id']}})

        # Retrieve the updated task
        updated_task = tasks_collection.find_one({'id': task_id})

        # Return the updated task with the assigned employee's information
        return jsonify(mongo_to_dict(updated_task)), 200

    except Exception as e:
        # If any error occurs, return an error message
        return jsonify({'error': str(e)}), 500


@app.route('/unassign-task/<string:task_id>', methods=['PUT'])
def unassign_task(task_id):
    task = tasks_collection.find_one({'id': task_id})
    if task:
        tasks_collection.update_one({'id': task_id}, {'$set': {'assigned_to': None}})
        task['assigned_to'] = None
        employees_collection.update_many({}, {'$pull': {'tasks': {'id': task_id}}})
        return jsonify(mongo_to_dict(task)), 200
    return 'Task not found', 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
