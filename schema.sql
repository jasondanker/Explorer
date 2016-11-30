drop table if exists users;
create table users (
	user_id integer primary key,
	first_name text not null,
	last_name text not null,
	email text not null unique,
	insecure_password text not null,
	active boolean not null
);

drop table if exists trips;
create table trips (
	trip_id integer primary key,
	trip_name text not null,
	origin text not null,
	budget integer not null,
	date_outbound date not null,
	date_inbound date not null,
	flight_outbound integer,
	flight_inbound integer,
	hotel integer,
	destination text,
	budget_remaining integer not null, -- Calculated
	active boolean not null
);

drop table if exists flights;
create table flights (
	flight_id integer primary key,
	airline text not null,
	flight_number text not null,
	flight_date date not null,
	origin text not null,
	destination text not null,
	cost integer not null,
	trip_id integer,
	active boolean not null,
	foreign key (trip_id) references trips(trip_id)
);

drop table if exists hotels;
create table hotels (
	hotel_id integer primary key,
	name text not null,
	check_in date not null,
	check_out date not null,
	location text not null, -- Likely to be expanded
	rating integer,
	cost integer not null,
	trip_id integer,
	active boolean not null,
	foreign key (trip_id) references trips(trip_id)
);

drop table if exists user_trips_junct;
create table user_trips_junct (
	relation_id integer primary key,
	user_id integer,
	trip_id integer,
	active boolean not null,
	foreign key (user_id) references users(user_id),
	foreign key (trip_id) references trips(trip_id)
);