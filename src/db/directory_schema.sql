drop table if exists gateways;
create table gateways (
  gateway_id integer primary key autoincrement,
  address text not null,
  last_update datetime not null,
  unique(address)
);


