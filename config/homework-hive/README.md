# In HDFS
hdfs dfs -put films.csv /user/hadoop/kao.leangseng/
hdfs dfs -put people.csv /user/hadoop/kao.leangseng/
hdfs dfs -put reviews.csv /user/hadoop/kao.leangseng/
hdfs dfs -put roles.csv /user/hadoop/kao.leangseng/

# In Hive - Hue UI
-- DROP TABLE films;
-- DROP TABLE people;
-- DROP TABLE reviews;
-- DROP TABLE roles;

CREATE DATABASE IF NOT EXISTS Movie;
USE Movie;

-- 1. Films Table
DROP TABLE IF EXISTS films;
CREATE EXTERNAL TABLE films (
    id INT,
    title STRING,
    release_year INT,
    country STRING,
    duration INT,
    language STRING,
    certification STRING,
    gross BIGINT,
    budget BIGINT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LOCATION 'hdfs://namenode:9000/user/hadoop/kao.leangseng/movie/films';
-- TBLPROPERTIES ("skip.header.line.count"="1");

-- 2. People Table
DROP TABLE IF EXISTS people;
CREATE EXTERNAL TABLE people (
    id INT,
    name STRING,
    birthdate STRING,
    deathdate STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LOCATION 'hdfs://namenode:9000/user/hadoop/kao.leangseng/movie/people';
-- TBLPROPERTIES ("skip.header.line.count"="1");

-- 3. Reviews Table
DROP TABLE IF EXISTS reviews;
CREATE EXTERNAL TABLE reviews (
    film_id INT,
    num_user INT,
    num_critic INT,
    imdb_score DOUBLE,
    num_votes INT,
    facebook_likes INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LOCATION 'hdfs://namenode:9000/user/hadoop/kao.leangseng/movie/reviews';
-- TBLPROPERTIES ("skip.header.line.count"="1");

-- 4. Roles Table
DROP TABLE IF EXISTS roles;
CREATE EXTERNAL TABLE roles (
    id INT,
    film_id INT,
    person_id INT,
    role STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LOCATION 'hdfs://namenode:9000/user/hadoop/kao.leangseng/movie/roles';
-- TBLPROPERTIES ("skip.header.line.count"="1");


LOAD DATA INPATH 'hdfs://namenode:9000/user/hadoop/kao.leangseng/films.csv' OVERWRITE INTO TABLE films;
LOAD DATA INPATH 'hdfs://namenode:9000/user/hadoop/kao.leangseng/people.csv' OVERWRITE INTO TABLE people;
LOAD DATA INPATH 'hdfs://namenode:9000/user/hadoop/kao.leangseng/reviews.csv' OVERWRITE INTO TABLE reviews;
LOAD DATA INPATH 'hdfs://namenode:9000/user/hadoop/kao.leangseng/roles.csv' OVERWRITE INTO TABLE roles;

SELECT * FROM films LIMIT 100;
SELECT * FROM people LIMIT 100;
SELECT * FROM reviews LIMIT 100;
SELECT * FROM roles LIMIT 100;