from sqlalchemy.sql.expression import null
from sqlalchemy import String,Boolean,Integer,Column,Text,DateTime,ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Member(Base):
    __tablename__ = 'members'
    naf_number = Column(Integer, primary_key=True)
    naf_name = Column(String(255), nullable=False)
    country = Column(String(255))
    registration_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime)


class Variant(Base):
    __tablename__ = 'variants'
    variantid = Column(Integer, primary_key=True)
    variantname = Column(String(255), nullable=False)
    variantorder = Column(Integer)


class Race(Base):
    __tablename__ = 'races'
    raceid = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    reroll_cost = Column(Integer)
    apoth = Column(String(1))
    race_order = Column(Integer)
    selectable = Column(String(255))
    race_count = Column(String(3))


class Award(Base):
    __tablename__ = 'awards'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    label = Column(String(255), nullable=False)
    award_order = Column(Integer)


class Tournament(Base):
    __tablename__ = 'tournaments'
    tournamentid = Column(Integer, primary_key=True)
    tournamentorganizerid = Column(Integer, ForeignKey('members.naf_number'))
    tournamentname = Column(String(255))
    tournamentaddress1 = Column(String(255))
    tournamentaddress2 = Column(String(255))
    tournamentcity = Column(String(255))
    tournamentstate = Column(String(255))
    tournamentzip = Column(String(255))
    tournamentnation = Column(String(255))
    tournamenturl = Column(String(255))
    tournamentnotesurl = Column(String(255))
    tournamentstartdate = Column(DateTime)
    tournamentenddate = Column(DateTime)
    tournamenttype = Column(String(50))
    tournamentstyle = Column(String(255))
    tournamentscoring = Column(Text)
    tournamentcost = Column(String(1023))
    tournamentnaffee = Column(String(255))
    tournamentnafdiscount = Column(String(255))
    tournamentinformation = Column(Text)
    tournamentcontact = Column(String(255))
    tournamentemail = Column(String(255))
    tournamentorg = Column(String(255))
    tournamentstatus = Column(String(50))
    tournamentmajor = Column(String(50))
    geolongitude = Column(String(50))
    geolattitude = Column(String(50))
    tournamentreport = Column(Text)
    subscription_closed = Column(String(1))
    rulesetid = Column(Integer)
    variantsid = Column(Integer, ForeignKey('variants.variantid'))
    variant_notes = Column(Text)
    variantstatus = Column(String(50))
    tournament_ruleset_file = Column(String(255))


class TournamentStatistic(Base):
    __tablename__ = 'tournament_statistics'
    typeid = Column(Integer, ForeignKey('award.id'), primary_key=True)
    tournamentid = Column(Integer, ForeignKey('tournaments.tournamentid'), primary_key=True)
    coachid = Column(Integer, ForeignKey('members.naf_number'), primary_key=True)
    raceid = Column(Integer, ForeignKey('races.raceid'))
    notes = Column(Text)
    date = Column(DateTime)


class TournamentCoach(Base):
    __tablename__ = 'tournament_coaches'
    tournamentid = Column(Integer, ForeignKey('tournaments.tournamentid'), primary_key=True)
    coachid = Column(Integer, ForeignKey('members.naf_number'), primary_key=True)
    raceid = Column(Integer, ForeignKey('races.raceid'), primary_key=True)


class Game(Base):
    __tablename__ = 'games'
    gameid = Column(Integer, primary_key=True)
    seasonid = Column(Integer)
    tournamentid = Column(Integer, ForeignKey('tournaments.tournamentid'))
    homecoachid = Column(Integer, ForeignKey('members.naf_number'))
    awaycoachid = Column(Integer, ForeignKey('members.naf_number'))
    racehome = Column(Integer, ForeignKey('races.raceid'))
    raceaway = Column(Integer, ForeignKey('races.raceid'))
    trhome = Column(Integer)
    traway = Column(Integer)
    rephome = Column(Integer)
    repaway = Column(Integer)
    rephome_calibrated = Column(Integer)
    repaway_calibrated = Column(Integer)
    dirty_calibrated = Column(Boolean)
    goalshome = Column(Integer)
    goalsaway = Column(Integer)
    badlyhurthome = Column(Integer)
    badlyhurtaway = Column(Integer)
    serioushome = Column(Integer)
    seriousaway = Column(Integer)
    killshome = Column(Integer)
    killsaway = Column(Integer)
    gate = Column(Integer)
    winningshome = Column(Integer)
    winningsaway = Column(Integer)
    notes = Column(Text)
    date = Column(DateTime)
    dirty = Column(Boolean)
    hour = Column(Integer)
    newdate = Column(DateTime)
    variantsid = Column(Integer, ForeignKey('variants.variantid'))


class CoachRankingVariant(Base):
    __tablename__ = 'coach_ranking_variant'
    coachid = Column(Integer, ForeignKey('members.naf_number'), primary_key=True)
    raceid = Column(Integer, ForeignKey('races.raceid'), primary_key=True)
    variantid = Column(Integer, ForeignKey('variants.variantid'), primary_key=True)
    dateupdate = Column(DateTime)
    ranking = Column(String(10))  # Adjusted to String to handle DECIMAL
    ranking_temp = Column(String(10))  # Adjusted to String to handle DECIMAL