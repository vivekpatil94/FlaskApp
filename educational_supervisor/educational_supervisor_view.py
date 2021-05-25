from flask import Blueprint,jsonify,request,abort
from app.authentication import require_auth
from sqlalchemy import and_, or_, func,exists
from app.models.users import System_Administrator,Educational_Supervisor,Laboratory_Manager
from app.models.resources import Course,City,Laboratory
from app.models.evaluate_system import Visit
from app.component import PAGE_SHELF,DATE_FORMAT,get_class_number,pagination
import datetime,pytz,math
from sqlalchemy.orm import joinedload


educational_supervisor_view = Blueprint('educational_supervisor_view',__name__)

'''
{
 "nid": "1224542790",
 "password": "123456"
}
{
 "nid": "1234567890",
 "password": "123456"
}
{
 "nid": "1592631597",
 "password": "123456"
}
{
 "nid": "1472583695",
 "password": "123456"
}
{
 "nid": "1112589659",
 "password": "123456"
} 
'''

########## ASSIGN EDUCATIONAL SUPERVISOR ##########

@educational_supervisor_view.route('/educational-supervisor', methods=['POST'])
@require_auth(['System_Administrator'])
def add_education_supervisor(payload):

    #get JSON request
    info_data = request.get_json()
    #check from the system administrator 
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    #invoke the function
    education_supervisor = user.add_education_supervisor(info_data)
    response = education_supervisor.format()
    education_supervisor.close()

    return jsonify({
        'success': True,
        'message': 'تم تسجيل مشرف تربوي جديد',
        'educationalSupervisor': response
    })

'''
Request:
    {
 "nid": "1112589658",
 "fname": "KHalid",
 "mname": "Ahmad",
 "lname": "Saleh",
 "password": "123456",
 "secondPassword": "123456",
 "phone": "0557797377",
 "email": "aa@hotmail.com",
 "role": "Educational_Supervisor",
 "courseId": 15,
 "areaID": 10
}
Response:
{
    "message": "تم تسجيل مشرف تربوي جديد",
    "success": true
}
'''

@educational_supervisor_view.route('/educational-supervisor', methods=['PATCH'])
@require_auth(['System_Administrator'])
def modify_education_supervisor(payload):

    #get JSON request
    info_data = request.get_json()
    #check from the system administrator 
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    #invoke the function
    edu_supervisor = user.modify_education_supervisor(info_data)
    response = edu_supervisor.format()
    edu_supervisor.close()

    return jsonify({
        'success': True,
        'message': 'تم تعديل المشرف تربوي',
        'educationalSupervisor': response
    })

'''
Request:
{
 "educationalSupervisorId": 88,
 "courseId": 15,
 "areaID": 11
}
Response:
{
    "educationalSupervisor": {
        "areaId": 11,
        "courseId": 15,
        "email": "aa@hotmail.com",
        "id": 88,
        "name": "KHalid Ahmad Saleh",
        "nid": "1112589658",
        "phone": "0557797377",
        "role": {
            "ar": "مشرف تربوي",
            "en": "Educational_Supervisor"
        }
    },
    "message": "تم تعديل المشرف تربوي",
    "success": true
}
'''

@educational_supervisor_view.route('/educational-supervisor/<int:user_id>', methods=['GET'])
@require_auth(['System_Administrator'])
def display_specific_education_supervisor(payload,user_id):

    #get JSON request
    info_data = request.get_json()
    #check from the system administrator 
    user = System_Administrator.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    #invoke the function
    edu_supervisor = Educational_Supervisor.query.filter_by(id= user_id).first_or_404('لا يوجد مشرف تربوي بهذا الرقم')
    response = edu_supervisor.format()

    city_selection = City.query.order_by(City.id).all()
    city_content = [c.format_create() for c in city_selection]

    courses = Course.query.order_by(Course.id).all()
    course_content = [course.format_detail_st() for course in courses]

    edu_supervisor.close()

    return jsonify({
        'success': True,
        'cities': city_content,
        'courses': course_content,
        'educationalSupervisor': response
    })

'''
Request:
route 
Response:
{
    "success": {
        "areaId": 11,
        "courseId": 15,
        "email": "aa@hotmail.com",
        "id": 88,
        "name": "KHalid Ahmad Saleh",
        "nid": "1112589658",
        "phone": "0557797377",
        "role": {
            "ar": "مشرف تربوي",
            "en": "Educational_Supervisor"
        }
    }
}
'''

