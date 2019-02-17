# TEAP - The Enterprisey Administration Project


## Overview

This project aims to centralise an interface for open-source based intranets - it aims to provide an administrator-friendly interface that would translate requirements into actions needed to be performed on:

- Nextcloud installation,
- LDAP server, and
- more to come.


## Motivation of the project

The project is aimed to assist large organizations in managing their intranets.
Such organizations typically make heavy use of groups - a group may indicate for example

* Geographical location (city, country, ...),
* division (Legal, HR, Engineering, ...),
* projects one is involved in,
* services one needs for work (git, accounting software, ...).

Membership in a group usually means that one should have access to a shared Nextcloud folder, Rocket.Chat room, calendar, and access rights.
This would mean adding a corresponding LDAP group memberships, and configuring those services either according to the LDAP setup, or according to their REST APIs.
This project aims to do exactly that - according to a predefined schema, enable addition of new users, modification and removals in an automated way, hiding the complexity of the REST API and LDAP schemas behind a sleek interface.


## Usage

### Command-line client

You can use the client to connect to a nextcloud instance and perform basic operations.
For example, the snippet below adds a new user `alice` to groups `accounting` and `users`:

```
cd src
python cli/client.py creds.ini add_user alice alices_password -g accounting -g users
```

The `creds.ini` file contains credential info, typically like this:

```ini
[credentials]

url = http://localhost
user = uname
password = pass
```

### Web application

Flask on back-end which serves single page vue.js front-end and provides api

#### Build setup

```
cd src/web/teap/frontend/
npm install

# serve vue.js application with reload on 8081 port
npm run dev

# build source with minification
npm run build

# install python requirements
pip install -r requirements.in

# run flask dev server on 5000 port 
cd /src/web/
python wsgi.py

```
