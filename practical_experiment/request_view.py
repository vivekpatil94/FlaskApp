from flask import Blueprint,jsonify,request,abort
from app.authentication import require_auth
from app.models.users import Laboratory_Manager,Science_Teacher
from app.models.resources import School,Laboratory_Item
from app.models.transactions import Practical_Experiment_Request,Confirm_Practical_Request
from app.models.evaluate_system import Evaluate_Type,Question
from app.component import pagination,PAGE_SHELF
from sqlalchemy import and_, or_
import math
import datetime


'''
School Manager
{
 "nid": "1224542790",
 "password": "123456"
}
Sys Admin
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
'''

request_view = Blueprint('request_view',__name__)

def check_school(user_id,role):
    user = None
    #check if the laboratory manager or science teacher has school or not 
    if role == 'Laboratory_Manager':
        user = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==user_id, Laboratory_Manager.activate == True)).first_or_404(description='الرجاء التسجيل في النظام اولاً')
    elif role == 'Science_Teacher':
        user = Science_Teacher.query.filter(and_(Science_Teacher.id==user_id, Science_Teacher.activate == True)).first_or_404(description='الرجاء التسجيل في النظام اولاً')
    else:
        abort(404, 'الرجاء التسجيل في النظام اولاً')
    school = user.his_school
    if school is None:
        abort(404, 'ليس لديك مدرسة مسجلة')
    return user, school

def check_lab(laboratory_manager):
    #get all the labs that lab manager work on
    labs = laboratory_manager.work_on_labs
    return labs

########## INITIATE PRACTICAL REQUEST ##########        

@request_view.route('/practical-experiment', methods=['POST'])
@require_auth(['Science_Teacher'])
def initiate_practical_experiment(payload):

    #check if the science teacher has school
    science_teacher, school = check_school(payload['sub'],payload['permissions'])

    practical_experiment_data = request.get_json()

    experiment_request, note = science_teacher.initiate_new_experiment(practical_experiment_data,school)
     
    return jsonify({
        'success': True,
        'message': note,
        'practicalExperiment': experiment_request.format()
    })

'''
Request:
{
 "experimentId": 60,
 "executeDate": "5-25-2023",
 "classNo": 5,
 "labId": 1,
 "quantity": 50
}
Response:
{
    "message": "تم انشاء طلب تجربة عملية جديد",
    "note": "لا توجد كمية مناسبة لعمل التجربة العملية في الوقت الحالي",
    "practicalExperiment": {
        "classNo": 5,
        "createDate": "Sun, 21 Feb 2021 00:00:00 GMT",
        "executeDate": "Thu, 25 May 2023 00:00:00 GMT",
        "experimentName": "EXP YY",
        "id": 1,
        "labId": 1,
        "quantity": 50
    },
    "success": true
}
{
    "message": "تم انشاء طلب تجربة عملية جديد",
    "note": "توجد كمية متوفرة",
    "practicalExperiment": {
        "classNo": 4,
        "createDate": "Sun, 21 Feb 2021 00:00:00 GMT",
        "executeDate": "Thu, 25 May 2023 00:00:00 GMT",
        "experimentName": "EXP YY",
        "id": 3,
        "labId": 1,
        "quantity": 10
    },
    "success": true
}
'''

@request_view.route('/practical-experiment', methods=['PATCH'])
@require_auth(['Science_Teacher'])
def modify_practical_experiment(payload):
    
    #check if the science teacher has school
    science_teacher, school = check_school(payload['sub'],payload['permissions'])

    practical_experiment_data = request.get_json()

    experiment_request, note = science_teacher.edit_experiment(practical_experiment_data,school)


    return jsonify({
        'success': True,
        'message': note,
        'practicalExperiment': experiment_request.format()
    })

'''
Request:
{
 "experimentId": 60,
 "executeDate": "5-25-2023",
 "classNo": 5,
 "labId": 1,
 "quantity": 50
}
Response:
{
    "message": "تم انشاء طلب تجربة عملية جديد",
    "note": "لا توجد كمية مناسبة لعمل التجربة العملية في الوقت الحالي",
    "practicalExperiment": {
        "classNo": 5,
        "createDate": "Sun, 21 Feb 2021 00:00:00 GMT",
        "executeDate": "Thu, 25 May 2023 00:00:00 GMT",
        "experimentName": "EXP YY",
        "id": 1,
        "labId": 1,
        "quantity": 50
    },
    "success": true
}
{
    "message": "تم انشاء طلب تجربة عملية جديد",
    "note": "توجد كمية متوفرة",
    "practicalExperiment": {
        "classNo": 4,
        "createDate": "Sun, 21 Feb 2021 00:00:00 GMT",
        "executeDate": "Thu, 25 May 2023 00:00:00 GMT",
        "experimentName": "EXP YY",
        "id": 3,
        "labId": 1,
        "quantity": 10
    },
    "success": true
}
'''

