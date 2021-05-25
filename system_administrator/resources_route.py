from flask import Blueprint,jsonify,request,abort
from app.authentication import require_auth
from app.models.resources import Course,Ministry_Item,Semester,Practical_Experiment,Practical_Item,City,Area
from app.models.evaluate_system import Question
from app.models.users import System_Administrator
from app.component import pagination,PAGE_SHELF,initiate_evaluate_type
import math

resources_route = Blueprint('resources_route',__name__)

########## COURSE ##########

@resources_route.route('/course', methods=['POST'])
@require_auth(['System_Administrator'])
def add_course(payload):

    course_data = request.get_json()

    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')    
    course = user.add_course_process(course_data)
    
    course_content = course.format()
    course.append(user) 
    course.close()

    return jsonify({
        'success': True,
        'message': 'تم اضافة المادة بنجاح',
        'course': course_content
    })

'''
Request: 
    {
"name": "CPIT-202"
}
Response:
{
    "id": 25,
    "message": "تم اضافة المادة بنجاح",
    "success": true
}
'''

@resources_route.route('/course', methods=['PATCH'])
@require_auth(['System_Administrator'])
def modify_course(payload):

    course_data = request.get_json()
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    course = user.edit_course(course_data)
    course_content = course.format_detail()
    
    return jsonify({
        'success': True,
        'message': 'تم تعديل معلومات المادة بنجاح',
        'course': course_content
    })

'''
Request:
    {
"newName": "CPIT-202",
"id": "13"
}
Response:
{
    "message": "تم تعديل المادة بنجاح",
    "success": true
}
'''

@resources_route.route('/course/<int:course_id>', methods=['DELETE'])
@require_auth(['System_Administrator'])
def delete_course(payload,course_id):

    course = Course.query.filter_by(id=course_id).first_or_404(description='لا توجد مادة بهذا الرقم')
    course.delete()

    return jsonify({
        'message': 'تم حذف المادة بنجاح',
        'success': True
    })

'''
Request: 
route: course/7
Response:
{
    "message": "تم حذف المادة بنجاح",
    "success": true
}
'''

@resources_route.route('/course/<int:course_id>', methods=['GET'])
@require_auth(['System_Administrator'])
def display_course(payload,course_id):

    course = Course.query.filter_by(id=course_id).first_or_404(description='لا توجد مادة بهذا الرقم')

    return jsonify({
        'course': course.format_detail(),
        'success': True
    })

'''
Request: 
route: course/23
Response:
{
    "course": {
        "id": 23,
        "name": "CPIT-121",
        "path": "/course/23",
        "practicalExperiment": []
    },
    "success": true
}
'''

@resources_route.route('/course', methods=['GET'])
@require_auth(['System_Administrator'])
def display_all_course(payload):

    selection = Course.query.order_by(Course.id)
    selection = Course.filtering(request,selection)
    current_content, current_page = pagination(request,selection)
    success = True
    code = 200
    if len(current_content) == 0:
        code = 204
        success = False

    return jsonify({
        'success': success,
        'courses': current_content,
        'totalPages': math.ceil(len(selection)/PAGE_SHELF),
        'currentPage': current_page,
        'error': code
    })

'''
Request: 
para : page=1
Response:
{
    "courses": [
        {
            "id": 15,
            "name": "CPIT-401",
            "path": "/course/15"
        },
        {
            "id": 17,
            "name": "CPIT-402",
            "path": "/course/17"
        },
        {
            "id": 18,
            "name": "CPIT-200",
            "path": "/course/18"
        },
        {
            "id": 19,
            "name": "CPIT-100",
            "path": "/course/19"
        },
        {
            "id": 20,
            "name": "CPIT-305",
            "path": "/course/20"
        },
        {
            "id": 22,
            "name": "CPIT-101",
            "path": "/course/22"
        },
        {
            "id": 23,
            "name": "CPIT-121",
            "path": "/course/23"
        }
    ],
    "current_page": 1,
    "success": true,
    "total_pages": 1
}
'''

