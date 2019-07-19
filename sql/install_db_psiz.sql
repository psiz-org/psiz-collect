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
    begin_hit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_hit TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status_code SMALLINT DEFAULT 0
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
    start_ms TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    r1_rt_ms INT UNSIGNED,
    r2_rt_ms INT UNSIGNED,
    r3_rt_ms INT UNSIGNED,
    r4_rt_ms INT UNSIGNED,
    r5_rt_ms INT UNSIGNED,
    r6_rt_ms INT UNSIGNED,
    r7_rt_ms INT UNSIGNED,
    r8_rt_ms INT UNSIGNED,
    is_catch_trial TINYINT(1),
    is_catch_trial_correct TINYINT(1),
    rating TINYINT,
    FOREIGN KEY (assignment_id) REFERENCES assignment(assignment_id)
    ON DELETE CASCADE
);