from flask import Blueprint,jsonify,request,abort
from app.authentication import require_auth
from app.models.users import Laboratory_Manager
from app.models.resources import School,Laboratory,Laboratory_Item,Remove_Laboratory_Item,Ministry_Item
from app.models.transactions import Practical_Experiment_Request
from app.component import pagination,PAGE_SHELF,check_date_format,getReasonAR
from sqlalchemy import and_, or_,func
import math
import datetime


lab_manager_route = Blueprint('lab_manager_route',__name__)

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

#check school DONE
#check lab DONE
#check the lab into his school DONE

def check_school(mngr_id):
    #check if the laboratory manager has school or not 
    laboratory_manager = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==mngr_id, Laboratory_Manager.activate == True)).first_or_404(description='الرجاء التسجيل في النظام اولاً')
    school = laboratory_manager.his_school
    if school is None:
        abort(404, 'ليس لديك مدرسة مسجلة')
    return laboratory_manager, school

def check_lab(laboratory_manager,school,lab_id):
    #get all the labs that lab manager work on
    labs = laboratory_manager.work_on_labs
    laboratory = Laboratory.query.filter(and_(Laboratory.number==lab_id,Laboratory.school_id==school.id)).first_or_404(description='لا يوجد مختبر بهذا الرقم') 
    if laboratory not in labs:
        abort(401, 'لا يمكنك الوصول الى المختبر')
    return laboratory
    
########## LABORATORY ITEM ##########        

@lab_manager_route.route('/laboratory/<int:lab_id>/item', methods=['POST'])
@require_auth(['Laboratory_Manager'])
def add_item_to_lab(payload,lab_id):
    #check from his school and lab
    laboratory_manager, school = check_school(payload['sub'])
    laboratory = check_lab(laboratory_manager,school,lab_id)

    item_data = request.get_json()

    laboratory_item = laboratory_manager.add_item(item_data,laboratory)
    response = jsonify({ 
        'success': True,
        'laboratoryItem': laboratory_item.format(),
        'message': 'تم اضافة عهدة جديدة بنجاح'
        })

    laboratory_manager.close() 
    return response

'''
Request:
{
    "itemId": 20,
    "expireDate": 10, 
    "quantity": "MM",
    "hasExpireDate: "False"
}
Response:
{
    "laboratoryItem": {
        "addedDate": "Tue, 16 Feb 2021 00:00:00 GMT",
        "expireDate": "Thu, 25 May 2023 00:00:00 GMT",
        "id": 5,
        "labId": 1,
        "name": "X - gram",
        "quantity": 5
    },
    "message": "تم اضافة عهدة جديدة بنجاح",
    "success": true
}
'''

@lab_manager_route.route('/laboratory/<int:lab_id>/item', methods=['PATCH'])
@require_auth(['Laboratory_Manager'])
def modify_lab_item(payload,lab_id):

    laboratory_manager, school = check_school(payload['sub'])
    laboratory = check_lab(laboratory_manager,school,lab_id)

    item_data = request.get_json()

    laboratory_item = laboratory_manager.edit_item(item_data,laboratory)
    response = jsonify({ 
        'success': True,
        'laboratoryItem': laboratory_item.format(),
        'message': 'تم تعديل عهدة جديدة بنجاح'
        })

    laboratory_manager.close() 
    return response

'''
Request:
{
    "itemId": 5,
    "expireDate": "5/25/2023", 
    "quantity": 5
}
Response:
{
    "laboratoryItem": {
        "addedDate": "Tue, 16 Feb 2021 00:00:00 GMT",
        "expireDate": "Thu, 25 May 2023 00:00:00 GMT",
        "id": 5,
        "labId": 1,
        "name": "X - gram",
        "quantity": 10
    },
    "message": "تم تعدبل العهدة بنجاح",
    "success": true
}
'''

@lab_manager_route.route('/laboratory/<int:lab_id>/item', methods=['GET'])
@require_auth(['Laboratory_Manager'])
def display_all_laboratory_item(payload,lab_id):

    laboratory_manager, school = check_school(payload['sub'])
    laboratory = check_lab(laboratory_manager,school,lab_id)
    #without deleted and for him only
    #get all the item in his lab to display 
    lab_items = Laboratory_Item.query.filter(and_(Laboratory_Item.school_id == school.id,Laboratory_Item.lab_id == laboratory.number,Laboratory_Item.deleted == False))
    lab_items,msg_exp = Laboratory_Item.filtering(request,lab_items)
    current_content, current_page = pagination(request,lab_items)

    #check if there is no any content to display     
    success = True
    code = 200
    if len(current_content) == 0:
        code = 204
        success = False

    items = Ministry_Item.query.order_by(Ministry_Item.id).all()
    item_content = [item.format_create() for item in items]

    response = jsonify({
        'success': success,
        'laboratoryItems': current_content,
        'totalPages': math.ceil(len(lab_items)/PAGE_SHELF),
        'currentPage': current_page,
        'ministryItems': item_content,
        'expireMessage': msg_exp,
        'error': code
         })
    
    laboratory_manager.close() 
    return response 

