from app import db
from flask import abort
from sqlalchemy.exc import DataError


class Visit(db.Model):

    __tablename__ = 'visit'
    id = db.Column(db.Integer, primary_key=True)
    visit_date =  db.Column(db.Date, nullable=False)
    note = db.Column(db.String(250))
    closed = db.Column(db.Boolean, default=False)
    educational_supervisor_id = db.Column(db.Integer,db.ForeignKey('educational_supervisor.id'))
    school_id = db.Column(db.Integer,db.ForeignKey('school.id'))

    school = db.relationship('School', backref='visits', lazy=True)

    def format(self):
        return {
            'visitId': self.id,
            'visitDate': self.visit_date,
            'note': self.note,
            'closed': self.closed,
            'schoolId': self.school_id,
            'schoolName': self.school.name,
            'areaName': self.school.area.name,
            'cityName': self.school.area.city.name
        }

    def insert(self):
        try:   
            db.session.add(self)
            db.session.flush()
            return self       
        except:
            db.session.rollback()
            abort(400, 'الزيارة قد انشأت من قبل') 

    def update_visit(self,school_id,date):
        try:
            self.school_id = school_id
            self.visit_date = date
            db.session.commit()
            return self
        except:
            db.session.rollback()   
            abort(400, ' الزيارة مضافة بالفعل') 
    
    def delete(self):
        try:              
            db.session.delete(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'لا يمكن حذف السؤال الان, يرجى المحاولة لاحقاً')
        finally:
            db.session.close()

    def close_visit(self):
        try:
            self.closed = (not self.closed)
            db.session.commit()
            return self
        except:
            db.session.rollback()   
            abort(400, ' الزيارة مضافة بالفعل') 

class Evaluate_Type(db.Model):

    __tablename__ = 'evaluate_type'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False,unique=True)

    question_relation = db.relationship('Question', backref='evlauate_type', lazy=True)

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'النوع مضاف بالفعل مضافة بالفعل')

    def delete(self):
        try:              
            db.session.delete(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'المدينة محذوفة بالفعل')
        finally:
            db.session.close()

    def update_name(self,name):
        try:
            self.name = name
            db.session.commit()
        except:
            db.session.rollback()   
            abort(400, ' المدينة مضافة بالفعل') 

class Evaluate(db.Model):

    __tablename__ = 'evaluate'
    id = db.Column(db.Integer, primary_key=True)
    date =  db.Column(db.Date, nullable=False)
    evaluate_type = db.Column(db.Integer,db.ForeignKey('evaluate_type.id'))

    def insert(self):
        try:   
            db.session.add(self)
            db.session.flush()  
            return self     
        except:
            db.session.rollback()
            abort(400, 'يرجى اختيار نوع التقييم المتاح في النظام')
    
    def commit(self):
        try:
            db.session.commit()
            return self     
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')
    
    def format(self):
        return {
            'id': self.id,
            'date': self.date
        }

class Evaluate_Laboratory_Manager(db.Model):

    __tablename__ = 'evaluate_laboratory_manager'
    id = db.Column(db.Integer,db.ForeignKey('evaluate.id'), primary_key=True)
    laboratory_manager_id = db.Column(db.Integer)
    laboratory_manager_school_id = db.Column(db.Integer)
    visit_id = db.Column(db.Integer,db.ForeignKey('visit.id'))
    rate = db.Column(db.Numeric(precision=3,scale=2), default= 0.00)

    laboratory_manager = db.relationship('Laboratory_Manager', backref='evaluate_by_educational_supervisor', lazy=True)

    __table_args__ = (
     db.ForeignKeyConstraint( ('laboratory_manager_id','laboratory_manager_school_id'), ('laboratory_manager.id','laboratory_manager.school_id'),  ),
     )
    
    
    def insert(self):
        try:   
            db.session.add(self)
            db.session.flush()      
        except:
            db.session.rollback()
            abort(400, 'لا توجد تجربة عملية للتقييم')

    def update_lab_mngr_rate(self,new_rate):
        try:
            lab_manager = self.laboratory_manager   
            lab_manager.update_rate(new_rate)
            db.session.commit()  
            return lab_manager    
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

class Evaluate_Laboratory(db.Model):

    __tablename__ = 'evaluate_laboratory'
    id = db.Column(db.Integer,db.ForeignKey('evaluate.id'), primary_key=True)
    laboratory_id = db.Column(db.Integer)
    school_id = db.Column(db.Integer)
    visit_id = db.Column(db.Integer,db.ForeignKey('visit.id'))
    rate = db.Column(db.Numeric(precision=3,scale=2), default= 0.00)

    __table_args__ = (
     db.ForeignKeyConstraint( ('school_id', 'laboratory_id'), ('laboratory.school_id', 'laboratory.number'),  ),
     )

    laboratory = db.relationship('Laboratory', backref='evaluate', lazy=True)
    
    def insert(self):
        try:   
            db.session.add(self)
            db.session.flush()      
        except:
            db.session.rollback()
            abort(400, 'يوجد تقييم بالفعل')   

    def update_lab_rate(self,new_rate):
        try:
            lab = self.laboratory   
            lab.update_rate(new_rate)
            db.session.commit()  
            return lab    
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')
    