########## ITEM ##########

@resources_route.route('/item', methods=['POST'])
@require_auth(['System_Administrator'])
def add_ministry_item(payload):

    item_data = request.get_json()
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    ministry_item = user.add_item(item_data)

    ministry_item.append(user)          

    ministry_item_content = ministry_item.format()
    return jsonify({
        'success': True,
        'message': 'تم اضافة العهدة بنجاح',
        'item': ministry_item_content
    })

'''
Request:
{
    "name": "LOOP",
    "unit": "gram"
}
Response:
{
    "id": 15,
    "message": "تم اضافة العهدة بنجاح",
    "success": true
}
'''

@resources_route.route('/item', methods=['PATCH'])
@require_auth(['System_Administrator'])
def modify_ministry_item(payload):

    item_data = request.get_json()
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    ministry_item = user.edit_item(item_data)
    
    ministry_item_content = ministry_item.format()

    return jsonify({
        'success': True,
        'message': 'تم تعديل العهدة بنجاح',
        'item': ministry_item_content
    })

'''
Request:
{
    "name": "AB",
    "unit": "GRAm",
    "id": 6
}
Response:
{
    "message": "تم تعديل معلومات العهدة بنجاح",
    "success": true
}
'''

@resources_route.route('/item/<int:item_id>', methods=['DELETE'])
@require_auth(['System_Administrator'])
def delete_ministry_item(payload,item_id):

    item = Ministry_Item.query.filter_by(id=item_id).first_or_404(description='لا توجد عهدة بهذا الرقم')
    item.delete()

    return jsonify({
        'message': 'تم حذف العهدة بنجاح',
        'success': True
    })

'''
Request: 
route: item/2
Response:
{
    "message": "تم حذف العهدة بنجاح",
    "success": true
}
'''

@resources_route.route('/item/<int:item_id>', methods=['GET'])
@require_auth(['System_Administrator'])
def display_ministry_item(payload,item_id):

    item = Ministry_Item.query.filter_by(id=item_id).first_or_404(description='لا توجد عهدة بهذا الرقم')

    return jsonify({
        'item': item.format(),
        'success': True
        })

'''
Request: 
route: item/4
Response:
{
    "item": {
        "id": 4,
        "name": "A",
        "unit": "GRAM"
    },
    "success": true
}
'''

@resources_route.route('/item', methods=['GET'])
@require_auth(['System_Administrator'])
def display_all_ministry_item(payload):

    selection = Ministry_Item.query.order_by(Ministry_Item.id)
    selection = Ministry_Item.filtering(request,selection)
    current_content, current_page = pagination(request,selection)
    success = True
    code = 200
    if len(current_content) == 0:
        code = 204
        success = False

    
    return jsonify({
        'success': success,
        'items': current_content,
        'totalPages': math.ceil(len(selection)/PAGE_SHELF),
        'currentPage': current_page,
        'error': code
        })

'''
Request: 
para : page=1
Response:
{
    "items": [
        {
            "id": 1,
            "name": "CPIT-444",
            "unit": "GRAM"
        },
        {
            "id": 4,
            "name": "A",
            "unit": "GRAM"
        },
        {
            "id": 5,
            "name": "الزئبق",
            "unit": "GRAM"
        }
    ],
    "success": true,
    "total_pages": 2
}
'''

########## SEMESTER ##########

@resources_route.route('/semester', methods=['POST'])
@require_auth(['System_Administrator'])
def add_semester(payload):

    semester_data = request.get_json()
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    semester = user.add_semester_process(semester_data)
    semester_content = semester.format()

    semester.append(user)
    semester.close()
                
    return jsonify({
        'success': True,
        'message': 'تم اضافة الترم الدراسي بنجاح',
        'semester': semester_content
    })

'''
Request:
{
 "title": "SEM1",
 "startDate": "2/1/2022",
 "endDate": "5/29/2023"
}
Response:
{
    "id": 20,
    "message": "تم اضافة الترم الدراسي بنجاح",
    "success": true
}
'''

