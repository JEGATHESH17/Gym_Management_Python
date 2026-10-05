USE gym_manager;

CREATE TABLE IF NOT EXISTS attendance (
 id INT PRIMARY KEY AUTO_INCREMENT,
 member_id INT NOT NULL,
 attended_on DATE NOT NULL,
 FOREIGN KEY(member_id) REFERENCES members(id),
 UNIQUE KEY one_visit_per_day(member_id,attended_on),
 INDEX(attended_on)
) ENGINE=InnoDB;
