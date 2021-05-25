from flask import Blueprint,jsonify,request,abort
from app.authentication import require_auth
from sqlalchemy import and_, or_, func,exists
from app.models.transactions import Confirm_Practical_Request, Practical_Experiment_Request
from app.models.evaluate_system import Question,Evaluate_Experiment,Evaluate_Type,Visit
from app.models.users import Science_Teacher,Educational_Supervisor,Laboratory_Manager
from app.component import pagination,PAGE_SHELF,DATE_FORMAT,get_class_number
from app.models.resources import Laboratory
import datetime,pytz,math



evaluate_view = Blueprint('evaluate_view',__name__)

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
'''

def check_user(user_id,role):
    user = None
    school = None
    #check if the educational supervisor or science teacher in the system
    if role == 'Educational_Supervisor':
        user = Educational_Supervisor.query.filter(and_(Educational_Supervisor.id==user_id)).first_or_404(description='الرجاء التسجيل في النظام اولاً')
    elif role == 'Science_Teacher':
        user = Science_Teacher.query.filter(and_(Science_Teacher.id==user_id, Science_Teacher.activate == True)).first_or_404(description='الرجاء التسجيل في النظام اولاً')
        #check if the science teacher has school or not 
        school = user.his_school
        if school is None:
            abort(404, 'ليس لديك مدرسة مسجلة')
    else:
        abort(404, 'الرجاء التسجيل في النظام اولاً')

    return user, school

    
########## EVALUATE ##########

@evaluate_view.route('/practical-experiment/<int:experiment_id>/evaluate', methods=['POST'])
@require_auth(['Science_Teacher'])
def evaluate_process(payload,experiment_id):

    user, school = check_user(payload['sub'],payload['permissions'])

    #get JSON request
    evaluate_data = request.get_json()
    #invoke function of evaluate
    practical_request = user.evaluate_experiment(evaluate_data,experiment_id)
    response = practical_request.format()
    practical_request.close()

    return jsonify({
        'success': True,
        'practicalExperiment':response
    })

'''
Response:
{
 "answers": [
     {"answer": 1,
     "questionId": 5     
     },
    {"answer": 5,
     "questionId": 6     
     }
 ]
}
Request:
{
    "date": "Tue, 16 Mar 2021 00:00:00 GMT",
    "id": 1004
}
'''

@evaluate_view.route('/visit/current/laboratory/<int:lab_id>/evaluate', methods=['POST'])
@require_auth(['Educational_Supervisor'])
def evaluate_laboratory(payload,lab_id):

    user, school = check_user(payload['sub'],payload['permissions'])

    #check if there is any visit right now [STATUS: OPEN]
    visit = Visit.query.filter(and_(Visit.educational_supervisor_id == user.id, Visit.closed == False)).first_or_404(description='لا توجد زيارات في الوقت الحالي')

    #get JSON request
    evaluate_data = request.get_json()
    #invoke function of evaluate
    laboraotory = user.evaluate_laboratory(evaluate_data,visit,lab_id)
    response = laboraotory.format_evaluate()
    laboraotory.close()

    return jsonify({
        'success': True,
        'laboratory':response
    })

'''
Response:
{
 "answers": [
     {"answerId": 1,
     "questionId": 7     
     },
    {"answerId": 1,
     "questionId": 8     
     }
 ]
}
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
        "path": "/laboratory/1"
    },
    "success": true
}
'''

@evaluate_view.route('/visit/current/laboratory-manager/<int:lab_mngr_id>/evaluate', methods=['POST'])
@require_auth(['Educational_Supervisor'])
def evaluate_laboratory_manager(payload,lab_mngr_id):

    user, school = check_user(payload['sub'],payload['permissions'])

    #check if there is any visit right now [STATUS: OPEN]
    visit = Visit.query.filter(and_(Visit.educational_supervisor_id == user.id, Visit.closed == False)).first_or_404(description='لا توجد زيارات في الوقت الحالي')

    #get JSON request
    evaluate_data = request.get_json()
    #invoke function of evaluate
    laboraotory_manager = user.evaluate_laboratory_manager(evaluate_data,visit,lab_mngr_id)
    response = laboraotory_manager.format_evaluate()
    laboraotory_manager.close()

    return jsonify({
        'success': True,
        'laboratoryManager':response
    })

'''
Response:
{
 "answers": [
     {"answerId": 1,
     "questionId": 7     
     },
    {"answerId": 1,
     "questionId": 8     
     }
 ]
}
Request:
{
    "practicalExperiment": {
        "id": 1,
        "labManagers": [
            {
                "label": "Fouad A Ramadan",
                "value": 62
            }
        ],
        "path": "/laboratory/1"
    },
    "success": true
}
'''

########## EVALUATE REQUIREMENT ##########

@evaluate_view.route('/visit/current/laboratory-manager/<int:lab_mngr_id>/evaluate', methods=['GET'])
@require_auth(['Educational_Supervisor'])
def get_question_evaluate_laboratory_manager(payload,lab_mngr_id):

    user, school = check_user(payload['sub'],payload['permissions'])

    #check if there is any visit right now [STATUS: OPEN]
    visit = Visit.query.with_entities(Visit.school_id).filter(and_(Visit.educational_supervisor_id == user.id,
    Visit.closed == False)).first_or_404(description='لا توجد زيارات في الوقت الحالي')

    #get only the id of evaluate type, to get all the questions
    evaluate = Evaluate_Type.query.with_entities(Evaluate_Type.id).filter_by(title='evaluate_laboratory_manager').first_or_404('لا يوجد نوع تقييم محدد')
    questions = Question.query.filter_by(evaluate_type=evaluate.id).all()
    questions = [q.format_question() for q in questions]
    #get the lab manager 
    laboraotory_manager = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==lab_mngr_id, Laboratory_Manager.school_id == visit.school_id,
    Laboratory_Manager.activate == True)).first_or_404(description='لا يوجد محضر مختبر بهذا الرقم')
    response = laboraotory_manager.format_evaluate()

    laboraotory_manager.close()

    return jsonify({
        'success': True,
        'questions':questions,
        'laboratoryManager': response
    })

'''
response:
{
    "questions": [
        {
            "id": 7,
            "options": [
                {
                    "label": "نعم",
                    "value": 1
                },
                {
                    "label": "لا",
                    "value": 0
                }
            ],
            "text": "Is Clean ?"
        },
        {
            "id": 8,
            "options": [
                {
                    "label": "نعم",
                    "value": 1
                },
                {
                    "label": "لا",
                    "value": 0
                }
            ],
            "text": "Is Has a Safety Equipement ?"
        }
    ],
    "success": true
}
'''

@evaluate_view.route('/visit/current/laboratory/<int:lab_id>/evaluate', methods=['GET'])
@require_auth(['Educational_Supervisor'])
def get_question_evaluate_laboratory(payload,lab_id):

    user, school = check_user(payload['sub'],payload['permissions'])
    #check if there is any visit right now [STATUS: OPEN]
    visit = Visit.query.with_entities(Visit.school_id).filter(and_(Visit.educational_supervisor_id == user.id,
    Visit.closed == False)).first_or_404(description='لا توجد زيارات في الوقت الحالي')
    
    #get only the id of evaluate type, to get all the questions
    evaluate = Evaluate_Type.query.with_entities(Evaluate_Type.id).filter_by(title='evaluate_laboratory').first_or_404('لا يوجد نوع تقييم محدد')
    questions = Question.query.filter_by(evaluate_type=evaluate.id).all()
    questions = [q.format_question() for q in questions]
    #get the laboratory
    laboraotory = Laboratory.query.filter(and_(Laboratory.school_id== visit.school_id, Laboratory.number==lab_id)).first_or_404('لا يوجد مختبر بهذا الرقم')

    response = laboraotory.format_evaluate()
    laboraotory.close()

    return jsonify({
        'success': True,
        'questions':questions,
        'laboratory': response
    })


@evaluate_view.route('/evaluate', methods=['GET'])
@require_auth(['Science_Teacher','Educational_Supervisor'])
def get_available_evaluate(payload):

    response = ''
    user, school = check_user(payload['sub'],payload['permissions'])
    evaluate_type = request.args.get('evaluateType')

    if payload['permissions'] == 'Science_Teacher':
        #select all request has not been evaluated yet and has confirmed and executed. Using not exists into evaluate table 
        #get time zone of KSA
        tz = pytz.timezone('Asia/Riyadh')
        time = datetime.datetime.now(tz)
        #convert to needed format
        now = time.strftime(DATE_FORMAT)
        #get the class number which science teacher can evaluate
        class_number_now = get_class_number(time)
        #query
        sub = ~ Evaluate_Experiment.query.filter(Evaluate_Experiment.confirm_id == Confirm_Practical_Request.request_id).exists()
        selection = Practical_Experiment_Request.query.filter(and_(Practical_Experiment_Request.science_teacher_id == user.id, Practical_Experiment_Request.school_id == school.id,
        or_(Practical_Experiment_Request.execute_date < now,(and_(Practical_Experiment_Request.execute_date == now,
        Practical_Experiment_Request.class_number < class_number_now))),
        Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,Confirm_Practical_Request.state == True,sub))
        #apply some filter on query 
        practical_experiments = Practical_Experiment_Request.filtering(request,selection)
        #pagination
        current_content, current_page = pagination(request,practical_experiments)
        #check if there is no any content to display 
        success = True
        code = 200
        if len(current_content) == 0:
            code = 204
            success = False
            
        #get only the id of evaluate type, to get all the questions
        evaluate = Evaluate_Type.query.with_entities(Evaluate_Type.id).filter_by(title='evaluate_experiment').first_or_404('لا يوجد نوع تقييم محدد')
        questions = Question.query.filter_by(evaluate_type=evaluate.id).all()
        questions = [q.format_question() for q in questions]

        response = {
            'success': success,
            'practicalExperiments': current_content,
            'questions': questions,
            'totalPages': math.ceil(len(practical_experiments)/PAGE_SHELF),
            'currentPage': current_page,
            'error': code
        }

    elif payload['permissions'] == 'Educational_Supervisor':
        response = 'H'

    return response

'''
Request:
para = evaluateType and other filter
Response:
role: Science_Teacher 
{
    "currentPage": 1,
    "practicalExperiments": [
        {
            "classNo": 1,
            "confirmDate": "Tue, 16 Mar 2021 00:00:00 GMT",
            "confirmNote": "OKAY",
            "confirmed": true,
            "courseName": "CPIT-401",
            "createDate": "Thu, 25 Feb 2021 00:00:00 GMT",
            "executeDate": "Mon, 15 Mar 2021 00:00:00 GMT",
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
            "path": "/practical-experiment/9",
            "quantity": 10,
            "scienceTeacher": "Fouad A Ramadan",
            "status": true
        }
    ],
    "questions": [
        {
            "label": "How many gram of sand in laboratory ?",
            "value": 5
        },
        {
            "label": "How many bottle in laboratory ?",
            "value": 6
        }
    ],
    "success": true,
    "totalPages": 1
}
'''

'''
        #select all request has not been confirmed yet. Using not exists into Confirm table 
        sub = ~ Confirm_Practical_Request.query.filter(Confirm_Practical_Request.request_id == Practical_Experiment_Request.id).exists()
        test = Practical_Experiment_Request.query.filter(and_(sub,Practical_Experiment_Request.school_id == school.id)).all()
'''
