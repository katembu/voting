import datetime
import uuid
from sqlalchemy import *
from flask import Markup, url_for
from sqlalchemy.orm import relationship
from flask.ext.appbuilder import Model, Base
from flask.ext.appbuilder.models.mixins import AuditMixin, FileColumn, ImageColumn
from flask.ext.appbuilder.filemanager import ImageManager
from utils import today
from app import db

now = today
uid = uuid.uuid4().hex


class SmsloggerLoggedmessage(Model):
    __tablename__ = 'smslogger_loggedmessage'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, default=today)
    direction = Column(String(1), nullable=False)
    text = Column(Text, nullable=False)
    identity = Column(String(100), nullable=False)
    status = Column(String(32))
    response_to_id = Column(ForeignKey(u'smslogger_loggedmessage.id'), index=True)
    response_to = relationship(u'SmsloggerLoggedmessage')

    def incoming(self):
        return self.direction == 'I'

    def outgoing(self):
        return self.direction == 'O'

    def success(self):
        return self.status == 'success'

    def month_year(self):
        date = self.date
        return datetime.datetime(date.year, date.month, 1)

    def year(self):
        date = self.date
        return datetime.datetime(date.year, 1, 1)

    def mdate(self):
        date = self.date
        return datetime.datetime(date.year, date.month, date.day)

class County(AuditMixin, Model):
    __tablename__ = 'counties'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)

    def __repr__(self):
        return self.name


class Constituency(AuditMixin, Model):
    __tablename__ = 'constituencies'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    county_id = Column(ForeignKey(u'counties.id'), nullable=False, index=True)
    county = relationship(u'County')

    def __repr__(self):
        return self.name


class Ward(AuditMixin, Model):
    __tablename__ = 'wards'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    constituency_id = Column(ForeignKey(u'constituencies.id'),
                             nullable=False, index=True)
    constituency = relationship(u'Constituency')

    def __repr__(self):
        return self.name


class PollingStation(Model):
    __tablename__ = 'polling_stations'

    id = Column(Integer, primary_key=True)
    code = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    ward_id = Column(ForeignKey(u'wards.id'), nullable=False, index=True)
    ward = relationship(u'Ward')

    def __repr__(self):
        return self.name


class Scope(AuditMixin, Model):
    __tablename__ = 'scopes'

    id = Column(Integer, unique=True, primary_key=True)
    name = Column(String(255), nullable=False)

    def __repr__(self):
        return self.name


class Post(AuditMixin, Model):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    scope_id = Column(ForeignKey(u'scopes.id'), nullable=False, index=True)
    scope = relationship(u'Scope')

    def __repr__(self):
        return self.name


class Party(AuditMixin, Model):
    __tablename__ = 'parties'

    id = Column(Integer, unique=True, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    short_name = Column(String(255), unique=True, nullable=True)
    motto = Column(String(50), unique=True, nullable=True)
    address = Column(Text(250), nullable=False)
    office_phone = Column(String(20))
    office_mobile = Column(String(50))
    website = Column(String(50))

    def __repr__(self):
        return self.name


class Voters(Model):
    __tablename__ = 'voters'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=False)
    gender = Column(String(50), nullable=False)
    telephone = Column(String(50), nullable=True)
    email = Column(String(50), nullable=True)
    vote_mobile = Column(Boolean, nullable=True)
    voter_pin = Column(String(50), nullable=True)
    document_type = Column(String(2), nullable=False)
    document_number = Column(String(50), nullable=False, unique=True)
    date_of_birth = Column(Date, nullable=False, default=today)
    ward_id = Column(ForeignKey(u'wards.id'), nullable=True)

    ward = relationship(u'Ward')

    __table_args__ = (
        UniqueConstraint('document_type', 'document_number'),
    )

    def __repr__(self):
        return self.full_name()

    def full_name(self):
        return self.first_name+" "+self.middle_name+" "+self.last_name

    def county(self):
        return self.ward.constituency.county

    @property
    def sex(self):
        if(self.gender=="1"):
            return "Male"
        else:
            return "Female"

    def constituency(self):
        return self.ward.constituency


