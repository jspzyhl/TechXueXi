CREATE DATABASE if not EXISTS learn CHARACTER SET utf8mb4;
use learn;
create table if not exists user_info(uid varchar(20) not null,nickname varchar(20),cookies varchar(4096),article_index int,video_index int,primary key (uid));
create table if not exists user_cfg(id int not null auto_increment,last_uid varchar(20),primary key(id));
create table if not exists wechat_bind(uid varchar(20) not null,openid varchar(32),primary key(uid));
create table if not exists wechat_privilege(openid varchar(32) not null,admin int, primary key(openid));
create table if not exists wechat_token(id int not null auto_increment,token varchar(200),expire_time double,primary key(id));
replace into user_info values(0,"default",null,null,null);
insert ignore into user_cfg values(1,"0");
