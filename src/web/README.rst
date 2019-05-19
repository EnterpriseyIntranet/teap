===============================
TEAP web project
===============================

TEAP - The Enterprisey Administration Project


Quickstart
----------

Run the following commands from current directory to bootstrap your environment for web project::

    pip install -r requirements/dev.txt
    cp .env.example .env
    cd teap/frontend
    npm install
    npm run dev  # run the webpack dev server and flask server using concurrently


Once you have installed your DBMS, run the following to create your app's
database tables and perform the initial migration ::

    flask db init
    flask db migrate
    flask db upgrade


Deployment
----------

To deploy::

    export FLASK_ENV=production
    export FLASK_DEBUG=0
    export DATABASE_URL="<YOUR DATABASE URL>"
    cd teap/frontend && npm run build   # build assets with webpack
    flask run       # start the flask server

In your production environment, make sure the ``FLASK_DEBUG`` environment
variable is unset or is set to ``0``.


Shell
-----

To open the interactive shell, run ::

    flask shell

By default, you will have access to the flask ``app``.


Running Tests
-------------

To run all tests, run ::

    flask test


Migrations
----------

Whenever a database migration needs to be made. Run the following commands ::

    flask db migrate

This will generate a new migration script. Then run ::

    flask db upgrade

To apply the migration.

For a full migration command reference, run ``flask db --help``.


Pages
------

**Divisions**

| Divisions are static and list of divisions defined in `ldap.ini` config file under Divisions section.
| Each division has machine name and display name, in config file you write config machine name as a key, and display name as a value.
| For example, the Legal division can have display name Legal, and machine name LEG. In config file you write `LEG = Legal`.

| On divisions page you can see 3 lists: for Normal divisions (exists in ldap and in config), Config only divisions, ldap only divisions.
| You are able to create Config only divisions and delete ldap only divisions.
| When division is created, 2 more requests are sent to the server - rocket chat channel creation, group folder creation,
user will see notification if they were successful or some error happened.
