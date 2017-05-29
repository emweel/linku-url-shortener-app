drop table if exists links;
create table links (
    id integer primary key autoincrement,
    link text not null
);