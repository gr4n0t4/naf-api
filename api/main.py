from fastapi import FastAPI
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, Body
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Member, Tournament, TournamentCoach, Game, Race, Variant, Award, TournamentStatistic, CoachRankingVariant
from datetime import datetime



root_path = os.getenv("ROOT_PATH", "api")
# FastAPI app and metadata tabs
tags_metadata = [
    {
        "name": "Members",
        "description": "Members are the players who are registered with the NAF.",
    },
    {
        "name": "Tournaments",
        "description": "Tournaments are events that are organized by NAF members.",
    },
    {
        "name": "Games",
        "description": "Games are the matches played between two teams in a tournament.",
    },
    {
        "name": "Awards",
        "description": "Awards are the recognitions given to players or teams for their performance in tournaments.",
    },
    {
        "name": "Rankings",
        "description": "Rankings are the standings of players based on their performance in tournaments.",
    },    
    {
        "name": "Common Data",
        "description": "Common data includes variants, races, and other shared information.",
    },    
]
app = FastAPI(title="NAF API", root_path=f"/{root_path}", openapi_tags=tags_metadata, summary="NAF API to use data from the daily dumps of the NAF database", description="Feel free to your own service and customize it to your needs. You can find the [source code](https://github.com/gr4n0t4/naf-api) in my github repository", version="0.0.1")

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST', 'localhost')}:5432/{os.getenv('POSTGRES_DB')}"
# Create SQLAlchemy engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    # connect_args={
    #     "server_settings": {
    #         "statement_timeout": "10000",
    #     }
    # },
)


# Dependency to get database session
async def get_async_db():

    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        finally:
            await session.close()



@app.get("/members",
         responses={200: {"content": {"application/json": {},}}},
         tags=["Members"],)
