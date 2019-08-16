-- drop database shaoyou;
create database if not exists shaoyou;
create table if not exists players(
	id integer  auto_increment primary key  ,
	username char(20) not null unique ,
	secretid char(32) not null,
	points integer );

ALTER TABLE players ADD freepoints date;
