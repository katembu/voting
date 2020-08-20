import calendar
import json
import uuid
from random import randint
from sqlalchemy.sql import text
from flask.ext.appbuilder.models.sqla.interface import SQLAInterface
from flask.ext.appbuilder.models.datamodel import SQLAModel
from flask.ext.appbuilder import ModelView, AppBuilder, expose, BaseView, \
                                 has_access
from flask_appbuilder.views import SimpleFormView
from flask_appbuilder.charts.views import DirectChartView, DirectByChartView, GroupByChartView
from flask_appbuilder.models.group import aggregate_count, aggregate_sum
from flask_appbuilder.models.sqla.filters import FilterStartsWith, FilterEqualFunction, FilterEqual
from flask.ext.babelpkg import lazy_gettext as _
from flask import flash, request, render_template
from app import appbuilder, db
from .models import *
from .forms import *
from .utils import generateIdentifier
from flask import jsonify

def pretty_month_year(value):
    return calendar.month_name[value.month] + ' ' + str(value.year)


def pretty_year(value):
    return str(value.year)


class Sms(BaseView):

    default_view = 'incoming'

    @expose('/incoming/', methods=['GET', 'POST'])
    def incoming(self):
        # do something with param1
        # and return to previous page or index

        if request.method == 'POST':

            '''get the phone number that sent the SMS.'''
            if "from" in request.form and request.form['from']:
                sender = request.form["from"]
            if "message" in request.form and request.form["message"]:
                message = request.form["message"]

            if len(sender) > 0 and len(message) > 0:
                '''LOG SMS INTO INCOMING SMS DATABASES'''
                logged = SmsloggerLoggedmessage()
                logged.direction = SMSForm.DIRECTION_INCOMING
                logged.text = message
                logged.identity = sender
                logged.status = SMSForm.STATUS_PENDING
                db.session.add(logged)
                db.session.commit()
                process_sms(logged)
                success = "true"
            else:
                success = "false"

            reply = {"payload": {"success": success}}
            return json.dumps(reply)
        if request.method == 'GET':

            if request.args.get('task'):
                action = request.args.get('task')
                if action == 'send':
                    '''Querry SMS to send'''
                    p = get_pending()
                    if p:
                        payload = {
                          "payload": {
                            "task": "send",
                            "messages": serialized_sms(p)
                          }
                        }
                        return json.dumps(payload)
                    else:
                        pass
        pass


class ScopeView(ModelView):
    datamodel = SQLAInterface(Scope)
    add_columns = edit_columns = ['name']


class PostView(ModelView):
    datamodel = SQLAInterface(Post)
    list_columns = add_columns = edit_columns = ['name', 'scope']


class CountiesView(ModelView):
    datamodel = SQLAInterface(County)
    list_columns = ['name']


class ConstituencyView(ModelView):
    datamodel = SQLAInterface(Constituency)
    list_columns = ['name', 'county']


class WardView(ModelView):
    datamodel = SQLAInterface(Ward)
    list_columns = ['name', 'constituency', 'constituency.county']


class PartyView(ModelView):
    datamodel = SQLAInterface(Party)
    list_columns = ['name', 'short_name']


class SmsloggerView(ModelView):
    datamodel = SQLAInterface(SmsloggerLoggedmessage)
    base_order = ('date', 'desc')
    show_title = "SMS Log"
    add_form = SMSForm
    page_size = 20
    list_columns = ['identity', 'direction', 'text', 'status', 'date']

def get_county():
    return g.ward.constituency.county

class VotersView(ModelView):
    datamodel = SQLAInterface(Voters)
    add_form = MyForm
    edit_form = MyForm
    add_columns = ['first_name', 'middle_name', 'last_name','gender',
                   'date_of_birth', 'document_type', 'document_number',
                   'ward', 'vote_mobile', 'telephone']
    edit_columns = ['first_name', 'middle_name', 'last_name', 'gender',
                    'date_of_birth', 'document_type', 'document_number',
                    'ward', 'vote_mobile', 'telephone']
    list_columns = ['full_name',  'document_number', 'sex', 'telephone', 'ward', 'ward.constituency',
                    'ward.constituency.county']
    search_columns = ['first_name', 'middle_name', 'last_name', 'document_number']
    order_columns = [None]

    def post_add(self, item):
        if item.vote_mobile:
            item.voter_pin = randint(1000, 9999)
            db.session.commit()

            '''PUT this in Outgoing DB'''
            message = "Welcome %s. Youve been registered as voter in %s. "\
                      "Your Mobile voting pin is: %s " % \
                      (item, item.ward, item.voter_pin)

            logged = SmsloggerLoggedmessage()
            logged.direction = SMSForm.DIRECTION_OUTGOING
            logged.text = message
            logged.identity = item.telephone
            logged.status = SMSForm.STATUS_PENDING
            db.session.add(logged)
            db.session.commit()