@resources_route.route('/semester', methods=['PATCH'])
@require_auth(['System_Administrator'])
def modify_semester(payload):

    semester_data = request.get_json()
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    semester = user.edit_semester(semester_data)
    semester_content = semester.format()
    semester.close()    

    return jsonify({
        'success': True,
        'message': 'تم تعديل الترم الدراسي بنجاح',
        'semester': semester_content
        })

'''
Request:
{
 "title": "SEM112243",
 "startDate": "2/1/2022",
 "endDate": "5/29/2023",
 "id": "20"
}
Response:
{
    "message": "تم تعديل معلومات الترم الدراسي بنجاح",
    "success": true
}
'''

@resources_route.route('/semester/<int:semester_id>', methods=['DELETE'])
@require_auth(['System_Administrator'])
def delete_semester(payload,semester_id):

    semester = Semester.query.filter_by(id=semester_id).first_or_404(description='لا يوجد ترم دراسي بهذا الرقم')
    semester.delete()

    return jsonify({
        'message': 'تم حذف الترم الدراسي بنجاح',
        'success': True
    })

'''
Request: 
route: semester/2
Response:
{
    "message": "تم حذف الترم الدراسي بنجاح",
    "success": true
}
'''

@resources_route.route('/semester/<int:semester_id>', methods=['GET'])
@require_auth(['System_Administrator'])
def get_semester(payload,semester_id):
    
    semester = Semester.query.filter_by(id=semester_id).first_or_404(description='لا يوجد ترم دراسي بهذا الرقم')

    return jsonify({
        'semester': semester.format(),
        'success': True
        })

'''
Request: 
route: semester/2
Response:
{
    "semester": {
        "id": 20,
        "title": "EXP ONE"
    },
    "success": true
}
'''

@resources_route.route('/semester', methods=['GET'])
@require_auth(['System_Administrator'])
def display_all_semester(payload):

    selection = Semester.query.order_by(Semester.id)
    selection = Semester.filtering(request,selection)
    current_content, current_page = pagination(request,selection)
    success = True
    code = 200
    if len(current_content) == 0:
        code = 204
        success = False

    
    return jsonify({
        'success': success,
        'semesters': current_content,
        'totalPages': math.ceil(len(selection)/PAGE_SHELF),
        'currentPage': current_page,
        'error': code
        })

'''
Request:
para : page=1
Response:
{
    "current_page": 1,
    "semesters": [
        {
            "end_date": "Mon, 29 May 2023 00:00:00 GMT",
            "id": 21,
            "path": "/semester/21",
            "start_date": "Tue, 01 Feb 2022 00:00:00 GMT",
            "title": "SEM112243"
        }
    ],
    "success": true,
    "total_pages": 1
}
'''

########## EXPERIMENT ##########

@resources_route.route('/experiment', methods=['POST'])
@require_auth(['System_Administrator'])
def add_experiment(payload):

    experiment_data = request.get_json()
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')

    practical_experiment = user.add_experiment_process(experiment_data)
    practical_experiment_id = practical_experiment.id
    #add the user, whos add the experiment
    practical_experiment.append(user)
   
    practical_experiment.close()
    return jsonify({
        'success': True,
        'message': 'تم اضافة التجربة العملية بنجاح',
        'id': practical_experiment_id
    })

'''
Request:
{
    "items": [
        {
            "value": 14,
            "label": "C"
        }
    ],
    "title": "EXP YY",
    "courseId": "15"
}
Response:
{
    "id": 36,
    "message": "تم اضافة التجربة العملية بنجاح",
    "success": true
}
'''

@resources_route.route('/experiment', methods=['PATCH'])
@require_auth(['System_Administrator'])
def modify_experiment(payload):

    experiment_data = request.get_json()
    #check from the user
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    #edit the experiment and return the object
    practical_experiment = user.edit_experiment(experiment_data)
    #print the response
    experiment_response = practical_experiment.format_detail()
    practical_experiment.close()

    return jsonify({
        'success': True,
        'message': 'تم تعديل معلومات التجربة العملية بنجاح',
        'experiment':experiment_response
        })