@educational_supervisor_view.route('/educational-supervisor', methods=['GET'])
@require_auth(['System_Administrator'])
def display_all_education_supervisor(payload):

    #get JSON request
    info_data = request.get_json()

    #invoke the function
    selection = Educational_Supervisor.query
    selection = Educational_Supervisor.filtering(request,selection)
    current_content, current_page = pagination(request,selection)

    success = True
    code = 200
    if len(current_content) == 0:
        code = 204
        success = False

    city_selection = City.query.order_by(City.id).all()
    city_content = [c.format_create() for c in city_selection]

    courses = Course.query.order_by(Course.id).all()
    course_content = [course.format_detail_st() for course in courses]

    return jsonify({
        'success': success,
        'code': code,
        'cities': city_content,
        'courses': course_content,
        'educationalSupervisors': current_content,
        'totalPages': math.ceil(len(selection)/PAGE_SHELF),
        'currentPage': current_page
    })

'''
Request:
route 
Response:
{
    "success": {
        "areaId": 11,
        "courseId": 15,
        "email": "aa@hotmail.com",
        "id": 88,
        "name": "KHalid Ahmad Saleh",
        "nid": "1112589658",
        "phone": "0557797377",
        "role": {
            "ar": "مشرف تربوي",
            "en": "Educational_Supervisor"
        }
    }
}
'''

@educational_supervisor_view.route('/educational-supervisor/create-requirements', methods=['GET'])
@require_auth(['System_Administrator'])
def city_requirements(payload):

    city_selection = City.query.order_by(City.id).all()
    city_content = [c.format_create() for c in city_selection]

    courses = Course.query.order_by(Course.id).all()
    course_content = [course.format_detail_st() for course in courses]

    return jsonify({
        'cities': city_content,
        'courses': course_content,
        'success': True
        })

'''
Request:
route: /school/create_requirements
Response:
{
    "cities": [
        {
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
            "label": "Jeddah",
            "value": 6
        }
    ],
    "success": true
}
'''

########## VISIT ##########

@educational_supervisor_view.route('/visit', methods=['POST'])
@require_auth(['Educational_Supervisor'])
def create_visit(payload):

    #get JSON request
    visit_data = request.get_json()
    #check from the educational supervisor
    user = Educational_Supervisor.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    #invoke the function of initiate new visit
    visit = user.initiate_visit(visit_data)
    response = visit.format()

    laboratories_selection = visit.school.own_labs
    laboratories_content = [l.format_evaluate() for l in laboratories_selection]  
    lab_mngrs_selection = visit.school.lab_manager_member
    lab_mngrs_content = [l.format_evaluate() for l in lab_mngrs_selection]

    user.close()

    return jsonify({
        'visit': response,
        'laboratories': laboratories_content,
        'laboratoryManager': lab_mngrs_content,
        'message': 'تم انشاء الزيارة بنجاح',
        'success': True
        })

'''
Request:
{
 "visitDate": "03-18-2021",
 "note": "I am coming",
 "schoolId": 1000
 }
Response:
{
    "success": true,
    "visit": {
        "educationalSupervisorId": 88,
        "educationalSupervisorName": "KHalid Ahmad Saleh",
        "note": "I am coming",
        "schoolId": 1000,
        "schoolName": "مدرسة الفلاح",
        "visitDate": "Thu, 18 Mar 2021 00:00:00 GMT",
        "visitId": 1
    }
}
'''

@educational_supervisor_view.route('/visit', methods=['PATCH'])
@require_auth(['Educational_Supervisor'])
def modify_visit(payload):

    #get JSON request
    visit_data = request.get_json()
    #check from the educational supervisor
    user = Educational_Supervisor.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    #invoke the function of initiate new visit
    visit = user.update_visit(visit_data)
    response = visit.format()
    user.close()

    return jsonify({
        'visit': response,
        'message': 'تم تعديل الزيارة بنجاح',
        'success': True
        })

'''
Request:
{
 "visitDate": "03-18-2021",
 "note": "I am coming",
 "schoolId": 1000,
 "visitId": 1
}
Response:
{
    "success": true,
    "visit": {
        "educationalSupervisorId": 88,
        "educationalSupervisorName": "KHalid Ahmad Saleh",
        "note": "I am coming",
        "schoolId": 1000,
        "schoolName": "مدرسة الفلاح",
        "visitDate": "Thu, 18 Mar 2021 00:00:00 GMT",
        "visitId": 1
    }
}
'''