class DelegatesView(ModelView):
    datamodel = SQLAModel(Delegates)
    add_template = 'add_delegate.html'
    add_form = DelegatesForm
    edit_form = DelegatesForm
    #validators_columns = {'pk_election': [EqualTo('pk_delegate',
    #                       message='fields must match')]}
    add_columns = ['elections', 'delegate', 'photo']
    edit_columns = ['delegate', 'elections']
    list_columns = ['candidate_key', 'photo_img', 'voters', 'posts', 'voters.ward',
                    'voters.ward.constituency', 'voters.ward.constituency.county', 'elections']
    show_fieldsets = [
        ('Personal Information', {'fields': ['voters', 'voters.gender', 'elections', 'photo_img']}),
        (
            'Description',
            {'fields': ['elections'], 'expanded': True}),
    ]
    #search_columns = ['first_name', 'middle_name', 'last_name', 'gender']
    order_columns = [None]

    def post_add(self, item):

        p = item.elections.posts.name.upper()
        item.candidate_key = p[0]+str(generateIdentifier())
        db.session.commit()

    def post_update(self, item):
        p = item.elections.posts.name.upper()
        item.candidate_key = p[0]+str(generateIdentifier())
        db.session.commit()


class ElectionView(ModelView):
    datamodel = SQLAInterface(Election)
    add_template = 'add_election.html'
    add_form = ElectionForm
    edit_form = ElectionForm
    list_columns = ['name', 'post_title', 'area']
    add_columns = ['name', 'posts', 'ward_id', 'voting_starts_at_date', 'voting_ends_at_date',
                   'is_approved']
    edit_columns = ['name', 'posts', 'ward_id', 'voting_starts_at_date', 'voting_ends_at_date',
                    'is_approved']
    related_views = [DelegatesView]
    #search_columns = ['first_name', 'middle_name', 'last_name', 'gender']
    order_columns = [None]

    def post_add(self, item):
        item.uuid = uuid.uuid4().hex
        db.session.commit()


class VotersChartView(GroupByChartView):
    datamodel = SQLAModel(Voters)
    chart_title = 'Registered Voters'
    label_columns = VotersView.label_columns
    chart_type = 'PieChart'
    search_columns = ['gender', 'ward']

    definitions = [
        {
            'label': 'County',
            'group': 'county',
            'series': [(aggregate_count, 'ward.constituency')]
        },
        {
            'label': 'Constituency',
            'group': 'constituency',
            'series': [(aggregate_count, 'ward')]
        },
        {
            'label': 'Gender',
            'group': 'gender',
            'series': [(aggregate_count, 'gender')]
        }
    ]


class SMSReportChartView(GroupByChartView):
    datamodel = SQLAModel(SmsloggerLoggedmessage)
    chart_title = 'SMS Report'
    label_columns = SmsloggerView.label_columns
    search_columns = ['direction']

    definitions = [
        {
            'label': 'Direction',
            'group': 'direction',
            'series': [(aggregate_count, 'direction')]
        },
        {
            'label': 'Date',
            'group': 'mdate',
            'series': [(aggregate_count, 'direction')]
        },
        {
            'label': 'Outgoing',
            'group': 'outgoing',
            'series': [(aggregate_count, 'direction')]
        }
    ]