class PollingStation(Model):
    __tablename__ = 'polling_stations'

    id = Column(Integer, primary_key=True)
    code = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    ward_id = Column(ForeignKey(u'wards.id'), nullable=False, index=True)
    ward = relationship(u'Ward')

    def __repr__(self):
        return self.name


class Election(AuditMixin, Model):
    __tablename__ = 'elections'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    uuid = Column(String(50), unique=True, default=uid)
    is_approved = Column(Boolean)
    voting_starts_at_date = Column(DateTime, default=today)
    voting_ends_at_date = Column(DateTime, default=today)
    approved_at_date = Column(DateTime, default=today)
    result_tallied_at_date = Column(DateTime, nullable=True)
    ward_id = Column(Integer, nullable=True, index=True)
    post_id = Column(ForeignKey(u'posts.id'), nullable=False, index=True)

    posts = relationship(u'Post')

    def __repr__(self):
        return str(self.name)+"-"+str(self.posts.name)+" ("+str(self.area())+")"

    def post_title(self):
        return self.posts.name


    def area(self):

        if (self.posts.name == 'Senator' or
           self.posts.name == 'Women Representative' or
           self.posts.name == 'Governor'):
            try:
                p = db.session.query(County).get(self.ward_id)
                return str(p)+" County"
            except:
                return "UNKNOWN"
        if self.posts.name == 'Member of Parliament':
            try:
                p = db.session.query(Constituency).get(self.ward_id)
                return str(p)+" Constituency"
            except:
                return "UNKNOWN"
        if self.posts.name == 'County Assembly Representative':
            try:
                p = db.session.query(Ward).get(self.ward_id)
                return str(p)+" Ward"
            except:
                return "UNKNOWN"
        else:
            return self.posts.name


    def has_started(self):
        '''Returns true if voting has started, false otherwise'''
        return self.voting_starts_at_date != None and self.voting_starts_at_date < datetime.datetime.now()

    def status(self):
        if (self.voting_starts_at_date < datetime.datetime.now() and self.voting_ends_at_date > datetime.datetime.now()):
            return "Completed"

    def is_tallied(self):
        '''Returns true if the election has been tallied, false otherwise'''
        return self.result_tallied_at_date != None



class Delegates(AuditMixin, Model):
    __tablename__ = 'delegates'

    id = Column(Integer, primary_key=True)
    delegate = Column(ForeignKey('voters.id'), nullable=False, index=True)
    photo = Column(ImageColumn)
    candidate_key = Column(String(50), nullable=True, index=True, unique=True)
    election_id = Column(ForeignKey('elections.id'), nullable=False, index=True)
    elections = relationship('Election')
    voters = relationship('Voters')

    __table_args__ = (
        UniqueConstraint('delegate', 'election_id'),
    )

    def __repr__(self):
        return self.delegate

    def pk_election(self):
        return self.elections.wards.id

    def pk_delegate(self):
        return self.voters.wards.id

    def posts(self):
        return self.elections.posts.name

    def full_name(self):
        return self.voters.full_name()

    def photo_img(self):
        im = ImageManager()
        if self.photo:
            return Markup('<a href="' + url_for('DelegatesView.show',
                                                pk=str(self.id)) + '" class="thumbnail"><img src="' +
                          im.get_url(self.photo) + '" alt="Photo" class="img-rounded img-responsive"></a>')
        else:
            return Markup('<a href="' + url_for('DelegatesView.show',
                                                pk=str(self.id)) + '" class="thumbnail"><img src="//:0" alt="Photo" class="img-responsive"></a>')


class Votes(Model):
    __tablename__ = 'votes'

    id = Column(Integer, primary_key=True)
    candidate_id = Column(ForeignKey('delegates.id'), nullable=False, index=True)
    voter_id = Column(ForeignKey('voters.id'), nullable=False, index=True)
    created_on = Column(DateTime, default=datetime.datetime.now, nullable=False)
    election_id = Column(ForeignKey('elections.id'), nullable=False, index=True)
    elections = relationship('Election')
    delegates = relationship('Delegates')
    voters = relationship('Voters')

    __table_args__ = (
        UniqueConstraint('candidate_id', 'voter_id', 'election_id'),
        UniqueConstraint('voter_id', 'election_id'),
    )