@request_view.route('/practical-experiment/<int:exp_id>', methods=['DELETE'])
@require_auth(['Science_Teacher'])
def delete_practical_experiment(payload,exp_id):
    
    #check if the science teacher has school
    science_teacher, school = check_school(payload['sub'],payload['permissions'])

    practical_experiment = Practical_Experiment_Request.query.filter(and_(Practical_Experiment_Request.id==exp_id,
    Practical_Experiment_Request.science_teacher_id==science_teacher.id, Practical_Experiment_Request.science_teacher_school_id==school.id)).first_or_404(
        description='لا يوجد طلب بهذا الرقم للحذف')
    #check the request has not confirm yet
    confirm = Confirm_Practical_Request.query.filter_by(request_id=practical_experiment.id).first()
    if confirm is not None:
        abort(400, 'الطلب قد تم الرد عليه مسبقا, لا يمكن حذفه في الوقت الحالي')
    
    practical_experiment.delete()
     
    return jsonify({
        'success': True,
        'message': 'تم حذف طلب تجربة عملية بنجاح'
    })

'''
Request:
route: /practical-experiment/3
Response:
{
    "message": "تم حذف طلب تجربة عملية بنجاح",
    "success": true
}
'''

@request_view.route('/practical-experiment/<int:exp_id>', methods=['GET'])
@require_auth(['Science_Teacher'])
def display_specific_practical_experiment(payload,exp_id):
    
    #check if the science teacher has school
    science_teacher, school = check_school(payload['sub'],payload['permissions'])

    practical_experiment = Practical_Experiment_Request.query.filter(and_(Practical_Experiment_Request.id==exp_id,
    Practical_Experiment_Request.science_teacher_id==science_teacher.id, Practical_Experiment_Request.science_teacher_school_id==school.id)).first_or_404(
        description='لا يوجد طلب بهذا الرقم للحذف')
    response = practical_experiment.format()  
    labs = school.own_labs
    lab_content = [lab.format_create() for lab in labs]

    #get the all course the scinnce teacher teach 
    courses = science_teacher.teach
    course_content = [course.format_detail_st() for course in courses]

    #get only the id of evaluate type, to get all the questions
    evaluate = Evaluate_Type.query.with_entities(Evaluate_Type.id).filter_by(title='evaluate_experiment').first_or_404('لا يوجد نوع تقييم محدد')
    questions = Question.query.filter_by(evaluate_type=evaluate.id).all()
    questions = [q.format_question() for q in questions]
    practical_experiment.close()


    return jsonify({
        'success': True,
        'practicalExperiment': response,
        'questions': questions,
        'laboratories': lab_content,
        'courses': course_content
    })

'''
Resquest:
route: /practical-experiment/3
Response:
{
    "practicalExperiment": {
        "classNo": 4,
        "createDate": "Sun, 21 Feb 2021 00:00:00 GMT",
        "executeDate": "Thu, 25 May 2023 00:00:00 GMT",
        "experimentName": "EXP YY",
        "id": 3,
        "labId": 5,
        "quantity": 5
    },
    "success": true
}
'''