class API(BaseView):
    route_base = "/api"
    default_view = 'api'

    @expose('/api/')
    def api(self):
        return json.dumps({'version':1})

    @expose('/area/<string:param1>')
    def area(self, param1):
        p = []
        param1 = int(param1)
        results = ""
        #County
        if (param1 == 2 or param1 == 3 or param1 == 4):
            z = "County"
            results = db.session.query(County)
        #get constituency
        if param1 == 5:
            z = "Constituency"
            results = db.session.query(Constituency)
        #get ward
        if param1 == 6:
            z = "Ward"
            results = db.session.query(Ward)

        if results.count() > 0:
            for x in results:
                p.append({'optionValue': x.id, 'optionDisplay':x.name+" "+z})
        #return json.dumps(p)
        return jsonify(results=p)


    @expose('/delegates/<string:param1>')
    def delegates(self, param1):
        p = []
        param1 = int(param1)
        results = ""
        #County
        results = db.session.query(Election).filter_by(id=param1)

        if results.count() == 1:
            el = results[0]
            #County
            if (el.post_id == 2 or el.post_id == 3):
                rr = db.session.execute(text("SELECT voters.id, \
                        concat(voters.first_name, \" \", voters.middle_name, \" \", voters.last_name) AS dname \
                        FROM voters JOIN wards ON wards.id = voters.ward_id \
                        JOIN constituencies ON  wards.constituency_id = constituencies.id \
                        JOIN counties ON  constituencies.county_id = counties.id  \
                        WHERE counties.id =:elid"),params=dict(elid=el.ward_id))
            elif (el.post_id == 4):
                rr = db.session.execute(text("SELECT voters.id, voters.gender, \
                        concat(voters.first_name, \" \", voters.middle_name, \" \", voters.last_name) AS dname \
                        FROM voters JOIN wards ON wards.id = voters.ward_id \
                        JOIN constituencies ON  wards.constituency_id = constituencies.id \
                        JOIN counties ON  constituencies.county_id = counties.id  \
                        WHERE voters.gender=2 and counties.id=:elid"),params=dict(elid=el.ward_id))
            #get constituency
            elif el.post_id == 5:
                rr = db.session.execute(text("SELECT voters.id, \
                        concat(voters.first_name, \" \", voters.middle_name, \" \", voters.last_name) AS dname \
                        FROM voters JOIN wards ON wards.id = voters.ward_id \
                        JOIN constituencies ON  wards.constituency_id = constituencies.id \
                        WHERE constituencies.id =:elid"),params=dict(elid=el.ward_id))
            #get ward
            elif el.post_id == 6:
                rr = db.session.execute(text("SELECT voters.id, \
                        concat(voters.first_name, \" \", voters.middle_name, \" \", voters.last_name) AS dname \
                        FROM voters WHERE voters.ward_id =:elid"),params=dict(elid=el.ward_id))
            else:
                rr = db.session.execute(text("SELECT voters.id, \
                        concat(voters.first_name, \" \", voters.middle_name, \" \", voters.last_name) AS dname \
                        FROM voters"))


            for x in rr:
                p.append({'optionValue': x.id, 'optionDisplay':x.dname })
        #return json.dumps(p)
        return jsonify(results=p)


