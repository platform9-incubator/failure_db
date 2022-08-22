/* contains schema info */

CREATE DATABASE failure_db;
USE failure_db;
CREATE TABLE `branches` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255) COMMENT 'e.g. atherton, v5.5, etc'
);

CREATE TABLE `builds` (
  `id` int PRIMARY KEY COMMENT 'teamcity build id',
  `branch_id` int,
  `date` datetime
);

CREATE TABLE `failures` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `suite` varchar(255),
  `test_module` varchar(255),
  `test` varchar(255),
  `message` varchar(255),
  `md5sum` varchar(255)
);

CREATE TABLE `users` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `username` varchar(255) UNIQUE
);

CREATE TABLE `build_failures` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `build_id` int,
  `failure_id` int,
  `bug_id` varchar(255) COMMENT 'jira bug id',
  `analyzed_by` int
);

ALTER TABLE `builds` ADD FOREIGN KEY (`branch_id`) REFERENCES `branches` (`id`);

ALTER TABLE `build_failures` ADD FOREIGN KEY (`build_id`) REFERENCES `builds` (`id`);

ALTER TABLE `build_failures` ADD FOREIGN KEY (`failure_id`) REFERENCES `failures` (`id`);

ALTER TABLE `build_failures` ADD FOREIGN KEY (`analyzed_by`) REFERENCES `users` (`id`);
