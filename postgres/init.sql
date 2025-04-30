-- CoachExport.csv
CREATE TABLE IF NOT EXISTS members (
    naf_number INT PRIMARY KEY,
    naf_name VARCHAR(255) NOT NULL,
    country VARCHAR(255),
    registration_date DATE NOT NULL,
    expiry_date DATE
);

-- naf_variants.csv
CREATE TABLE IF NOT EXISTS variants (
    variantid INT PRIMARY KEY,
    variantname VARCHAR(255) NOT NULL,
    variantorder INT
);

-- naf_race.csv
CREATE TABLE IF NOT EXISTS races (
    raceid INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    reroll_cost INT,
    apoth CHAR(1),
    race_order INT,
    selectable VARCHAR(255),
    race_count VARCHAR(3)
);

-- naf_tournament_statistics_list.csv
CREATE TABLE IF NOT EXISTS awards (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    label VARCHAR(255) NOT NULL,
    award_order INT
);

-- naf_tournament.csv
CREATE TABLE IF NOT EXISTS tournaments (
    tournamentid INT PRIMARY KEY,
    tournamentorganizerid INT REFERENCES members(naf_number),
    tournamentname VARCHAR(255),
    tournamentaddress1 VARCHAR(255),
    tournamentaddress2 VARCHAR(255),
    tournamentcity VARCHAR(255),
    tournamentstate VARCHAR(255),
    tournamentzip VARCHAR(255),
    tournamentnation VARCHAR(255),
    tournamenturl VARCHAR(255),
    tournamentnotesurl VARCHAR(255),
    tournamentstartdate DATE,
    tournamentenddate DATE,
    tournamenttype VARCHAR(50),
    tournamentstyle VARCHAR(255),
    tournamentscoring VARCHAR(4096),
    tournamentcost VARCHAR(1023),
    tournamentnaffee VARCHAR(255),
    tournamentnafdiscount VARCHAR(255),
    tournamentinformation TEXT,
    tournamentcontact VARCHAR(255),
    tournamentemail VARCHAR(255),
    tournamentorg VARCHAR(255),
    tournamentstatus VARCHAR(50),
    tournamentmajor VARCHAR(50),
    geolongitude VARCHAR(50),
    geolattitude VARCHAR(50),
    tournamentreport TEXT,
    subscription_closed VARCHAR(1),
    rulesetid INT,
    variantsid INT REFERENCES variants(variantid),
    variant_notes TEXT,
    variantstatus VARCHAR(50),
    tournament_ruleset_file VARCHAR(255)
);

-- naf_tournament_statistics_group.csv
CREATE TABLE IF NOT EXISTS tournament_statistics (
    typeid INT REFERENCES variants(variantid),
    tournamentid INT REFERENCES tournaments(tournamentid),
    coachid INT REFERENCES members(naf_number),
    raceid INT REFERENCES races(raceid),
    notes TEXT,
    date TIMESTAMP,
    PRIMARY KEY (typeid, tournamentid, coachid)
);

-- naf_tournamentcoach.csv
CREATE TABLE IF NOT EXISTS tournament_coaches (
    tournamentid INT REFERENCES tournaments(tournamentid),
    coachid INT REFERENCES members(naf_number),
    raceid INT REFERENCES races(raceid),
    PRIMARY KEY (tournamentid, coachid, raceid)
);

-- naf_game.csv
CREATE TABLE IF NOT EXISTS games (
    gameid INT PRIMARY KEY,
    seasonid INT,
    tournamentid INT REFERENCES tournaments(tournamentid),
    homecoachid INT REFERENCES members(naf_number),
    awaycoachid INT REFERENCES members(naf_number),
    racehome INT REFERENCES races(raceid),
    raceaway INT REFERENCES races(raceid),
    trhome INT,
    traway INT,
    rephome INT,
    repaway INT,
    rephome_calibrated INT,
    repaway_calibrated INT,
    dirty_calibrated BOOLEAN,
    goalshome INT,
    goalsaway INT,
    badlyhurthome INT,
    badlyhurtaway INT,
    serioushome INT,
    seriousaway INT,
    killshome INT,
    killsaway INT,
    gate INT,
    winningshome INT,
    winningsaway INT,
    notes TEXT,
    date DATE,
    dirty BOOLEAN,
    hour INT,
    newdate TIMESTAMP,
    variantsid INT REFERENCES variants(variantid)
);

-- naf_coachranking_variant.csv
CREATE TABLE IF NOT EXISTS coach_ranking_variant (
    coachid INT REFERENCES members(naf_number),
    raceid INT REFERENCES races(raceid),
    variantid INT REFERENCES variants(variantid),
    dateupdate TIMESTAMP,
    ranking DECIMAL(10, 2),
    ranking_temp DECIMAL(10, 4),
    PRIMARY KEY (coachid, raceid, variantid)
);