@request_view.route('/practical-experiment', methods=['GET'])
@require_auth(['Science_Teacher'])
def dispaly_all_practical_experiment(payload):
    
    #check if the science teacher has school
    science_teacher, school = check_school(payload['sub'],payload['permissions'])
    
    practical_experiments = Practical_Experiment_Request.query.filter(and_(
    Practical_Experiment_Request.science_teacher_id==science_teacher.id, Practical_Experiment_Request.science_teacher_school_id==school.id))
    
    practical_experiments = Practical_Experiment_Request.filtering(request,practical_experiments)

    current_content, current_page = pagination(request,practical_experiments)
    #check if there is no any content to display 
    success = True
    code = 200
    if len(current_content) == 0:
        code = 204
        success = False

    labs = school.own_labs
    lab_content = [lab.format_create() for lab in labs]

    courses = science_teacher.teach
    course_content = [course.format_detail_st() for course in courses]

    #get only the id of evaluate type, to get all the questions
    evaluate = Evaluate_Type.query.with_entities(Evaluate_Type.id).filter_by(title='evaluate_experiment').first_or_404('لا يوجد نوع تقييم محدد')
    questions = Question.query.filter_by(evaluate_type=evaluate.id).all()
    questions = [q.format_question() for q in questions]


    return jsonify({
        'success': success,
        'practicalExperiments': current_content,
        'laboratories': lab_content,
        'questions': questions,
        'totalPages': math.ceil(len(practical_experiments)/PAGE_SHELF),
        'currentPage': current_page,
        'courses': course_content,
        'error': code
    })

'''
Request:
route /practical-experiment
Response:
{
    "practicalExperiments": [
        {
            "classNo": 6,
            "createDate": "Sun, 21 Feb 2021 00:00:00 GMT",
            "executeDate": "Thu, 25 May 2023 00:00:00 GMT",
            "experimentName": "EXP YY",
            "id": 2,
            "labId": 1,
            "quantity": 50
        },
        {
            "classNo": 5,
            "createDate": "Mon, 22 Feb 2021 00:00:00 GMT",
            "executeDate": "Thu, 25 May 2023 00:00:00 GMT",
            "experimentName": "EXP YY",
            "id": 8,
            "labId": 1,
            "quantity": 10
        },
        {
            "classNo": 4,
            "createDate": "Sun, 21 Feb 2021 00:00:00 GMT",
            "executeDate": "Thu, 25 May 2023 00:00:00 GMT",
            "experimentName": "EXP YY",
            "id": 3,
            "labId": 5,
            "quantity": 5
        }
    ],
    "success": true
}
'''

@request_view.route('/practical-experiment/create-requirements', methods=['GET'])
@require_auth(['Science_Teacher'])
def practical_experiment_requirements(payload):
    
    #check if the science teacher has school
    science_teacher, school = check_school(payload['sub'],payload['permissions'])

    courses = science_teacher.teach
    course_content = [course.format_detail_st() for course in courses]
    if len(course_content) == 0:
        abort(404, 'لم يتم تعيين مواد دراسية مخصصة لك من قبل قائد المدرسة')
    labs = school.own_labs
    lab_content = [lab.format_create() for lab in labs]
    if len(lab_content) == 0:
        abort(404, 'لا يوجد مختبر في المدرسة')
          
    return jsonify({
        'success': True,
        'courses': course_content,
        'laboraotries': lab_content
    })
    
'''
Request
route: /practical-experiment/create-requirements
Resonse
{
    "courses": [
        {
            "label": "CPIT-401",
            "practicalExperiments": [
                {
                    "items": [
                        {
                            "label": "AB - GRAM",
                            "quantity": 1,
                            "value": 7
                        }
                    ],
                    "label": 60,
                    "value": "EXP YY"
                },
                {
                    "items": [],
                    "label": 5,
                    "value": "X"
                }
            ],
            "value": 15
        }
    ],
    "laboraotries": [
        {
            "label": 1,
            "value": 1
        },
        {
            "label": 2,
            "value": 2
        }
    ],
    "success": true
}
'''

########## CONFIRM PRACTICAL REQUEST ##########        

@request_view.route('/practical-request', methods=['POST'])
@require_auth(['Laboratory_Manager'])
def confirm_practical_experiment(payload):
    
    #check if the laboratory manager has school
    lab_mngr, school = check_school(payload['sub'],payload['permissions'])
    laboratories = check_lab(lab_mngr)

    practical_experiment_data = request.get_json()


    confirmation, message = lab_mngr.confirm_request(practical_experiment_data,school,laboratories)
    response = confirmation.format()
    confirmation.close()

    return jsonify({
        'success': True,
        'message': message,
        'request': response
    })

