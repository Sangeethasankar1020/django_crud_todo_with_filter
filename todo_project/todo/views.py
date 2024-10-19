from datetime import datetime
from django.shortcuts import render, redirect
from pymongo import MongoClient
from bson.objectid import ObjectId

# MongoDB 
client = MongoClient('mongodb://localhost:27017/')
db = client['todo_db']
todos_collection = db['todos']

STATUS_OPTIONS = ['pending', 'completed', 'in progress']

def home(request):
    status_filter = request.GET.get('status', 'all')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    time_from = request.GET.get('time_from', '')
    time_to = request.GET.get('time_to', '')

    query = {}

    # Filter
    if status_filter and status_filter != 'all':
        query['status'] = status_filter

    # Date  filter
    if date_from and date_to:
        query['datetime'] = {
            '$gte': f'{date_from}T00:00:00',
            '$lte': f'{date_to}T23:59:59'
        }

    # Time  filter
    if time_from and time_to:
        time_from_str = time_from.replace(':', '')
        time_to_str = time_to.replace(':', '')

        # Filter by combining date and time
        if 'datetime' in query:
            query['datetime']['$regex'] = f'T({time_from_str}|{time_to_str})'
        else:
            query['datetime'] = {'$regex': f'T({time_from_str}|{time_to_str})'}

    tasks = list(todos_collection.find(query))

    for task in tasks:
        task['id'] = str(task['_id'])
        dt = datetime.fromisoformat(task['datetime'])
        task['date'] = dt.date().isoformat()
        task['time'] = dt.time().isoformat()

    return render(request, 'home.html', {'tasks': tasks, 'status_options': STATUS_OPTIONS})


def add_task(request):
    if request.method == 'POST':
        task_name = request.POST.get('name')
        task_description = request.POST.get('description')
        task_status = request.POST.get('status', 'pending')
        task_datetime = datetime.now().isoformat()

        todos_collection.insert_one({
            'name': task_name,
            'description': task_description,
            'status': task_status,
            'datetime': task_datetime,
            'created_at': datetime.now()
        })
        return redirect('home')

    return redirect('home')  


def update_task(request, task_id):
    task = todos_collection.find_one({'_id': ObjectId(task_id)})

    if request.method == 'POST':
        task_name = request.POST.get('name')
        task_description = request.POST.get('description')
        task_status = request.POST.get('status')

        todos_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {
                'name': task_name,
                'description': task_description,
                'status': task_status,
            }}
        )
        return redirect('home')

    task['id'] = str(task['_id'])
    return render(request, 'update_task.html', {'task': task, 'status_options': STATUS_OPTIONS})


def delete_task(request, task_id):
    todos_collection.delete_one({'_id': ObjectId(task_id)})
    return redirect('home')