@educational_supervisor_view.route('/visit/<int:visit_id>', methods=['DELETE'])
@require_auth(['Educational_Supervisor'])
def delete_visit(payload,visit_id):

    #get JSON request
    visit_data = request.get_json()
    #check from the educational supervisor
    user = Educational_Supervisor.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    #get specific visit to delete
    visit = Visit.query.filter(and_(Visit.id==visit_id, Visit.educational_supervisor_id == user.id)).first_or_404(description='لا توجد زيارة بهذا الرقم')

    visit.delete()

    return jsonify({
        'message': 'تم حذف الزيارة بنجاح',
        'success': True
        })

'''
Request:
route
Response:
{
        'message': 'تم حدف الزيارة بنجاح',
        'success': True
        }
'''

@educational_supervisor_view.route('/visit/<int:visit_id>', methods=['GET'])
@require_auth(['Educational_Supervisor'])
def display_specific_visit(payload,visit_id):


    #get JSON request
    visit_data = request.get_json()
    #check from the educational supervisor
    user = Educational_Supervisor.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    #get specific visit to display
    visit = Visit.query.filter(and_(Visit.id==visit_id, Visit.educational_supervisor_id == user.id)).first_or_404(description='لا توجد زيارة بهذا الرقم')
    response = visit.format()
    
    laboratories_selection = visit.school.own_labs
    laboratories_content = [l.format_evaluate() for l in laboratories_selection]  
    lab_mngrs_selection = visit.school.lab_manager_member
    lab_mngrs_content = [l.format_evaluate() for l in lab_mngrs_selection]

    user.close()

    return jsonify({
        'visit': response,
        'laboratories': laboratories_content,
        'laboratoryManager': lab_mngrs_content,
        'success': True
        })

'''
Request:
route
Response:
{
    "success": true,
    "visit": {
        "educationalSupervisorId": 88,
        "educationalSupervisorName": "KHalid Ahmad Saleh",
        "note": "I am coming",
        "schoolId": 1000,
        "schoolName": "مدرسة الفلاح",
        "visitDate": "Thu, 18 Mar 2021 00:00:00 GMT",
        "visitId": 1
    }
}
'''

@educational_supervisor_view.route('/visit/current', methods=['GET'])
@require_auth(['Educational_Supervisor'])
def display_current_visit(payload):


    #check from the educational supervisor
    user = Educational_Supervisor.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    #get specific visit to display
    visit = Visit.query.filter(and_(Visit.educational_supervisor_id == user.id, Visit.closed == False)).first_or_404(description='لا توجد زيارات في الوقت الحالي')
    response = visit.format()
    
    laboratories_selection = visit.school.own_labs
    laboratories_content = [l.format_evaluate() for l in laboratories_selection]  
    lab_mngrs_selection = visit.school.lab_manager_member
    lab_mngrs_content = [l.format_evaluate() for l in lab_mngrs_selection]

    user.close()

    return jsonify({
        'visit': response,
        'laboratories': laboratories_content,
        'laboratoryManager': lab_mngrs_content,
        'success': True
        })

'''
Request:
route
Response:
{
    "success": true,
    "visit": {
        "educationalSupervisorId": 88,
        "educationalSupervisorName": "KHalid Ahmad Saleh",
        "note": "I am coming",
        "schoolId": 1000,
        "schoolName": "مدرسة الفلاح",
        "visitDate": "Thu, 18 Mar 2021 00:00:00 GMT",
        "visitId": 1
    }
}
'''

@educational_supervisor_view.route('/visit', methods=['GET'])
@require_auth(['Educational_Supervisor'])
def display_all_visits(payload):

    #get JSON request
    visit_data = request.get_json()
    #check from the educational supervisor
    user = Educational_Supervisor.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    #get all visits
    visits = Visit.query.filter(Visit.educational_supervisor_id == user.id).all()
    visit_content = [visit.format() for visit in visits]

    laboratories_selection = visit.school.own_labs
    laboratories_content = [l.format_evaluate() for l in laboratories_selection]  
    lab_mngrs_selection = visit.school.lab_manager_member
    lab_mngrs_content = [l.format_evaluate() for l in lab_mngrs_selection]
    user.close()

    return jsonify({
        'visits': visit_content,
        'laboratories': laboratories_content,
        'laboratoryManager': lab_mngrs_content,
        'success': True
        })

