CREATE DATABASE IF NOT EXISTS psiz;
USE psiz;

CREATE TABLE IF NOT EXISTS assignment (
    assignment_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    project_id CHAR(255) NOT NULL,
    protocol_id CHAR(255) NOT NULL,
    worker_id CHAR(255) NOT NULL,
    amt_assignment_id CHAR(255) NOT NULL,
    amt_hit_id CHAR(255) NOT NULL,
    browser CHAR(255) NOT NULL,
    platform CHAR(255) NOT NULL,
    begin_hit TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_hit TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status_code SMALLINT DEFAULT 0,
    ver INT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS trial (
    trial_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    assignment_id INT NOT NULL,
    n_select INT UNSIGNED NOT NULL,
    is_ranked INT UNSIGNED NOT NULL,
    q_idx INT NOT NULL,
    r1_idx INT NOT NULL,
    r2_idx INT NOT NULL,
    r3_idx INT,
    r4_idx INT,
    r5_idx INT,
    r6_idx INT,
    r7_idx INT,
    r8_idx INT,
    c1_idx INT NOT NULL,
    c2_idx INT NOT NULL,
    c3_idx INT,
    c4_idx INT,
    c5_idx INT,
    c6_idx INT,
    c7_idx INT,
    c8_idx INT,
    start_ms TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    c1_rt_ms INT UNSIGNED,
    c2_rt_ms INT UNSIGNED,
    c3_rt_ms INT UNSIGNED,
    c4_rt_ms INT UNSIGNED,
    c5_rt_ms INT UNSIGNED,
    c6_rt_ms INT UNSIGNED,
    c7_rt_ms INT UNSIGNED,
    c8_rt_ms INT UNSIGNED,
    submit_rt_ms INT UNSIGNED NOT NULL,
    is_catch_trial TINYINT(1),
    rating TINYINT,
    FOREIGN KEY (assignment_id) REFERENCES assignment(assignment_id)
    ON DELETE CASCADE
);