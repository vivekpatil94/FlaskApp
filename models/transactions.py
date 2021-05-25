from app import db
from flask import abort
from sqlalchemy.exc import DataError
from app.component import check_date_format
from sqlalchemy import and_, or_


class Item_Used(db.Model):

    __tablename__ = 'item_used'

    confirm_id = db.Column(db.Integer,db.ForeignKey('confirm_practical_request.request_id'), primary_key=True)
    lab_manager_id = db.Column(db.Integer)
    lab_manager_school_id = db.Column(db.Integer)
    quantity = db.Column(db.Integer, nullable=False)
    lab_item_id = db.Column(db.Integer, db.ForeignKey('laboratory_item.id'), primary_key=True)


    __table_args__ = (
     db.ForeignKeyConstraint( ('lab_manager_id','lab_manager_school_id'), ('laboratory_manager.id','laboratory_manager.school_id'),  ),
     )
    
    manage_item_used = db.relationship('Confirm_Practical_Request', backref='items_used', lazy=True)


    #user_id = db.Column(db.Integer, db.ForeignKey('system_administrator.id'), nullable=False)

    def format(self):
        return{
            'quantity': self.quantity,
            'label': self.lab_item.ministry_item.compound_name(),
            'value': self.lab_item_id
         }

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.flush()       
        except:
            db.session.rollback()
            abort(400, 'لا يوجد عهدة مربتبطة مع رد للحذف')

class Invitation(db.Model):

    __tablename__ = 'invitation'

    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('school_member.id'), primary_key=True)
    message = db.Column(db.String(250))

    school_member_relation = db.relationship('School_Member', backref='invited_list', lazy=True)
    school_relation = db.relationship('School', backref='invited', lazy=True)

    #user_id = db.Column(db.Integer, db.ForeignKey('system_administrator.id'), nullable=False)

    def format(self):
        return{
         'memberId': self.member_id,
         'message': self.message,
         'name': self.school_member.full_name_member(),
         'schoolId': self.school_id
         }

    def format_recieve(self):
        return{
         'memberId': self.member_id,
         'message': self.message,
         'nameSchool': self.school.name,
         'schoolId': self.school_id
         }

    def format_create(self):
        return{
         'value': self.member_id,
         'label': self.message,
         }
       
    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'تم ارسال دعوة من قبل ولم يتم الرد حتى الآن')

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'لا توجد اي دعوة للحذف')

    def close(self):
        db.session.close()