async def get_members(
    request: Request,  
    naf_name: str = Query(None),
    naf_number: int = Query(None),
    country: str = Query(None),
    expire_date_gte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$" ),
    expire_date_lte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    registration_date_gte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    registration_date_lte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        query = select(Member)
        if naf_name:
            query = query.where(Member.naf_name.ilike(f"%{naf_name}%"))
        if naf_number:
            query = query.where(Member.naf_number == naf_number)
        if country:
            query = query.where(Member.country.ilike(f"%{country}%"))
        if expire_date_gte:
            expire_date_gte = datetime.strptime(expire_date_gte, "%Y-%m-%d").date()
            query = query.where(Member.expire_date >= expire_date_gte)
        if expire_date_lte:
            expire_date_lte = datetime.strptime(expire_date_lte, "%Y-%m-%d").date()
            query = query.where(Member.expire_date <= expire_date_lte)
        if registration_date_gte:
            registration_date_gte = datetime.strptime(registration_date_gte, "%Y-%m-%d").date()
            query = query.where(Member.registration_date >= registration_date_gte)
        if registration_date_lte:
            registration_date_lte = datetime.strptime(registration_date_lte, "%Y-%m-%d").date()
            query = query.where(Member.registration_date <= registration_date_lte)
        
        result = await db.execute(query)
        members = result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")        
    return members

@app.get("/members/{naf_number}",
            responses={200: {"content": {"application/json": {},}}},
            tags=["Members"],)
async def get_member_by_id(
    naf_number: int = Path(..., description="The ID of the member to retrieve"),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        query = select(Member).where(Member.naf_number == naf_number)
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    return member

@app.get("/member/{naf_number}/tournaments",
            responses={200: {"content": {"application/json": {},}}},
            tags=["Members"],)
async def get_member_tournaments(
    naf_number: int = Path(..., description="The NAF number of the member"),
    tournament_nation: str = Query(None, description="Filter tournaments by nation"),
    race_name: str = Query(None, description="Filter tournaments by race name"),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        query = (
            select(Tournament)
            .join(TournamentCoach, Tournament.tournamentid == TournamentCoach.tournamentid)
            .where(TournamentCoach.coachid == naf_number)
        )
        if tournament_nation:
            query = query.where(Tournament.tournamentnation.ilike(f"%{tournament_nation}%"))
        if race_name:
            query = query.join(Race, TournamentCoach.raceid == Race.raceid).where(Race.name.ilike(f"%{race_name}%"))
        
        result = await db.execute(query)
        tournaments = result.scalars().all()
        if not tournaments:
            raise HTTPException(status_code=404, detail="No tournaments found for this member")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    return tournaments
@app.get("/member/{naf_number}/games",
            responses={200: {"content": {"application/json": {},}}},
            tags=["Members"],)
async def get_member_games(
    naf_number: int = Path(..., description="The NAF number of the member"),
    tournamentid: int = Query(None, description="Filter games by tournament ID"),
    date_gte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$", description="Filter games by start date (greater than or equal to)"),
    date_lte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$", description="Filter games by end date (less than or equal to)"),
    variant_name: str = Query(None, description="Filter games by variant name"),
    variant_id: int = Query(None, description="Filter games by variant ID"),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        query = select(Game).where(
            (Game.homecoachid == naf_number) | (Game.awaycoachid == naf_number)
        )
        if tournamentid:
            query = query.where(Game.tournamentid == tournamentid)
        if date_gte:
            date_gte = datetime.strptime(date_gte, "%Y-%m-%d")
            query = query.where(Game.date >= date_gte)
        if date_lte:
            date_lte = datetime.strptime(date_lte, "%Y-%m-%d")
            query = query.where(Game.date <= date_lte)
        if variant_name:
            query = query.join(Variant, Game.variantsid == Variant.variantid).where(Variant.variantname.ilike(f"%{variant_name}%"))
        if variant_id:
            query = query.where(Game.variantsid == variant_id)
        result = await db.execute(query)
        games = result.scalars().all()
        if not games:
            raise HTTPException(status_code=404, detail="No games found for this member")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    return games


@app.get("/tournaments",
            responses={200: {"content": {"application/json": {},}}},
            tags=["Tournaments"],)
async def get_tournaments(
    request: Request,
    tournamentid: int = Query(None),
    tournamentorganizerid: int = Query(None),
    tournamentname: str = Query(None),
    tournamentcity: str = Query(None),
    tournamentstate: str = Query(None),
    tournamentnation: str = Query(None),
    tournamentstartdate_gte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    tournamentstartdate_lte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    tournamentenddate_gte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    tournamentenddate_lte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    tournamenttype: str = Query(None),
    tournamentstyle: str = Query(None),
    tournamentstatus: str = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        query = select(Tournament)
        if tournamentid:
            query = query.where(Tournament.tournamentid == tournamentid)
        if tournamentorganizerid:
            query = query.where(Tournament.tournamentorganizerid == tournamentorganizerid)
        if tournamentname:
            query = query.where(Tournament.tournamentname.ilike(f"%{tournamentname}%"))
        if tournamentcity:
            query = query.where(Tournament.tournamentcity.ilike(f"%{tournamentcity}%"))
        if tournamentstate:
            query = query.where(Tournament.tournamentstate.ilike(f"%{tournamentstate}%"))
        if tournamentnation:
            query = query.where(Tournament.tournamentnation.ilike(f"%{tournamentnation}%"))
        if tournamentstartdate_gte:
            tournamentstartdate_gte = datetime.strptime(tournamentstartdate_gte, "%Y-%m-%d")
            query = query.where(Tournament.tournamentstartdate >= tournamentstartdate_gte)
        if tournamentstartdate_lte:
            tournamentstartdate_lte = datetime.strptime(tournamentstartdate_lte, "%Y-%m-%d")
            query = query.where(Tournament.tournamentstartdate <= tournamentstartdate_lte)
        if tournamentenddate_gte:
            tournamentenddate_gte = datetime.strptime(tournamentenddate_gte, "%Y-%m-%d")
            query = query.where(Tournament.tournamentenddate >= tournamentenddate_gte)
        if tournamentenddate_lte:
            tournamentenddate_lte = datetime.strptime(tournamentenddate_lte, "%Y-%m-%d")
            query = query.where(Tournament.tournamentenddate <= tournamentenddate_lte)
        if tournamenttype:
            query = query.where(Tournament.tournamenttype.ilike(f"%{tournamenttype}%"))
        if tournamentstyle:
            query = query.where(Tournament.tournamentstyle.ilike(f"%{tournamentstyle}%"))
        if tournamentstatus:
            query = query.where(Tournament.tournamentstatus.ilike(f"%{tournamentstatus}%"))
        
        result = await db.execute(query)
        tournaments = result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    return tournaments

@app.get("/games",
            responses={200: {"content": {"application/json": {},}}},
            tags=["Games"],)
async def get_games(
    request: Request,
    gameid: int = Query(None),
    seasonid: int = Query(None),
    tournamentid: int = Query(None),
    homecoachid: int = Query(None),
    awaycoachid: int = Query(None),
    racehome: int = Query(None),
    raceaway: int = Query(None),
    race_name: str = Query(None, description="Filter by race name (either home or away)"),
    coach_name: str = Query(None, description="Filter by coach name (either home or away)"),
    race_id: int = Query(None, description="Filter by home race ID (either home or away)"),
    coach_id: int = Query(None, description="Filter by home coach ID (either home or away)"),
    trhome: int = Query(None),
    traway: int = Query(None),
    rephome: int = Query(None),
    repaway: int = Query(None),
    rephome_calibrated: int = Query(None),
    repaway_calibrated: int = Query(None),
    dirty_calibrated: bool = Query(None),
    goalshome: int = Query(None),
    goalsaway: int = Query(None),
    badlyhurthome: int = Query(None),
    badlyhurtaway: int = Query(None),
    serioushome: int = Query(None),
    seriousaway: int = Query(None),
    killshome: int = Query(None),
    killsaway: int = Query(None),
    gate: int = Query(None),
    winningshome: int = Query(None),
    winningsaway: int = Query(None),
    date_gte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    date_lte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    dirty: bool = Query(None),
    hour: int = Query(None),
    newdate_gte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    newdate_lte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    variantsid: int = Query(None),
    variant_name: str = Query(None, description="Filter by variant name"),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        query = select(Game)
        if gameid:
            query = query.where(Game.gameid == gameid)
        if seasonid:
            query = query.where(Game.seasonid == seasonid)
        if tournamentid:
            query = query.where(Game.tournamentid == tournamentid)
        if homecoachid:
            query = query.where(Game.homecoachid == homecoachid)
        if awaycoachid:
            query = query.where(Game.awaycoachid == awaycoachid)
        if racehome:
            query = query.where(Game.racehome == racehome)
        if raceaway:
            query = query.where(Game.raceaway == raceaway)
        if race_name:
            query = query.join(Race, (Game.racehome == Race.raceid) | (Game.raceaway == Race.raceid)).where(Race.name.ilike(f"%{race_name}%"))
        if coach_name:
            query = query.join(Member, (Game.homecoachid == Member.naf_number) | (Game.awaycoachid == Member.naf_number)).where(Member.naf_name.ilike(f"%{coach_name}%"))
        if race_id:
            query = query.where((Game.racehome == race_id) | (Game.raceaway == race_id))
        if coach_id:
            query = query.where((Game.homecoachid == coach_id) | (Game.awaycoachid == coach_id))
        if trhome:
            query = query.where(Game.trhome == trhome)
        if traway:
            query = query.where(Game.traway == traway)
        if rephome:
            query = query.where(Game.rephome == rephome)
        if repaway:
            query = query.where(Game.repaway == repaway)
        if rephome_calibrated:
            query = query.where(Game.rephome_calibrated == rephome_calibrated)
        if repaway_calibrated:
            query = query.where(Game.repaway_calibrated == repaway_calibrated)
        if dirty_calibrated is not None:
            query = query.where(Game.dirty_calibrated == dirty_calibrated)
        if goalshome:
            query = query.where(Game.goalshome == goalshome)
        if goalsaway:
            query = query.where(Game.goalsaway == goalsaway)
        if badlyhurthome:
            query = query.where(Game.badlyhurthome == badlyhurthome)
        if badlyhurtaway:
            query = query.where(Game.badlyhurtaway == badlyhurtaway)
        if serioushome:
            query = query.where(Game.serioushome == serioushome)
        if seriousaway:
            query = query.where(Game.seriousaway == seriousaway)
        if killshome:
            query = query.where(Game.killshome == killshome)
        if killsaway:
            query = query.where(Game.killsaway == killsaway)
        if gate:
            query = query.where(Game.gate == gate)
        if winningshome:
            query = query.where(Game.winningshome == winningshome)
        if winningsaway:
            query = query.where(Game.winningsaway == winningsaway)
        if date_gte:
            date_gte = datetime.strptime(date_gte, "%Y-%m-%d")
            query = query.where(Game.date >= date_gte)
        if date_lte:
            date_lte = datetime.strptime(date_lte, "%Y-%m-%d")
            query = query.where(Game.date <= date_lte)
        if dirty is not None:
            query = query.where(Game.dirty == dirty)
        if hour:
            query = query.where(Game.hour == hour)
        if newdate_gte:
            newdate_gte = datetime.strptime(newdate_gte, "%Y-%m-%d")
            query = query.where(Game.newdate >= newdate_gte)
        if newdate_lte:
            newdate_lte = datetime.strptime(newdate_lte, "%Y-%m-%d")
            query = query.where(Game.newdate <= newdate_lte)
        if variantsid:
            query = query.where(Game.variantsid == variantsid)
        if variant_name:
            query = query.join(Variant, Game.variantsid == Variant.variantid).where(Variant.variantname.ilike(f"%{variant_name}%"))
        
        result = await db.execute(query)
        games = result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    return games

@app.get("/awards",
            responses={200: {"content": {"application/json": {},}}},
            tags=["Awards"],)
async def get_awards(
    request: Request,
    typeid: int = Query(None, description="Filter by award type ID"),
    tournamentid: int = Query(None, description="Filter by tournament ID"),
    coachid: int = Query(None, description="Filter by coach ID"),
    coach_name: str = Query(None, description="Filter by coach name"),
    raceid: int = Query(None, description="Filter by race ID"),
    notes: str = Query(None, description="Filter by notes content"),
    award_name: str = Query(None, description="Filter by award name"),
    date_gte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$", description="Filter by start date (greater than or equal to)"),
    date_lte: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$", description="Filter by end date (less than or equal to)"),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        query = select(TournamentStatistic).join(Member, TournamentStatistic.coachid == Member.naf_number)
        if typeid:
            query = query.where(TournamentStatistic.typeid == typeid)
        if tournamentid:
            query = query.where(TournamentStatistic.tournamentid == tournamentid)
        if coachid:
            query = query.where(TournamentStatistic.coachid == coachid)
        if coach_name:
            query = query.where(Member.naf_name.ilike(f"%{coach_name}%"))
        if raceid:
            query = query.where(TournamentStatistic.raceid == raceid)
        if notes:
            query = query.where(TournamentStatistic.notes.ilike(f"%{notes}%"))
        if award_name:            
            query = query.join(Award, (TournamentStatistic.typeid == Award.id)).where(Award.name.ilike(f"%{award_name}%"))
        if date_gte:
            date_gte = datetime.strptime(date_gte, "%Y-%m-%d")
            query = query.where(TournamentStatistic.date >= date_gte)
        if date_lte:
            date_lte = datetime.strptime(date_lte, "%Y-%m-%d")
            query = query.where(TournamentStatistic.date <= date_lte)
        
        result = await db.execute(query)
        awards = result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    return awards

@app.get("/rankings",
            responses={200: {"content": {"application/json": {},}}},
            tags=["Rankings"],)
async def get_rankings(
    request: Request,
    coachid: int = Query(None, description="Filter by coach ID"),
    raceid: int = Query(None, description="Filter by race ID"),
    variantid: int = Query(None, description="Filter by variant ID"),
    race_name: str = Query(None, description="Filter by race name"),
    coach_name: str = Query(None, description="Filter by coach name"),
    variant_name: str = Query(None, description="Filter by variant name"),
    country: str = Query(None, description="Filter by coach country"),
    ranking_gte: int = Query(None, description="Filter by ranking (greater than or equal to)"),
    ranking_lte: int = Query(None, description="Filter by ranking (less than or equal to)"),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        query = select(CoachRankingVariant).join(Member, CoachRankingVariant.coachid == Member.naf_number).join(Race, CoachRankingVariant.raceid == Race.raceid).join(Variant, CoachRankingVariant.variantid == Variant.variantid)
        if coachid:
            query = query.where(CoachRankingVariant.coachid == coachid)
        if raceid:
            query = query.where(CoachRankingVariant.raceid == raceid)
        if variantid:
            query = query.where(CoachRankingVariant.variantid == variantid)
        if race_name:
            query = query.where(Race.name.ilike(f"%{race_name}%"))
        if coach_name:
            query = query.where(Member.naf_name.ilike(f"%{coach_name}%"))
        if variant_name:
            query = query.where(Variant.variantname.ilike(f"%{variant_name}%"))
        if country:
            query = query.where(Member.country.ilike(f"%{country}%"))
        if ranking_gte is not None:
            query = query.where(CoachRankingVariant.ranking >= ranking_gte)
        if ranking_lte is not None:
            query = query.where(CoachRankingVariant.ranking <= ranking_lte)
        
        result = await db.execute(query)
        rankings = result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    return rankings

@app.get("/common/races",
        responses={200: {"content": {"application/json": {},}}},
        tags=["Common Data"],)
async def get_races(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        query = select(Race)
        result = await db.execute(query)
        races = result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    return races

@app.get("/common/variants",
        responses={200: {"content": {"application/json": {},}}},
        tags=["Common Data"],)
async def get_variants(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        query = select(Variant)
        result = await db.execute(query)
        variants = result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    return variants


@app.get("/common/awards",
        responses={200: {"content": {"application/json": {},}}},
        tags=["Common Data"],)
async def get_awards(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        query = select(Award)
        result = await db.execute(query)
        awards = result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    return awards
