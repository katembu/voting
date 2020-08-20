# Tutorial
--------------------------------------------------------------
Requirements Voting system
Ubuntu
Mysql
Internet Connection


- Install Steps::
1. By default Ubuntu comes with Python installed.
2. Install mysql server by typing the command "sudo apt-get install mysql-server". Follow the steps until to the last one.
Default user is root. Make sure you note down the password because its needed to connect to mysql database
3. Install python pip by typing command "sudo apt-get install python-pip" This is needed to install requirements.
4. Switch to where you've downloaded this folder. If its in Desktop you can switch by typing command "cd ~/Desktop/votingsystem"
This should be done on terminal.
5. Once that is complete install requirements by typing command "sudo pip install -r requirements.txt"
6. If step 5 is complete you will need to create database, import the database and configure database connection.


CREATE DATABASE
==============
Login into mysql-server by typing the command "mysql -u root -p "After the prompt enter mysql password.
Create a database by typing command "create database votingsystem;"
Press CTRL + Q to Quit
Import tables and initial data by using command:
mysql -u root -p votingsystem < ~/Desktop/votingsystem/database/votingsystem.sql


- Run it::
Type command "fabmanager run" on terminal to run the system. Make sure you're on the folder where the system is installed. Follow step 4.
Go to browser type http://localhost:8080/
Default user: admin password: admin

That's it!!
