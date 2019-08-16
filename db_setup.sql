-- drop database shaoyou;
create database if not exists shaoyou;
drop table players;
create table if not exists players(
	id integer  auto_increment primary key  ,
	username char(20) not null unique ,
	secretid char(32) not null,
	points integer ,
	freepoints integer
	);

-- ALTER TABLE players ADD freepoints integer;