class Practical_Experiment_Request(db.Model):
    __tablename__ = 'practical_experiment_request'

    id = db.Column(db.Integer, primary_key=True)
    class_number = db.Column(db.Integer, nullable=False)
    create_date = db.Column(db.Date, nullable=False)
    execute_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    confirmed = db.Column(db.Boolean, default=False)


    science_teacher_id = db.Column(db.Integer)
    science_teacher_school_id = db.Column(db.Integer)
    lab_id = db.Column(db.Integer)
    school_id = db.Column(db.Integer)

    practical_experiment_id = db.Column(db.Integer, db.ForeignKey('practical_experiment.id'))


    __table_args__ = (
     db.ForeignKeyConstraint( ('school_id', 'lab_id'), ('laboratory.school_id', 'laboratory.number'),  ),
     db.ForeignKeyConstraint( ('science_teacher_id','science_teacher_school_id'), ('science_teacher.id','science_teacher.school_id'),  ),
     )

    request_relation = db.relationship('Confirm_Practical_Request', backref='request', lazy=True)

    #school_member_relation = db.relationship('School_Member', backref='invited_list', lazy=True)
    #school_relation = db.relationship('School', backref='invited', lazy=True)

    #user_id = db.Column(db.Integer, db.ForeignKey('system_administrator.id'), nullable=False)

         
    def format(self,role = 'Science_Teacher'):

        status = None
        confirm_date = ''
        note = ''
        lab_mngr = ''
        items_used = []
        executed = ''
        evaluated = ''
        rate = 0

        
        try:
            confirm = self.his_confirm[0]
            status = confirm.state
            confirm_date = confirm.confirm_date
            note = confirm.note
            lab_mngr = confirm.lab_manager.school_member.full_name_member()
            executed = confirm.executed
            evaluated = confirm.evaluated
            rate = float(confirm.evaluate[0].rate) if confirm.evaluated == True else 0
            items_used = [i.format() for i in confirm.items_used]
        except IndexError:
            #out of index
            con = 'OUT OF INDEX'  
        return{
         'id': self.id,
         'executeDate': self.execute_date,
         'classNo': self.class_number,
         'createDate': self.create_date,
         'quantity': self.quantity,
         'labId': self.lab_id,
         'experimentName': self.practical_experiment.title,
         'courseName': self.practical_experiment.course.name,
         'confirmed': self.confirmed,
         'scienceTeacher': self.created_by.school_member.full_name_member(),
         'status': status,
         'rate': rate,
         'confirmDate': confirm_date,
         'confirmNote': note,
         'executed':executed,
         'evaluated':evaluated,
         'labManager': lab_mngr,
         'items_used': items_used,
         'path': '/practical-experiment/{}'.format(self.id) if role == 'Science_Teacher' else '/practical-request/{}'.format(self.id)
         }

    def format_create(self):
        return{
         'value': self.id,
         'label': self.id,
         }

    def filtering(request,practical_requests):

        #here we get the value from the request and we have the default value if there is not exist in the request 
        id = request.args.get('id')
        lab_id = request.args.get('labId')
        fromExecuteDate = request.args.get('fromExecuteDate')
        toExecuteDate = request.args.get('toExecuteDate')
        fromCreateDate = request.args.get('fromCreateDate')
        toCreateDate = request.args.get('toCreateDate')
        accepted = request.args.get('accepted') 
        rejected = request.args.get('rejected') 
        pending = request.args.get('pending') 

        selection = practical_requests
        try:
            #check from the requiremnets then apply it on the selection (query)
            #filter by id 
            if id is not None and id != '':
                selection = selection.filter(Practical_Experiment_Request.id == id)
            #filter by laboratory id 
            if lab_id is not None and lab_id != '' and lab_id != 'all':
                selection = selection.filter(Practical_Experiment_Request.lab_id == lab_id)
            #filter the request by excute date 
            if fromExecuteDate is not None and fromExecuteDate != '':
                check_date_format(fromExecuteDate)
                selection = selection.filter(Practical_Experiment_Request.execute_date >= fromExecuteDate)
            #filter the request by excute date 
            if toExecuteDate is not None and toExecuteDate != '':
                check_date_format(toExecuteDate)
                selection = selection.filter(Practical_Experiment_Request.execute_date <= toExecuteDate)
            #filter the request by created date
            if fromCreateDate is not None and fromCreateDate != '':
                check_date_format(fromCreateDate)
                selection = selection.filter(Practical_Experiment_Request.create_date >= fromCreateDate)
            #filter the request by created date
            if toCreateDate is not None and toCreateDate != '':
                check_date_format(toCreateDate)
                selection = selection.filter(Practical_Experiment_Request.create_date <= toCreateDate)

            #to deal with data as list 
            copy_selection = []
            key = False

            #filter the request by state if accpected 
            if accepted is not None and accepted.lower() == 'true':
                key = True
                temp_selection = selection.filter(and_(Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,Confirm_Practical_Request.state == True)).all()
                copy_selection.extend(temp_selection)
            #filter the request by state if rejected
            if rejected is not None and rejected.lower() == 'true':
                key = True
                temp_selection = selection.filter(and_(Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,Confirm_Practical_Request.state == False)).all()
                copy_selection.extend(temp_selection)
            #filter the request by confirmed if has not confirm yet 
            if pending is not None and pending.lower() == 'true':
                key = True
                temp_selection = selection.filter(Practical_Experiment_Request.confirmed == False).all()
                copy_selection.extend(temp_selection)

            #return the filtering query 
            if copy_selection is not None and key:
                return copy_selection
            return selection.all()

        #this type of excpetion, for to use the wrong type in query 
        except DataError:
            db.session.rollback()
            return []
        
    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit() 
            return self      
        except:
            db.session.rollback()
            abort(400, 'تم انشاء طلب تجربة عملية من قبل')
    
    def update_laboratory(self,lab_id):
        try:   
            self.lab_id = lab_id
            db.session.flush() 
        except:
            db.session.rollback()
            abort(400, 'لا يوجد مختبر بهذا الرقم')
    
    def update_time(self,classNo,executeDate):
        try:   
            self.execute_date = executeDate
            self.class_number = classNo
            db.session.flush() 
        except:
            db.session.rollback()
            abort(400, 'يرجى اختيار وقت اخر')
    
    def update_quantity(self,quantity):
        try:   
            self.quantity = quantity
            db.session.flush() 
        except:
            db.session.rollback()
            abort(400, 'لا توجد كمية كافية')

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'لا يوجد اي طلب للحذف')
    
    def update_confirmed(self):
        try:   
            self.confirmed = (not self.confirmed)
            db.session.commit() 
        except:
            db.session.rollback()
            abort(400, 'تم تأكيد بالفعل')

    def close(self):
        db.session.close()
    
    def commit(self):
        db.session.commit()

class Confirm_Practical_Request(db.Model):
    __tablename__ = 'confirm_practical_request'

    state = db.Column(db.Boolean, nullable=False)
    confirm_date = db.Column(db.Date, nullable=False)
    note = db.Column(db.String(250), nullable=False)
    evaluated = db.Column(db.Boolean, default=False)
    executed = db.Column(db.Boolean)

    request_id = db.Column(db.Integer, db.ForeignKey('practical_experiment_request.id'),primary_key=True)
    lab_manager_id = db.Column(db.Integer)
    lab_manager_school_id = db.Column(db.Integer)

    __table_args__ = (
     db.ForeignKeyConstraint( ('lab_manager_id','lab_manager_school_id'), ('laboratory_manager.id','laboratory_manager.school_id'),  ),
     )

    request_relation = db.relationship('Practical_Experiment_Request', backref='his_confirm', lazy=True)
    #item_used_relation = db.relationship('Item_Used', backref='confirmation',cascade="all,delete", lazy=True)


    #school_relation = db.relationship('School', backref='invited', lazy=True)

    #user_id = db.Column(db.Integer, db.ForeignKey('system_administrator.id'), nullable=False)

    def format(self):
        return self.request.format('Laboratory_Manager')     

    def format_create(self):
        return{
         'value': self.id,
         'label': self.id,
         }
       
    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()
            return self       
        except:
            db.session.rollback()
            abort(400, 'تم الرد على طلب تجربة عملية من قبل')

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.commit()       
        except Exception as e:
            print(e)
            db.session.rollback()
            abort(400, 'لا يوجد اي رد للحذف')

    def append_item_used(self,item):
        try:
            self.items_used.append(item)
            db.session.flush()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')
        
    def update_state(self):
        try:
            self.state = (not self.state)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

    def update_evaluated(self):
        try:
            self.evaluated = (not self.evaluated)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

    def update_manager_rate(self,lab_mngr_rate):
        try:
            self.lab_manager.update_rate(lab_mngr_rate)
            db.session.flush()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

    def update_executed(self,executed):
        try:
            self.executed = executed
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

    def close(self):
        db.session.close()

    def commit(self):
        db.session.commit()




