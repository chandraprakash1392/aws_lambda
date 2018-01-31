# aws_lambda
This is a lambda function to shutdown and start instances integrated with Route53 to allow updation of any modification of Public IP through code
Things to take care in the project:
Please make sure you have two tables in your database namely: instance_details and instance_to_dns_map
database description of instance_details:
mysql> desc instance_details;
+------------------+------------------+------+-----+---------+----------------+
| Field            | Type             | Null | Key | Default | Extra          |
+------------------+------------------+------+-----+---------+----------------+
| id               | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
| instance_id      | varchar(45)      | NO   | UNI | NULL    |                |
| instance_state   | varchar(40)      | NO   |     | NULL    |                |
| stopped_manually | varchar(3)       | NO   |     | NULL    |                |
+------------------+------------------+------+-----+---------+----------------+

database description of instance_to_dns_map:
mysql> desc instance_to_dns_map;
+---------------+-------------+------+-----+----------+-------+
| Field         | Type        | Null | Key | Default  | Extra |
+---------------+-------------+------+-----+----------+-------+
| id            | int(11)     | NO   | PRI | NULL     |       |
| instance_id   | varchar(45) | NO   |     | NOT NULL |       |
| domain_name   | varchar(45) | YES  | UNI | NOT NULL |       |
| public_ip     | varchar(45) | YES  |     | NOT NULL |       |
| instance_name | char(100)   | YES  |     | NULL     |       |
+---------------+-------------+------+-----+----------+-------+

Once you have setup the databases and granted permissions to the users over these DB, everything should work fine.
Enjoy!!!