'''
Request:
    {
"title": "EXP xxx",
"courseId": 17,
"id": "52",
"items": [
        {
            "value": 10,
            "label": "AB",
            "status": "add"
        },
               {
            "value": 11,
            "label": "A",
            "status": "add"
        }
        ]
}
Response:
{
    "message": "تم تعديل التجربة العملية بنجاح",
    "success": true
}
'''

@resources_route.route('/experiment/<int:experiment_id>', methods=['DELETE'])
@require_auth(['System_Administrator'])
def delete_experiment(payload,experiment_id):

    practical_experiment = Practical_Experiment.query.filter_by(id=experiment_id).first_or_404(description='لا توجد تجربة علمية بهذا الرقم')
    practical_experiment.delete()

    return jsonify({
        'message': 'تم حذف التجربة العملية بنجاح',
        'success': True
    })

'''
Request:
route: experiment/2
Response:
{
    "message": "تم حذف التجربة العملية بنجاح",
    "success": true
}
'''

@resources_route.route('/experiment/<int:experiment_id>', methods=['GET'])
@require_auth(['System_Administrator'])
def get_experiment(payload,experiment_id):
    
    practical_experiment = Practical_Experiment.query.filter_by(id=experiment_id).first_or_404(description='لا توجد تجربة علمية بهذا الرقم')

    return jsonify({
        'experiment': practical_experiment.format_detail(),
        'success': True
        })

'''
Request: 
route: experiment/49
Response:
{
    "experiment": {
        "course": {
            "label": "CPIT-401",
            "value": 15
        },
        "id": 49,
        "items": [
            {
                "label": "C-gram",
                "value": 14
            }
        ],
        "title": "EXP YY"
    },
    "success": true
}
'''

@resources_route.route('/experiment', methods=['GET'])
@require_auth(['System_Administrator'])
def display_all_experiment(payload):

    selection = Practical_Experiment.query.order_by(Practical_Experiment.id)
    selection = Practical_Experiment.filtering(request,selection)
    
    current_content, current_page = pagination(request,selection)

    success = True
    code = 200
    if len(current_content) == 0:
        code = 204
        success = False

    course_selection = Course.query.order_by(Course.id).all()
    course_content = [s.format_create() for s in course_selection]
    
    return jsonify({
        'success': success,
        'experiments': current_content,
        'courses': course_content,
        'totalPages': math.ceil(len(selection)/PAGE_SHELF),
        'currentPage': current_page,
        'error': code
        })

'''
Request:
para : page=1
Response:
{
    "current_page": 1,
    "experiments": [
        {
            "courseName": "CPIT-401",
            "id": 49,
            "path": "/experiment/49",
            "title": "EXP YY"
        },
        {
            "courseName": "CPIT-401",
            "id": 50,
            "path": "/experiment/50",
            "title": "EXP XX"
        },
        {
            "courseName": "CPIT-402",
            "id": 52,
            "path": "/experiment/52",
            "title": "EXP xxx"
        }
    ],
    "success": true,
    "total_pages": 1
}
'''

@resources_route.route('/experiment/create-requirements', methods=['GET'])
@require_auth(['System_Administrator'])
def create_experiment(payload):

    course_selection = Course.query.order_by(Course.id).all()
    course_content = [s.format_create() for s in course_selection]

    item_selection = Ministry_Item.query.filter_by(safety = False).all()
    item_content = [s.format_create() for s in item_selection]

    return jsonify({
        'items': item_content,
        'courses': course_content,
        'success': True
        })