'''
Request:
para: page=1
Response:
{
    "laboratoryItem": {
        "addedDate": "Tue, 16 Feb 2021 00:00:00 GMT",
        "expireDate": "Thu, 25 May 2023 00:00:00 GMT",
        "id": 5,
        "labId": 1,
        "name": "X - gram",
        "quantity": 10
    },
    "message": "تم تعدبل العهدة بنجاح",
    "success": true
}
'''

@lab_manager_route.route('/laboratory/<int:lab_id>/item/<int:item_id>', methods=['GET'])
@require_auth(['Laboratory_Manager'])
def dsiplay_specific_laboratory_item(payload,lab_id,item_id):

    laboratory_manager, school = check_school(payload['sub'])
    laboratory = check_lab(laboratory_manager,school,lab_id)
    #get the laboratory item based on id
    laboratory_item = Laboratory_Item.query.filter_by(id=item_id).first_or_404(description='لا توجد عهدة بهذا الرقم')
    #get all the items in his lab 
    lab_items = laboratory.lab_items
    #if the lab manager has no access to this laboratory item
    if laboratory_item not in lab_items:
        abort(401, description='لا يمكنك الوصول الى العهدة المطلوبة')
    #check if the laboratory item was deleted before
    if laboratory_item.deleted == True:
        reason = laboratory_item.laboratory_item_removed[0].reason
        reasonAr = getReasonAR(reason)
        abort(400, 'العهدة محذوفة, السبب: {}'.format(reasonAr))
    
    items = Ministry_Item.query.order_by(Ministry_Item.id).all()
    item_content = [item.format_create() for item in items]

    response = jsonify({ 
        'success': True,
        'laboratoryItem': laboratory_item.format(),
        'ministryItems': item_content
        })
    
    laboratory_manager.close() 
    return response 

'''
Request:
route: /laboratory/1/item/12
Response:
{
    "laboratoryItem": {
        "addedDate": "Tue, 16 Feb 2021 00:00:00 GMT",
        "expireDate": "Sat, 18 Feb 2023 00:00:00 GMT",
        "id": 12,
        "labId": 1,
        "name": "AB - GRAM",
        "quantity": 10
    },
    "success": true
}
'''

@lab_manager_route.route('/laboratory/<int:lab_id>/item/<int:item_id>', methods=['DELETE'])
@require_auth(['Laboratory_Manager'])
def delete_laboratory_item(payload,lab_id,item_id):

    laboratory_manager, school = check_school(payload['sub'])
    laboratory = check_lab(laboratory_manager,school,lab_id)
    #get the laboratory item 
    laboratory_item = Laboratory_Item.query.filter_by(id=item_id).first_or_404(description='لا توجد عهدة بهذا الرقم')

    item_data = request.get_json()
    removed_item = laboratory_manager.remove_item(item_data,laboratory_item)

    response = jsonify({ 
        'success': True,
        'laboratoryItem': removed_item.format()
        })
    
    laboratory_manager.close() 
    return response 

'''
Request:
route: /laboratory/1/item/14
Response:
{
    "laboratoryItem": {
        "id": 14,
        "note": "by mistake",
        "reason": "broke",
        "removeDate": "Wed, 17 Feb 2021 00:00:00 GMT"
    },
    "success": true
}
'''

@lab_manager_route.route('/laboratory/<int:lab_id>/item-deleted', methods=['GET'])
@require_auth(['Laboratory_Manager'])
def display_all_deleted_laboratory_item(payload,lab_id):

    laboratory_manager, school = check_school(payload['sub'])
    laboratory = check_lab(laboratory_manager,school,lab_id)

    #get only removed item for specicic laboratory by join the laboratory item and remove laborator item and laboratory 
    removed_items = Remove_Laboratory_Item.query.filter(and_(Remove_Laboratory_Item.lab_item == Laboratory_Item.id,
     Laboratory_Item.lab_id == laboratory.number,Laboratory_Item.school_id == school.id))
    removed_items = Remove_Laboratory_Item.filtering(request,removed_items)

    current_content, current_page = pagination(request,removed_items)
    #check if there is no any content to display 
    success = True
    code = 200
    if len(current_content) == 0:
        code = 204
        success = False

    items = Ministry_Item.query.order_by(Ministry_Item.id).all()
    item_content = [item.format_create() for item in items]
    
    response = jsonify({
        'success': success,
        'removedLaboratoryItems': current_content,
        'totalPages': math.ceil(len(removed_items)/PAGE_SHELF),
        'currentPage': current_page,
        'ministryItems': item_content,
        'error': code
         })
    
    laboratory_manager.close() 
    return response 