class MyView(BaseView):
    route_base = "/election"
    default_view = 'results'

    @expose('/result/')
    @has_access
    def results(self):
        el = db.session.query(Election)
        # do something with param1
        # and return it
        # return param1
        # do something with param1
        # and render template with param
        # param1 = 'Goodbye %s' % (param1)
        # self.update_redirect()
        self.update_redirect()
        return self.render_template('method3.html', param1=el)

    @expose('/show/<string:param1>')
    def show(self, param1):
        p = db.session.query(Election).filter_by(uuid=param1)
        if p.count() == 1:
            el = p[0]
            data_k = ""
            info = {"election": el}
            mm = {}
            '''
            results = db.session.query(Votes.election_id, \
                        func.concat(Voters.first_name," ",Voters.middle_name," ",Voters.last_name).label('name'),\
                        func.count(Votes.candidate_id).label('votecount')).\
                        outerjoin(Votes.delegates).\
                        outerjoin(Delegates.delegate).\
                        filter(Votes.election_id==el.id).\
                        group_by(Votes.candidate_id)
            '''

            results = db.session.execute(text("SELECT voters.id, \
                            concat(k.first_name, \" \", k.middle_name, \" \", k.last_name) AS dname, \
                            count(votes.candidate_id) AS votecount FROM votes \
                                JOIN delegates d ON votes.candidate_id  = d.id \
                                JOIN voters   ON votes.voter_id  = voters.id \
                                JOIN voters k ON d.delegate  = k.id \
                                WHERE votes.election_id =:elid \
                                group by votes.candidate_id \
                                ORDER by votecount DESC"),params=dict(elid=el.id))
            r = []
            if results.rowcount > 0:
                #prezzo
                if el.post_id == 1:
                    rrr = db.session.execute(text("SELECT votes.candidate_id as kid, voters.id, counties.id as cid, counties.name as areaname, \
                                    concat(k.first_name, \" \", k.middle_name, \" \", k.last_name) AS dname, \
                                    count(votes.candidate_id) AS votecount FROM votes \
                                        JOIN delegates d ON votes.candidate_id  = d.id \
                                        JOIN voters   ON votes.voter_id  = voters.id \
                                        JOIN voters k ON d.delegate  = k.id \
                                        JOIN wards ON wards.id = voters.ward_id \
                                        JOIN constituencies ON  wards.constituency_id = constituencies.id  \
                                        JOIN counties ON  constituencies.county_id = counties.id  \
                                        WHERE votes.election_id =:elid group by votes.candidate_id, counties.id "),params=dict(elid=el.id))

                #Ward
                if el.post_id == 5:
                    rrr = db.session.execute(text("SELECT votes.candidate_id as kid, voters.id, wards.id as cid, wards.name as areaname, \
                            concat(k.first_name, \" \", k.middle_name, \" \", k.last_name) AS dname, \
                            count(votes.candidate_id) AS votecount FROM votes \
                                JOIN delegates d ON votes.candidate_id  = d.id \
                                JOIN voters   ON votes.voter_id  = voters.id \
                                JOIN voters k ON d.delegate  = k.id \
                                JOIN wards ON wards.id = voters.ward_id \
                                WHERE votes.election_id =:elid group by votes.candidate_id, wards.id "),params=dict(elid=el.id))

                #County
                if (el.post_id == 2 or el.post_id == 3 or el.post_id == 4):
                    rrr = db.session.execute(text("SELECT votes.candidate_id as kid, voters.id, constituencies.id as cid, constituencies.name as areaname, \
                            concat(k.first_name, \" \", k.middle_name, \" \", k.last_name) AS dname, \
                            count(votes.candidate_id) AS votecount FROM votes \
                                JOIN delegates d ON votes.candidate_id  = d.id \
                                JOIN voters   ON votes.voter_id  = voters.id \
                                JOIN voters k ON d.delegate  = k.id \
                                JOIN wards ON wards.id = voters.ward_id \
                                JOIN constituencies ON  wards.constituency_id = constituencies.id \
                                WHERE votes.election_id =:elid group by votes.candidate_id, constituencies.id "),params=dict(elid=el.id))


                mm = self.get_area(rrr)
                for x in results:
                    r.append({'name': x.dname, 'votecount': x.votecount })

            name = el.name
            '''Get Delegates Votesself.update_redirect() '''
            return self.render_template('results.html',
                               result=r, info=info, data_k=mm)
        else:
            return "Erro"

    def get_area(self, results):
        y = {}
        k = {}
        z = {}
        for x in results:
            y[x.cid] = x.areaname
            k[x.kid] = x.dname
            z['area'] = y
            z['delgate'] = k
        return z


db.create_all()

appbuilder.add_view_no_menu(Sms())
appbuilder.add_view_no_menu(MyView())
appbuilder.add_view_no_menu(API())


appbuilder.add_view(VotersView, "Voters", category="Settings")
appbuilder.add_view(DelegatesView, "Delegates", category="Settings")
appbuilder.add_view(ElectionView, "Elections", category="Settings")
appbuilder.add_view(ScopeView, " Scopes", category="Settings")
appbuilder.add_view(PostView, " Post", category="Settings")
appbuilder.add_view(CountiesView, "Counties", category="Settings")
appbuilder.add_view(ConstituencyView, "Constituency", category="Settings")
appbuilder.add_view(WardView, "Ward", category="Settings")
appbuilder.add_view(SmsloggerView, "SMS LOGGER", category="Settings")
appbuilder.add_view(VotersChartView, "Voters Registered", category="Reports")
appbuilder.add_view(SMSReportChartView, "SMS Report", category="Reports")
# appbuilder.add_view(MyView, "Election Results", category="Reports")

appbuilder.add_link("Election Results", href='/election/result', category='Reports')