'''
Request: 
 use route
Response:
{
    "courses": [
        {
            "label": "CPIT-401",
            "value": 15
        },
        {
            "label": "CPIT-402",
            "value": 17
        },
        {
            "label": "CPIT-200",
            "value": 18
        },
        {
            "label": "CPIT-100",
            "value": 19
        },
        {
            "label": "CPIT-305",
            "value": 20
        },
        {
            "label": "CPIT-101",
            "value": 22
        },
        {
            "label": "CPIT-121",
            "value": 23
        },
        {
            "label": "CPIT-222",
            "value": 25
        }
    ],
    "items": [
        {
            "label": "AB-GRAM",
            "value": 7
        },
        {
            "label": "X-gram",
            "value": 8
        },
        {
            "label": "Y-gram",
            "value": 10
        },
        {
            "label": "G-gram",
            "value": 11
        },
        {
            "label": "H-gram",
            "value": 12
        },
        {
            "label": "A-gram",
            "value": 13
        },
        {
            "label": "C-gram",
            "value": 14
        }
    ],
    "success": true
}
'''
########## CITY ##########-

@resources_route.route('/city', methods=['POST'])
@require_auth(['System_Administrator'])
def add_city(payload):

    city_data = request.get_json()
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    city = user.add_city_process(city_data)

    city.append(user)

    city_content = city.format_detail()

    return jsonify({
        'success': True,
        'message': 'تم اضافة المدينة بنجاح',
        'city': city_content
    })

'''
Request:
{
    "areas": [
        {
            "label": "North"
        },
        {
            "label": "West"
        } 
    ],
    "name": "Jeddah"
}
Response:
{
    "id": 4,
    "message": "تم اضافة المدينة بنجاح",
    "success": true
}
'''

@resources_route.route('/city', methods=['PATCH'])
@require_auth(['System_Administrator'])
def modify_city(payload):

    city_data = request.get_json()
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    city = user.edit_city(city_data)
    city_content = city.format_detail()
    city.close()

    return jsonify({
        'success': True,
        'message': 'تم تعديل معلومات المدينة بنجاح',
        'city': city_content
        })

'''
Request:
{
    "areas": [
        {
            "label": "east-west",
            "value": null,
            "status": "add"
        },
        {
            "label": "West",
            "value": 9,
            "status": "delete"
        } 
    ],
    "name": "Jeddah",
    "id": 6
}
Response:
{
    "message": "تم تعديل المدينة بنجاح",
    "success": true
}
'''

@resources_route.route('/city/<int:city_id>', methods=['DELETE'])
@require_auth(['System_Administrator'])
def delete_city(payload,city_id):

    city = City.query.filter_by(id=city_id).first_or_404(description='لا توجد مدينة بهذا الرقم')
    city.delete()

    return jsonify({
        'message': 'تم حذف المدينة بنجاح',
        'success': True
    })

'''
Request:
route: city/2
Response:
{
    "message": "تم حذف المدينة بنجاح",
    "success": true
}
'''

@resources_route.route('/city/<int:city_id>', methods=['GET'])
@require_auth(['System_Administrator'])
def get_city(payload,city_id):
    
    city = City.query.filter_by(id=city_id).first_or_404(description='لا توجد مدينة بهذا الرقم')

    return jsonify({
        'city': city.format_detail(),
        'success': True
        })

'''
Request: 
route: city/2
Response:
{
    "experiment": {
        "areas": [
            {
                "label": "West",
                "value": 10
            },
            {
                "label": "east-west",
                "value": 11
            }
        ],
        "id": 6,
        "name": "Jeddah"
    },
    "success": true
}
'''

@resources_route.route('/city', methods=['GET'])
@require_auth(['System_Administrator'])
def display_all_city(payload):

    selection = City.query.order_by(City.id)
    selection = City.filtering(request,selection)
    current_content, current_page = pagination(request,selection)

    success = True
    code = 200
    if len(current_content) == 0:
        code = 204
        success = False

    
    return jsonify({
        'success': success,
        'cities': current_content,
        'totalPages': math.ceil(len(selection)/PAGE_SHELF),
        'currentPage': current_page,
        'error': code
        })