'''
Request:
para: page=1
Response:
{
    "currentPage": 1,
    "laboratoryItems": [
        {
            "id": 12,
            "note": "by mistake",
            "reason": "broke",
            "removeDate": "Wed, 17 Feb 2021 00:00:00 GMT"
        },
        {
            "id": 13,
            "note": "by mistake",
            "reason": "broke",
            "removeDate": "Wed, 17 Feb 2021 00:00:00 GMT"
        },
        {
            "id": 14,
            "note": "by mistake",
            "reason": "broke",
            "removeDate": "Wed, 17 Feb 2021 00:00:00 GMT"
        }
    ],
    "success": true,
    "totalPages": 1
}
'''

@lab_manager_route.route('/laboratory-item/create-requirements', methods=['GET'])
@require_auth(['Laboratory_Manager'])
def item_requirements(payload):

    laboratory_manager, school = check_school(payload['sub'])

    items = Ministry_Item.query.order_by(Ministry_Item.id).all()
    item_content = [item.format_create() for item in items]

    response = jsonify({
        'success': True,
        'ministryItems': item_content
         })
    
    laboratory_manager.close() 
    return response 

'''
Request:
route: /laboratory-item/create-requirements
Response:
{
    "ministryItems": [
        {
            "label": "AB - GRAM",
            "value": 7
        },
        {
            "label": "X - gram",
            "value": 8
        },
        {
            "label": "Y - gram",
            "value": 10
        },
        {
            "label": "G - gram",
            "value": 11
        },
        {
            "label": "H - gram",
            "value": 12
        },
        {
            "label": "A - gram",
            "value": 13
        },
        {
            "label": "C - gram",
            "value": 14
        }
    ],
    "success": true
}
'''

@lab_manager_route.route('/school-laboratory/<int:lab_id>', methods=['GET'])
@require_auth(['Laboratory_Manager'])
def display_specific_laboratory(payload,lab_id):

    laboratory_manager, school = check_school(payload['sub'])
    laboratory = check_lab(laboratory_manager,school,lab_id)

    items = Ministry_Item.query.order_by(Ministry_Item.id).all()
    item_content = [item.format_create() for item in items]

    response = jsonify({
        'success': True,
        'laboratory': laboratory.format_lab_manager(),
        'ministryItems': item_content 
         })
    
    laboratory_manager.close() 
    return response 

'''
Request:
route: /school-laboratory/1
Response:
{
    "laboratory": {
        "id": 1,
        "laboratoryManagers": [
            {
                "label": "Fouad A Ramadan",
                "value": 62
            }
        ],
        "ministryItems": [
            {
                "label": "AB - GRAM",
                "value": 7
            },
            {
                "label": "X - gram",
                "value": 8
            },
            {
                "label": "Y - gram",
                "value": 10
            },
            {
                "label": "G - gram",
                "value": 11
            },
            {
                "label": "H - gram",
                "value": 12
            },
            {
                "label": "A - gram",
                "value": 13
            },
            {
                "label": "C - gram",
                "value": 14
            }
        ]
    },
    "success": true
}
'''

@lab_manager_route.route('/school-laboratory', methods=['GET'])
@require_auth(['Laboratory_Manager'])
def display_all_laboratory(payload):

    laboratory_manager, school = check_school(payload['sub'])

    labs = laboratory_manager.work_on_labs
    lab_content = [lab.format_lab_manager() for lab in labs]

    items = Ministry_Item.query.order_by(Ministry_Item.id).all()
    item_content = [item.format_create() for item in items]

    response = jsonify({
        'success': True,
        'laboratories': lab_content,
        'ministryItems': item_content 
         })
    
    laboratory_manager.close() 
    return response 

'''
Request:
route: /school-laboratory/1
Response:
{
    "laboratory": {
        "id": 1,
        "laboratoryManagers": [
            {
                "label": "Fouad A Ramadan",
                "value": 62
            }
        ],
        "ministryItems": [
            {
                "label": "AB - GRAM",
                "value": 7
            },
            {
                "label": "X - gram",
                "value": 8
            },
            {
                "label": "Y - gram",
                "value": 10
            },
            {
                "label": "G - gram",
                "value": 11
            },
            {
                "label": "H - gram",
                "value": 12
            },
            {
                "label": "A - gram",
                "value": 13
            },
            {
                "label": "C - gram",
                "value": 14
            }
        ]
    },
    "success": true
}
'''
