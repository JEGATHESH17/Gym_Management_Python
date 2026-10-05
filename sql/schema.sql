CREATE DATABASE IF NOT EXISTS gym_manager CHARACTER SET utf8mb4;
USE gym_manager;
CREATE TABLE IF NOT EXISTS members (
 id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100) NOT NULL,
 phone VARCHAR(30) NOT NULL UNIQUE
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS plans (
 id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100) NOT NULL UNIQUE,
 duration_days INT NOT NULL, price DECIMAL(10,2) NOT NULL,
 CHECK(duration_days > 0), CHECK(price > 0)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS memberships (
 id INT PRIMARY KEY AUTO_INCREMENT, member_id INT NOT NULL, plan_id INT NOT NULL,
 start_date DATE NOT NULL, end_date DATE NOT NULL, agreed_price DECIMAL(10,2) NOT NULL,
 FOREIGN KEY(member_id) REFERENCES members(id), FOREIGN KEY(plan_id) REFERENCES plans(id),
 INDEX(end_date), CHECK(end_date >= start_date)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS payments (
 id INT PRIMARY KEY AUTO_INCREMENT, membership_id INT NOT NULL,
 amount DECIMAL(10,2) NOT NULL, reference VARCHAR(100) NOT NULL UNIQUE,
 recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(membership_id) REFERENCES memberships(id), CHECK(amount > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS attendance (
 id INT PRIMARY KEY AUTO_INCREMENT,
 member_id INT NOT NULL,
 attended_on DATE NOT NULL,
 FOREIGN KEY(member_id) REFERENCES members(id),
 UNIQUE KEY one_visit_per_day(member_id,attended_on),
 INDEX(attended_on)
) ENGINE=InnoDB;