''' 
Request:
{
 "requestId": 9,
 "state": true,
 "note": "OKAY"
}
Response:
{
    "itemUsed": [
        {
            "id": 16,
            "quantity": 5
        },
        {
            "id": 15,
            "quantity": 5
        }
    ],
    "message": "تم قبول الطلب بنجاح",
    "success": true
}
-------
{
    "confirmation": {
        "classNo": 1,
        "confirmDate": "Fri, 26 Feb 2021 00:00:00 GMT",
        "confirmNote": "OKAY",
        "confirmed": true,
        "courseName": "CPIT-401",
        "createDate": "Thu, 25 Feb 2021 00:00:00 GMT",
        "executeDate": "Sun, 28 May 2023 00:00:00 GMT",
        "experimentName": "EXP YY",
        "id": 9,
        "items_used": [
            {
                "label": "(GRAM :وحدة القياس) AB",
                "quantity": 10,
                "value": 16
            }
        ],
        "labId": 1,
        "labManager": "Fouad A Ramadan",
        "quantity": 10,
        "status": true
    },
    "message": "قد تم الرد على الطلب مسبقاً",
    "success": true
}
'''

@request_view.route('/practical-request', methods=['PATCH'])
@require_auth(['Laboratory_Manager'])
def modify_confirm_practical_experiment(payload):
    
    #check if the laboratory manager has school
    lab_mngr, school = check_school(payload['sub'],payload['permissions'])
    laboratories = check_lab(lab_mngr)

    practical_experiment_data = request.get_json()


    confirmation, message = lab_mngr.edit_confirm_request(practical_experiment_data,school,laboratories)
    response = confirmation.format()
    confirmation.close()

    return jsonify({
        'success': True,
        'message': message,
        'request': response
    })

'''
Request:
{
 "requestId": 9,
 "state": false,
 "note": "There is problem with laboraotry"
}
Response:
{
    "confirmation": {
        "classNo": 1,
        "confirmDate": "Fri, 26 Feb 2021 00:00:00 GMT",
        "confirmNote": "There is problem with laboraotry",
        "confirmed": true,
        "courseName": "CPIT-401",
        "createDate": "Thu, 25 Feb 2021 00:00:00 GMT",
        "executeDate": "Sun, 28 May 2023 00:00:00 GMT",
        "experimentName": "EXP YY",
        "id": 9,
        "items_used": [],
        "labId": 1,
        "labManager": "Fouad A Ramadan",
        "quantity": 10,
        "status": false
    },
    "message": "تم رفض الطلب بنجاح",
    "success": true
}
'''

@request_view.route('/practical-request/<int:request_id>', methods=['DELETE'])
@require_auth(['Laboratory_Manager'])
def delete_confirm_practical_experiment(payload,request_id):
    
    #check if the laboratory manager has school
    lab_mngr, school = check_school(payload['sub'],payload['permissions'])
    laboratories = check_lab(lab_mngr)

    request = lab_mngr.delete_confirm_request(request_id,laboratories,school)

    response = request.format(payload['permissions'])
    request.close()

    return jsonify({
        'success': True,
        'request': response
    })

'''
Request:
route: /confirm-practical-experiment/9
Response:
{
    "request": {
        "classNo": 1,
        "confirmDate": "",
        "confirmNote": "",
        "confirmed": false,
        "courseName": "CPIT-401",
        "createDate": "Thu, 25 Feb 2021 00:00:00 GMT",
        "executeDate": "Sun, 28 May 2023 00:00:00 GMT",
        "experimentName": "EXP YY",
        "id": 9,
        "items_used": [],
        "labId": 1,
        "labManager": "",
        "quantity": 10,
        "status": null
    },
    "success": true
}
'''

@request_view.route('/practical-request/<int:request_id>', methods=['GET'])
@require_auth(['Laboratory_Manager'])
def display_specific_confirm_practical_experiment(payload,request_id):
    
    #check if the laboratory manager has school
    lab_mngr, school = check_school(payload['sub'],payload['permissions'])
    laboratories = check_lab(lab_mngr)

    lab_content = [lab.format_lab_manager() for lab in laboratories]
    #check if there is no any lab to display 
    if len(lab_content) == 0:
        abort(404, 'لا يوجد مختبرات مسجلة برقمك, الرجاء التواصل مع مدير المدرسة')

    labs_id = []
    for lab in laboratories:
        labs_id.append(lab.number) 
    #check if the request for his labs and exists
    request = Practical_Experiment_Request.query.filter(and_(Practical_Experiment_Request.id==request_id,
    Practical_Experiment_Request.school_id == school.id,Practical_Experiment_Request.lab_id.in_(labs_id))).first_or_404('لا يوجد طلب بهذا الرقم')

    response = request.format(payload['permissions'])
    request.close()



    return jsonify({
        'success': True,
        'request': response,
        'laboratories':lab_content
    })