'''
Request:
route
Response:
{
    "success": true,
    "visits": [
        {
            "educationalSupervisorId": 88,
            "educationalSupervisorName": "KHalid Ahmad Saleh",
            "note": "I am coming",
            "schoolId": 1000,
            "schoolName": "مدرسة الفلاح",
            "visitDate": "Thu, 18 Mar 2021 00:00:00 GMT",
            "visitId": 1
        }
    ]
}
'''

@educational_supervisor_view.route('/visit/current/close', methods=['POST'])
@require_auth(['Educational_Supervisor'])
def close_visit(payload):

    #check from the educational supervisor
    user = Educational_Supervisor.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    #close the current visit
    visits = user.close_visit()
    response = visits.format()
    user.close()

    return jsonify({
        'visits': response,
        'success': True
        })

########## GET SPECIFIC IN VISIT ##########

@educational_supervisor_view.route('/visit/current/laboratory/<int:lab_id>', methods=['GET'])
@require_auth(['Educational_Supervisor'])
def display_laboratory(payload,lab_id):

    #check id of educational supervisor
    user = Educational_Supervisor.query.with_entities(Educational_Supervisor.id).filter(and_(
    Educational_Supervisor.id==payload['sub'])).first_or_404(description='الرجاء التسجيل في النظام اولاً')

    #check if there is any visit right now [STATUS: OPEN]
    visit = Visit.query.with_entities(Visit.id, Visit.school_id).filter(and_(Visit.educational_supervisor_id == user.id,
    Visit.closed == False)).first_or_404(description='لا توجد زيارات في الوقت الحالي')
    #get the laboratory
    laboraotory = Laboratory.query.filter(and_(Laboratory.school_id== visit.school_id, Laboratory.number==lab_id)).first_or_404('لا يوجد مختبر بهذا الرقم')

    response = laboraotory.format_evaluate()
    laboraotory.close()

    return jsonify({
        'success': True,
        'laboratory':response
    })

'''
Response:
route
Request:
{
    "laboratory": {
        "id": 1,
        "labManagers": [
            {
                "label": "Fouad A Ramadan",
                "value": 62
            }
        ],
        "path": "/laboratory/1",
        "rate": 5.0
    },
    "success": true
}
'''

@educational_supervisor_view.route('/visit/current/laboratory-manager/<int:lab_mngr_id>', methods=['GET'])
@require_auth(['Educational_Supervisor'])
def display_laboratory_manager(payload,lab_mngr_id):

    #check id of educational supervisor
    user = Educational_Supervisor.query.with_entities(Educational_Supervisor.id).filter(and_(
    Educational_Supervisor.id==payload['sub'])).first_or_404(description='الرجاء التسجيل في النظام اولاً')

    #check if there is any visit right now [STATUS: OPEN]
    visit = Visit.query.with_entities(Visit.id, Visit.school_id).filter(and_(Visit.educational_supervisor_id == user.id,
    Visit.closed == False)).first_or_404(description='لا توجد زيارات في الوقت الحالي')

    #get the lab manager 
    laboraotory_manager = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==lab_mngr_id, Laboratory_Manager.school_id == visit.school_id,
    Laboratory_Manager.activate == True)).first_or_404(description='لا يوجد محضر مختبر بهذا الرقم')
    response = laboraotory_manager.format_evaluate()

    laboraotory_manager.close()

    return jsonify({
        'success': True,
        'laboratoryManager':response
    })

'''
Response:
route
Request:
{
    "laboratoryManager": {
        "id": 62,
        "laboratories": [
            {
                "label": 1,
                "value": 1
            },
            {
                "label": 25,
                "value": 25
            },
            {
                "label": 55,
                "value": 55
            },
            {
                "label": 88,
                "value": 88
            },
            {
                "label": 58,
                "value": 58
            },
            {
                "label": 59,
                "value": 59
            },
            {
                "label": 522,
                "value": 522
            }
        ],
        "name": "Fouad A Ramadan",
        "path": "/laboratory-manager/62",
        "rate": 3.75,
        "role": {
            "ar": "محضر مختبر",
            "en": "Laboratory_Manager"
        }
    },
    "success": true
}
'''

########## DASHBOARD IN VISIT ##########

