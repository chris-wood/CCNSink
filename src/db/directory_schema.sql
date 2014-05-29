drop table if exists gateways;
create table gateways (
  gateway_id integer primary key autoincrement,
  address text not null,
  last_update datetime not null,
  unique(address)
);

-- drop table if exists follower;
-- create table follower (
--   who_id integer,
--   whom_id integer
-- );

-- drop table if exists message;
-- create table message (
--   message_id integer primary key autoincrement,
--   author_id integer not null,
--   text text not null,
--   pub_date integer
-- );