class Evaluate_Experiment(db.Model):

    __tablename__ = 'evaluate_experiment'
    id = db.Column(db.Integer,db.ForeignKey('evaluate.id'), primary_key=True)
    confirm_id = db.Column(db.Integer,db.ForeignKey('confirm_practical_request.request_id'), unique=True)
    rate = db.Column(db.Numeric(precision=3,scale=2), default= 0.00)

    confirmation = db.relationship('Confirm_Practical_Request', backref='evaluate', lazy=True)


    def insert(self):
        try:   
            db.session.add(self)
            db.session.flush()      
        except:
            db.session.rollback()
            abort(400, 'لا توجد تجربة عملية للتقييم')

class Question(db.Model):

    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(300), nullable=False)
    evaluate_type = db.Column(db.Integer,db.ForeignKey('evaluate_type.id'))

    answer_relation = db.relationship('Answer', backref='question', cascade="all,delete" ,lazy=True)

    def format(self):
        from app.component import getEvaluateTypeAR 

        return {
            'id': self.id,
            'text': self.text,
            'evaluateType': self.evaluate_type,
            'evaluateTypeAR': getEvaluateTypeAR(self.evaluate_type),
            'path': '/question/{}'.format(self.id)
        }

    def format_create(self):
        return{
         'value': self.id,
         'label': self.text
         }
    
    def format_question(self):
        return{
         'id': self.id,
         'text': self.text,
         'options': self.getOptions()
         }

    def getOptions(self):
        return [
            {'label': 'نعم',
             'value': 1},
            {'label': 'لا',
             'value': 0}
        ]

    def filtering(request,questions):

        #here we get the value from the request and we have the default value if there is not exist in the request 
        id = request.args.get('id')
        evaluate_type = request.args.get('evaluateType')
        text = request.args.get('text')

        selection = questions
        try:
            #check from the requiremnets then apply it on the selection (query)
            #filter the questions by id
            if id is not None and id != '':
                selection = selection.filter(Question.id == id) 
            #filter the questions by evaluate type
            if evaluate_type is not None and evaluate_type != '' and evaluate_type.lower() != 'all':
                selection = selection.filter(Question.evaluate_type == evaluate_type) 
            #filter the questions by text
            if text is not None and text != '':
                text = '%{}%'.format(text)
                selection = selection.filter(Question.text.ilike(text))
                
            #return the filtering query 
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
            abort(400, 'يرجى اختيار نوع التقييم المتاح في النظام')

    def delete(self):
        try:              
            db.session.delete(self)
            db.session.commit() 
        except Exception as e:
            print(e.__class__.__name__)
            db.session.rollback()
            abort(400, 'لا يمكن حذف السؤال الان, يرجى المحاولة لاحقاً')      
        except:
            db.session.rollback()
            abort(400, 'لا يمكن حذف السؤال الان, يرجى المحاولة لاحقاً')
        finally:
            db.session.close()

    def update_evaluate_type(self,evaluate_type):
        try:
            self.evaluate_type = evaluate_type
            db.session.flush()
        except:
            db.session.rollback()
            abort(400, 'يرجى اختيار نوع التقييم المتاح في النظام')

    def append(self,user):
        try:
            self.modifier.append(user)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')  
        finally:
            db.session.close()  

class Answer(db.Model):

    __tablename__ = 'answer'
    id = db.Column(db.Integer, primary_key=True)
    answer_value = db.Column(db.Integer, nullable=False)
    question_id = db.Column(db.Integer,db.ForeignKey('question.id'))
    evaluate_id = db.Column(db.Integer,db.ForeignKey('evaluate.id'))

    question_relation = db.relationship('Question', backref='answers', lazy=True)

    def insert(self):
        try:   
            db.session.add(self)
            db.session.flush()  
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')


Manage_Evaluate_Type = db.Table('manage_evaluate_type',
    db.Column('user_id', db.Integer, db.ForeignKey('system_administrator.id'), nullable=False),
    db.Column('type_id', db.Integer, db.ForeignKey('evaluate_type.id'), nullable=False)
)           

Manage_Question = db.Table('manage_question',
    db.Column('user_id', db.Integer, db.ForeignKey('system_administrator.id'), nullable=False),
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), nullable=False)
) 

accounts_table = db.table('account',
    db.column('id', db.Integer),
    db.column('name', db.String),
)