@educational_supervisor_view.route('/visit/current/laboratory/<int:lab_id>/dashboard', methods=['GET'])
@require_auth(['Educational_Supervisor'])
def laboratory_dashboard(payload,lab_id):

    #check id of educational supervisor
    user = Educational_Supervisor.query.with_entities(Educational_Supervisor.id).filter(and_(
    Educational_Supervisor.id==payload['sub'])).first_or_404(description='الرجاء التسجيل في النظام اولاً')

    #check if there is any visit right now [STATUS: OPEN]
    visit = Visit.query.with_entities(Visit.id, Visit.school_id).filter(and_(Visit.educational_supervisor_id == user.id,
    Visit.closed == False)).first_or_404(description='لا توجد زيارات في الوقت الحالي')
    #get the laboratory
    laboraotory = Laboratory.query.filter(and_(Laboratory.school_id== visit.school_id, Laboratory.number==lab_id)).first_or_404('لا يوجد مختبر بهذا الرقم')

    response = laboraotory.dashboard(request)
    laboraotory.close()

    return jsonify({
        'success': True,
        'dashboard':response
    })

'''
Response:
route
Request:
{
    "dashboard": {
        "endSemester": "Tue, 01 Jun 2021 00:00:00 GMT",
        "executedExperiment": 1,
        "expiredItem": 1,
        "notExecutedExperiment": 0,
        "numberExecuteExperiment": [
            {
                "experimentExecuted": "EXP YY",
                "qunatity": 1
            },
            {
                "experimentExecuted": "X",
                "qunatity": 0
            },
            {
                "experimentExecuted": "Xa",
                "qunatity": 0
            }
        ],
        "numberExecutedDate": [
            [
                "Mon, 15 Mar 2021 00:00:00 GMT",
                1
            ]
        ],
        "numberSafetyItem": [
            {
                "quantity": 0,
                "safetyItem": "Fire extinguisher"
            }
        ],
        "startSemester": "Mon, 01 Feb 2021 00:00:00 GMT",
        "validItem": 8,
        "waitingExperiment": 0,
        "willExpireItem": 0
    },
    "success": true
}
'''

@educational_supervisor_view.route('/visit/current/laboratory-manager/<int:lab_mngr_id>/dashboard', methods=['GET'])
@require_auth(['Educational_Supervisor'])
def laboratory_manager_dashboard(payload,lab_mngr_id):

    #check id of educational supervisor
    user = Educational_Supervisor.query.with_entities(Educational_Supervisor.id).filter(and_(
    Educational_Supervisor.id==payload['sub'])).first_or_404(description='الرجاء التسجيل في النظام اولاً')

    #check if there is any visit right now [STATUS: OPEN]
    visit = Visit.query.with_entities(Visit.id, Visit.school_id).filter(and_(Visit.educational_supervisor_id == user.id,
    Visit.closed == False)).first_or_404(description='لا توجد زيارات في الوقت الحالي')
    #get the lab manager 
    laboraotory_manager = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==lab_mngr_id, Laboratory_Manager.school_id == visit.school_id,
    Laboratory_Manager.activate == True)).first_or_404(description='لا يوجد محضر مختبر بهذا الرقم')

    response = laboraotory_manager.dashboard(request)
    laboraotory_manager.close()

    return jsonify({
        'success': True,
        'dashboard':response
    })

'''
Response:
route
Response:
{
    "dashboard": {
        "approvedExperiments": 1,
        "endSemester": "Sat, 05 Jun 2021 00:00:00 GMT",
        "itemActivity": [
            {
                "added": 0,
                "deleted": 0,
                "monthName": "January"
            },
            {
                "added": 9,
                "deleted": 4,
                "monthName": "February"
            },
            {
                "added": 2,
                "deleted": 0,
                "monthName": "March"
            }
        ],
        "notApprovedExperiments": 0,
        "numberExecuteExperiment": [
            {
                "experimentExecuted": "EXP YY",
                "qunatity": 1
            },
            {
                "experimentExecuted": "X",
                "qunatity": 0
            },
            {
                "experimentExecuted": "Xa",
                "qunatity": 0
            }
        ],
        "numberExecutedDate": [
            [
                "Mon, 15 Mar 2021 00:00:00 GMT",
                1
            ]
        ],
        "numberLabs": 7,
        "rate": 3.75,
        "startSemester": "Fri, 01 Jan 2021 00:00:00 GMT",
        "totalExperiments": 1
    },
    "success": true
}
'''