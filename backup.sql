BEGIN TRANSACTION;
CREATE TABLE attendance (
	id INTEGER NOT NULL, 
	member_id INTEGER NOT NULL, 
	gym_id INTEGER NOT NULL, 
	check_date VARCHAR(15) NOT NULL, 
	status VARCHAR(20), 
	marked_by VARCHAR(60), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(member_id) REFERENCES members (id) ON DELETE CASCADE, 
	FOREIGN KEY(gym_id) REFERENCES gyms (id) ON DELETE CASCADE
);
INSERT INTO "attendance" VALUES(1,1,2,'2026-05-09','Present','Shahzad','2026-05-09 13:48:24.750873');
INSERT INTO "attendance" VALUES(2,2,2,'2026-05-09','Absent','Shahzad','2026-05-09 14:15:18.050397');
CREATE TABLE audit_entries (
	id INTEGER NOT NULL, 
	gym_id INTEGER NOT NULL, 
	entry_type VARCHAR(20) NOT NULL, 
	reference_id INTEGER, 
	expected_amount FLOAT, 
	actual_amount FLOAT, 
	description TEXT, 
	entry_date VARCHAR(15) NOT NULL, 
	verified_by VARCHAR(60), 
	status VARCHAR(20), 
	notes TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(gym_id) REFERENCES gyms (id) ON DELETE CASCADE
);
INSERT INTO "audit_entries" VALUES(1,2,'headcount_total',2,0.0,0.0,'Total headcount on 2026-05-09','2026-05-09','Waqas','Verified','','2026-05-09 11:18:54.316565');
INSERT INTO "audit_entries" VALUES(2,2,'headcount_active',2,0.0,0.0,'Active headcount on 2026-05-09','2026-05-09','Waqas','Verified','','2026-05-09 11:18:54.361903');
INSERT INTO "audit_entries" VALUES(3,1,'headcount_total',1,0.0,1.0,'Total headcount on 2026-05-09','2026-05-09','Waqas','Discrepancy','','2026-05-09 11:19:23.531415');
INSERT INTO "audit_entries" VALUES(4,1,'headcount_active',1,0.0,0.0,'Active headcount on 2026-05-09','2026-05-09','Waqas','Verified','','2026-05-09 11:19:23.579281');
INSERT INTO "audit_entries" VALUES(5,1,'headcount_total',1,0.0,3.0,'Total headcount on 2026-05-09','2026-05-09','Waqas','Discrepancy','','2026-05-09 11:19:40.428118');
INSERT INTO "audit_entries" VALUES(6,1,'headcount_active',1,0.0,5.0,'Active headcount on 2026-05-09','2026-05-09','Waqas','Discrepancy','','2026-05-09 11:19:40.476615');
INSERT INTO "audit_entries" VALUES(7,2,'fee',1,0.01,200000.0,'All member total','2026-05-09','Waqas','Discrepancy','','2026-05-09 11:35:40.706414');
INSERT INTO "audit_entries" VALUES(8,2,'headcount_total',2,1.0,25.0,'Total headcount on 2026-05-09','2026-05-09','Waqas','Discrepancy','','2026-05-09 11:36:31.276239');
INSERT INTO "audit_entries" VALUES(9,2,'headcount_active',2,1.0,20.0,'Active headcount on 2026-05-09','2026-05-09','Waqas','Discrepancy','','2026-05-09 11:36:31.322973');
INSERT INTO "audit_entries" VALUES(10,2,'expense',1,50000.0,0.0,'','2026-05-09','admin','Discrepancy','','2026-05-09 11:44:03.889665');
INSERT INTO "audit_entries" VALUES(11,2,'fee',1,0.01,0.0,'','2026-05-09','admin','Discrepancy','','2026-05-09 11:44:15.688429');
CREATE TABLE body_measurements (
	id INTEGER NOT NULL, 
	member_id INTEGER NOT NULL, 
	recorded_date VARCHAR(15) NOT NULL, 
	weight_kg FLOAT, 
	chest_cm FLOAT, 
	waist_cm FLOAT, 
	hips_cm FLOAT, 
	bicep_cm FLOAT, 
	body_fat_pct FLOAT, 
	notes TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(member_id) REFERENCES members (id) ON DELETE CASCADE
);
CREATE TABLE complaints (
	id INTEGER NOT NULL, 
	gym_id INTEGER NOT NULL, 
	member_id INTEGER, 
	subject VARCHAR(200) NOT NULL, 
	description TEXT, 
	status VARCHAR(20), 
	priority VARCHAR(20), 
	submitted_by VARCHAR(60), 
	resolved_by VARCHAR(60), 
	wa_sent BOOLEAN, 
	created_at DATETIME, 
	resolved_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(gym_id) REFERENCES gyms (id) ON DELETE CASCADE, 
	FOREIGN KEY(member_id) REFERENCES members (id) ON DELETE SET NULL
);
CREATE TABLE daily_expenses (
	id INTEGER NOT NULL, 
	gym_id INTEGER NOT NULL, 
	amount FLOAT NOT NULL, 
	category VARCHAR(60) NOT NULL, 
	description TEXT, 
	expense_date VARCHAR(15) NOT NULL, 
	staff_name VARCHAR(60), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(gym_id) REFERENCES gyms (id) ON DELETE CASCADE
);
CREATE TABLE fee_records (
	id INTEGER NOT NULL, 
	member_id INTEGER NOT NULL, 
	gym_id INTEGER NOT NULL, 
	amount FLOAT NOT NULL, 
	payment_method VARCHAR(40), 
	payment_date VARCHAR(15) NOT NULL, 
	period_start VARCHAR(15), 
	period_end VARCHAR(15), 
	receipt_number VARCHAR(30), 
	collected_by VARCHAR(60), 
	notes TEXT, 
	created_at DATETIME, whatsapp_sent BOOLEAN NOT NULL DEFAULT 0, 
	PRIMARY KEY (id), 
	FOREIGN KEY(member_id) REFERENCES members (id) ON DELETE CASCADE, 
	FOREIGN KEY(gym_id) REFERENCES gyms (id) ON DELETE CASCADE
);
INSERT INTO "fee_records" VALUES(1,1,2,1000.0,'Cash','2026-05-05','2026-05-09','2026-06-05','RCP-E6256049','Shahzad','','2026-05-09 13:45:27.078994',1);
INSERT INTO "fee_records" VALUES(2,2,2,1300.0,'Cash','2026-05-05','2026-05-05','2026-06-05','RCP-072A4DAD','Shahzad','','2026-05-09 13:51:45.261810',0);
INSERT INTO "fee_records" VALUES(3,4,2,1500.0,'Cash','2026-05-09','2026-05-09','2026-06-08','RCP-17A5189F','Shahzad','','2026-05-09 15:44:47.824570',0);
CREATE TABLE gyms (
	id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	address VARCHAR(255), 
	phone VARCHAR(30), 
	email VARCHAR(120), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
INSERT INTO "gyms" VALUES(1,'Life Fittness Gym Sattlite town','Killi shabo chowq life fittness gym near to chaman housing scheem','+923337871342','inamkhan744@gmail.com','2026-05-09 09:47:01.716992');
INSERT INTO "gyms" VALUES(2,'Life Fittness gym killi shaboo','Killi shabo chowq life fittness gym near to chaman housing scheem','+923337871342','inamkhan744@gmail.com','2026-05-09 09:47:12.713873');
INSERT INTO "gyms" VALUES(3,'Life Fittness gym Killi shaboo ladies','Killi shaboo','+923337871342','inamkhan744@gmail.com','2026-05-09 11:13:34.336954');
INSERT INTO "gyms" VALUES(4,'Life Fittness Gym Sattlite Town ladies','Sattlite town','+923337871342','inamkhan744@gmail.com','2026-05-09 11:14:02.127267');
CREATE TABLE members (
	id INTEGER NOT NULL, 
	gym_id INTEGER NOT NULL, 
	serial_number VARCHAR(20) NOT NULL, 
	full_name VARCHAR(120) NOT NULL, 
	phone VARCHAR(30), 
	email VARCHAR(120), 
	gender VARCHAR(20), 
	dob VARCHAR(15), 
	photo_path VARCHAR(255), 
	membership_type VARCHAR(40) NOT NULL, 
	fee_amount FLOAT, 
	join_date VARCHAR(15) NOT NULL, 
	expiry_date VARCHAR(15), 
	status VARCHAR(20), 
	notes TEXT, 
	created_at DATETIME, whatsapp_sent BOOLEAN NOT NULL DEFAULT 0, 
	PRIMARY KEY (id), 
	FOREIGN KEY(gym_id) REFERENCES gyms (id) ON DELETE CASCADE, 
	UNIQUE (serial_number)
);
INSERT INTO "members" VALUES(1,2,'KS-00001','Ghazi','03132154293','','Male','','/home/runner/workspace/gym-app/uploads/e20ae80d65434d0487770e3bbf446ac8.jpg','Monthly',1000.0,'2026-05-05','2026-06-05','Active','Bodybuilding','2026-05-09 13:43:39.282414',1);
INSERT INTO "members" VALUES(2,2,'KS-00002','Ghulam farooq','03444112233','','Male','','/home/runner/workspace/gym-app/uploads/64f0b5e3ac5b4839b87d1b5abb953db8.jpg','Monthly',1300.0,'2026-05-05','2026-06-05','Active','Bodybuilding','2026-05-09 13:50:51.616275',0);
INSERT INTO "members" VALUES(3,2,'KS-00003','Abbas','03478746322','','Male','','/home/runner/workspace/gym-app/uploads/027b960ef9db47f3b5da3881c147acc5.jpg','Monthly',0.0,'2026-05-09','2026-06-08','Active','Bodybilding','2026-05-09 15:28:09.627478',0);
INSERT INTO "members" VALUES(4,2,'KS-00004','Aqib nazeer','03','','Male','','/home/runner/workspace/gym-app/uploads/f40690144a844c559513855441fc351f.jpg','Monthly',1500.0,'2026-05-04','2026-06-04','Active','Bodybuilding','2026-05-09 15:36:57.642761',0);
CREATE TABLE stock_items (
	id INTEGER NOT NULL, 
	gym_id INTEGER NOT NULL, 
	item_name VARCHAR(120) NOT NULL, 
	category VARCHAR(60), 
	purchase_price FLOAT, 
	sale_price FLOAT, 
	quantity INTEGER, 
	min_quantity INTEGER, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(gym_id) REFERENCES gyms (id) ON DELETE CASCADE
);
CREATE TABLE stock_sales (
	id INTEGER NOT NULL, 
	stock_item_id INTEGER NOT NULL, 
	gym_id INTEGER NOT NULL, 
	member_id INTEGER, 
	quantity_sold INTEGER, 
	sale_price FLOAT, 
	total_amount FLOAT, 
	sold_by VARCHAR(60), 
	sale_date VARCHAR(15) NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(stock_item_id) REFERENCES stock_items (id) ON DELETE CASCADE, 
	FOREIGN KEY(gym_id) REFERENCES gyms (id) ON DELETE CASCADE, 
	FOREIGN KEY(member_id) REFERENCES members (id) ON DELETE SET NULL
);
CREATE TABLE users (
	id INTEGER NOT NULL, 
	username VARCHAR(60) NOT NULL, 
	full_name VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(128) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	gym_id INTEGER, 
	is_active BOOLEAN, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (username), 
	FOREIGN KEY(gym_id) REFERENCES gyms (id) ON DELETE SET NULL
);
INSERT INTO "users" VALUES(1,'admin','Administrator','240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9','admin',NULL,1,'2026-05-09 09:42:41.906652');
INSERT INTO "users" VALUES(4,'Zakir','Zakir khan','2153119d5c19f2e6ccc1874bf235e5d3d273d07fa80bca13aefef037278d206d','staff',1,1,'2026-05-09 09:48:50.029333');
INSERT INTO "users" VALUES(7,'Arifa','Arifa','2153119d5c19f2e6ccc1874bf235e5d3d273d07fa80bca13aefef037278d206d','staff',3,1,'2026-05-09 11:15:42.737323');
INSERT INTO "users" VALUES(8,'Jiya','Jiya khan','2153119d5c19f2e6ccc1874bf235e5d3d273d07fa80bca13aefef037278d206d','staff',4,1,'2026-05-09 11:16:08.336987');
INSERT INTO "users" VALUES(9,'Waqas','Waqas khan','2153119d5c19f2e6ccc1874bf235e5d3d273d07fa80bca13aefef037278d206d','auditor',NULL,1,'2026-05-09 11:17:16.134581');
INSERT INTO "users" VALUES(11,'Shahzad','Shahzad','2153119d5c19f2e6ccc1874bf235e5d3d273d07fa80bca13aefef037278d206d','staff',2,1,'2026-05-09 11:29:24.968690');
INSERT INTO "users" VALUES(13,'Inam','Inam khan','2153119d5c19f2e6ccc1874bf235e5d3d273d07fa80bca13aefef037278d206d','admin',NULL,1,'2026-05-09 13:23:23.265673');
INSERT INTO "users" VALUES(14,'auditor','Auditor','5b92db4dfb561dc69c949f34d36f5db0f8b30811be3a2949d85c5001279e9b1a','auditor',NULL,0,'2026-05-10 07:43:13.656448');
INSERT INTO "users" VALUES(15,'staff','Staff Member','10176e7b7b24d317acfcf8d2064cfd2f24e154f7b5a96603077d5ef813d6a6b6','staff',NULL,0,'2026-05-10 07:44:15.133273');
COMMIT;
