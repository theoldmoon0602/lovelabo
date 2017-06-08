create table users(
    id integer primary key,
    username text unique,
    password text,
    realname text unique,
    rank integer,
    first integer,
    second integer,
    third integer
);

create table labs(
    id integer primary key,
    name text unique
);
insert into labs(name) values('山口 智浩');
insert into labs(name) values('松尾 賢一');
insert into labs(name) values('松村 寿枝');
insert into labs(name) values('内田 眞司');
insert into labs(name) values('山口 賢一');
insert into labs(name) values('岡村 真吾');
insert into labs(name) values('本間 啓道');
insert into labs(name) values('上野 秀剛');
insert into labs(name) values('市川 嘉裕');