'''
Request:
para : page=1
Response:
{
    "cities": [
        {
            "id": 6,
            "name": "Jeddah",
            "path": "/city/6"
        }
    ],
    "current_page": 1,
    "success": true,
    "total_pages": 1
}
'''

########## QUESTION ##########-

@resources_route.route('/question', methods=['POST'])
@require_auth(['System_Administrator'])
def add_question(payload):

    #get the json request
    question_data = request.get_json()
    #check form the system administrator
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    question = user.add_question(question_data)
    #get the response of question object
    question_response = question.format()
    #add the system administrator who has added the question
    question.append(user)

    return jsonify({
        'success': True,
        'message': 'تم اضافة السؤال بنجاح بنجاح',
        'question': question_response
    })

'''
Request:
{
 "text": "How many gram of sand in laboratory ?",
 "evaluateType": 1
}
Response:
{
    "message": "تم اضافة السؤال بنجاح بنجاح",
    "question": {
        "evaluateType": "evaluate_experiment",
        "id": 4,
        "text": "How many gram of sand in laboratory ?"
    },
    "success": true
}
'''

@resources_route.route('/question', methods=['PATCH'])
@require_auth(['System_Administrator'])
def modify_question(payload):

    #get the json request
    question_data = request.get_json()
    #check form the system administrator
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    #get the response after update the evaluate type 
    question_response = user.edit_question(question_data)

    return jsonify({
        'success': True,
        'message': 'تم تغيير نوع التقييم بنجاح',
        'question': question_response
        })

'''
Request:
{
 "text": "How many gram of sand in laboratory ?",
 "evaluateType": 2,
 "id": 4
}
Response:
{
    "message": "تم تغيير نوع التقييم بنجاح",
    "question": {
        "evaluateType": "evaluate_laboratory",
        "id": 4,
        "text": "How many gram of sand in laboratory ?"
    },
    "success": true
}
'''

@resources_route.route('/question/<int:question_id>', methods=['DELETE'])
@require_auth(['System_Administrator'])
def delete_question(payload,question_id):

    question = Question.query.filter_by(id=question_id).first_or_404(description='لا يوجد سؤال بهذا الرقم')
    #delete the question and all it's answer
    question.delete()

    return jsonify({
        'message': 'تم حذف المدينة بنجاح',
        'success': True
    })

'''
Request:
route: city/2
Response:
{
    "message": "تم حذف المدينة بنجاح",
    "success": true
}
'''

@resources_route.route('/question/<int:question_id>', methods=['GET'])
@require_auth(['System_Administrator'])
def get_question(payload,question_id):
    
    question = Question.query.filter_by(id=question_id).first_or_404(description='لا يوجد سؤال بهذا الرقم')

    return jsonify({
        'question': question.format(),
        'success': True
        })

'''
Request: 
route: city/2
Response:
{
    "question": {
        "evaluateType": "evaluate_laboratory",
        "id": 4,
        "text": "How many gram of sand in laboratory ?"
    },
    "success": true
}
'''

@resources_route.route('/question', methods=['GET'])
@require_auth(['System_Administrator'])
def display_all_questions(payload):

    selection = Question.query.order_by(Question.id)
    selection = Question.filtering(request,selection)
    current_content, current_page = pagination(request,selection)

    success = True
    code = 200
    if len(current_content) == 0:
        code = 204
        success = False
    
    return jsonify({
        'success': success,
        'questions': current_content,
        'totalPages': math.ceil(len(selection)/PAGE_SHELF),
        'currentPage': current_page,
        'error': code
        })

'''
Request:
para : page=1
Response:
{
    "currentPage": 1,
    "questions": [
        {
            "evaluateType": "evaluate_laboratory",
            "id": 4,
            "text": "How many gram of sand in laboratory ?"
        }
    ],
    "success": true,
    "totalPages": 1
}
'''

@resources_route.route('/evaluate-type', methods=['POST'])
@require_auth(['System_Administrator'])
def post_evaluate_type(payload):

    #initiate_evaluate_type()
    
    return jsonify({
        'success': True
        })