'''
Request:
route: /confirm-practical-experiment/9
Response:
{
    "confirmation": {
        "classNo": 1,
        "confirmDate": "Fri, 26 Feb 2021 00:00:00 GMT",
        "confirmNote": "There is problem with laboraotry",
        "confirmed": true,
        "courseName": "CPIT-401",
        "createDate": "Thu, 25 Feb 2021 00:00:00 GMT",
        "executeDate": "Sun, 28 May 2023 00:00:00 GMT",
        "experimentName": "EXP YY",
        "id": 9,
        "items_used": [],
        "labId": 1,
        "labManager": "Fouad A Ramadan",
        "quantity": 10,
        "status": false
    },
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
    "success": true
}
'''

@request_view.route('/practical-request', methods=['GET'])
@require_auth(['Laboratory_Manager'])
def display_all_confirm_practical_experiment(payload):
    
    #check if the laboratory manager has school
    lab_mngr, school = check_school(payload['sub'],payload['permissions'])
    laboratories = check_lab(lab_mngr)


    lab_content = [lab.format_lab_manager() for lab in laboratories]
    #check if there is no any lab to display 
    if len(lab_content) == 0:
        abort(404, 'لا يوجد مختبرات مسجلة برقمك, الرجاء التواصل مع مدير المدرسة')
        
    labs_id = []
    for lab in laboratories:
        labs_id.append(lab.number) 
    #check if the request for his labs and exists
    requests = Practical_Experiment_Request.query.filter(and_(Practical_Experiment_Request.school_id == school.id,Practical_Experiment_Request.lab_id.in_(labs_id)))

    practical_requests = Practical_Experiment_Request.filtering(request,requests)

    current_content, current_page = pagination(request,practical_requests,payload['permissions'])
    #check if there is no any content to display 
    success = True
    code = 200
    if len(current_content) == 0:
        code = 204
        success = False

    return jsonify({
        'success': success,
        'requests': current_content,
        'laboratories':lab_content,
        'totalPages': math.ceil(len(practical_requests)/PAGE_SHELF),
        'currentPage': current_page,
        'error': code
    })

'''
Response:
{
    "confirmations": [],
    "currentPage": 1,
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
    "success": true,
    "totalPages": 0
}
'''

@request_view.route('/practical-request/create-requirements', methods=['GET'])
@require_auth(['Laboratory_Manager'])
def confrim_practical_experiment_requirements(payload):
    
    #check if the laboratory manager has school
    lab_mngr, school = check_school(payload['sub'],payload['permissions'])
    laboratories = check_lab(lab_mngr)


    labs_id = []
    for lab in laboratories:
        labs_id.append(lab.number) 
    #check if the request for his labs and exists
    requests = Practical_Experiment_Request.query.filter(and_(Practical_Experiment_Request.school_id == school.id,Practical_Experiment_Request.lab_id.in_(labs_id),
    Practical_Experiment_Request.confirmed == False)).all()

    current_content, current_page = pagination(request,requests)
    #check if there is no any content to display 
    #if len(current_content) == 0:
    #    abort(404, 'لا يوجد تأكيد طلبات لتجارب عملية للعرض')

    lab_content = [lab.format_lab_manager() for lab in laboratories]
     
    return jsonify({
        'success': True,
        'requests': current_content,
        'laboraotries': lab_content
    })


@request_view.route('/practical-request/<int:request_id>/executed', methods=['POST'])
@require_auth(['Laboratory_Manager'])
def confirm_execution_request(payload,request_id):
    
    #check if the laboratory manager has school
    lab_mngr, school = check_school(payload['sub'],payload['permissions'])
    laboratories = check_lab(lab_mngr)

    practical_experiment_data = request.get_json()

    labs_id = []
    for lab in laboratories:
        labs_id.append(lab.number) 
    #check if the request for his labs and exists
    practical_request = Practical_Experiment_Request.query.filter(and_(Practical_Experiment_Request.id==request_id,
    Practical_Experiment_Request.school_id == school.id,Practical_Experiment_Request.lab_id.in_(labs_id))).first_or_404('لا يوجد طلب بهذا الرقم')

    lab_mngr.confirm_execution_request(practical_experiment_data,practical_request)

    response = practical_request.format(payload['permissions'])
    practical_request.close()
     
    return jsonify({
        'success': True,
        'request': response
    })