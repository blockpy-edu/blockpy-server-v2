# Blockpy Server V2

Flask-based server for managing the BlockPy LTI app. Its main responsibilities are:
* Managing the database of courses, users, assignments, submissions, and associated artifacts
* Providing the editor, particularly when launched from an LTI context
* Providing an interface for instructors to select assignments
* Grade passback to the LTI Tool Consumer (e.g., Canvas).
* Some basic course management features (CRUD operations for assignments, courses, etc.)

Ideally, students will never realize that BlockPy is a whole website standing apart from their LMS -
it will seem like an integrated part. Teachers should be able to forget that BlockPy is separate
as well, after they have added BlockPy as a new LTI App. Administrators and researchers using
BlockPy may find some of the other interfaces helpful.

# Requirements

This guide will go into more details about all of the following, but here's a quick list of some of the things you're going to end up needing to host your instance of BlockPy.

* A canvas installation (we have also had an integration with Moodle, although we do not try and support that since Moodle is a more limited LMS).
* The ability to add new LTI apps to your Canvas installation.
* A *nix server that can run BlockPy's server.
* An SSL certificate for the server.

Computationally, the server should not be a very demanding application. Most of its work is to manage the database. We did have some issues with scaling before we added some more indexes to the database, but ever since those improvements we have been able to handle hundreds of concurrent users. Since BlockPy's execution happens client-side, the difficulties are only:

1. Managing all the student submissions, which usually won't be very big "files". Once we figured out our indexes, we didn't have any issues even when we reached hundreds of thousands of submissions.
2. Managing all the logged data, which can be very big. We reached several gigs after a few years of use (several hundreds of students per semester). If you're concerned, please raise an Issue to have us add a feature to turn off logging optionally - it's not necessary to most use, but supports our research.
3. Communicating to Canvas through LTI. Grade passback happens when students submit, and this can take a second based on our timing logs. However, we have not had any recent issues with this even when hundreds of students were submitting.

# Installation

Let's look at the steps involved in setting up BlockPy.

## Server Setup

We recommend hosting BlockPy through [Nginx](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-18-04-quickstart) on a Linux server. We have used both Ubuntu and CentOS without major issues. We used to use Apache, but that gave us a lot of trouble.

The server will need to support SSL, so you should obtain an appropriate certificate. Some universities' or CS departments' tech staff can help you get a certificate. Otherwise, you could also use a site like Let's Encrypt (although we haven't tried that).

Make sure your server's firewall is configured to allow traffic for both HTTP and HTTPS. You may also need to configure ports for mail, SSH, and external database access - however, none of these are really required for managing the server. We usually use IPTables, so it's just a matter of adding the relevant rules. We recommend finding an appropriate guide.

## Get BlockPy Server

Choose an appropriate directory on your server to store the BlockPy server application. We used `/var/www/blockpy-server` and `/home/www/blockpy-server/` but there are many options.

**Sidebar: Permissions** -  We had some difficulty getting our permissions squared away when setting up our server initially. Ignoring typos, the most common problem was forgetting that permissions needed to go up the entire folder hierarchy. It wasn't enough to make `blockpy-server/` readable, we had to make its parent directories readable too.

You can download the server from our public GitHub repo:

```
> git clone https://github.com/blockpy-edu/blockpy-server.git .
```

Using Git will allow you to pull in the inevitable bug fixes we'll be publishing. Right now, all of our latest madness is in the Summer2019 branch, but we hope to merge to master in a few days. For now, checkout out lunacy:

```bash
> git checkout summer2019
```

## VirtualEnv

BlockPy's server is a Python 3.5 Flask application, and it will eventually be run using a system called UWSGI. However, you won't want to use your systems' Python version. Instead, you should use a Virtual Environment via VirtualEnv. There are many tutorials for setting up a Virtual Env, such as [this SO post](https://stackoverflow.com/questions/29934032/virtualenv-python-3-ubuntu-14-04-64-bit?answertab=active#tab-top). We put our `env/` folder directly in the `/var/www/blockpy-server/` folder.

Make sure you install the server's required libraries:

```
> env/bin/pip install -r requirements.txt
```

We also need UWSGI to daemonize the server:

```
> env/bin/pip install uwsgi
```

## Filesystem Directories

BlockPy's server has a few folders that it puts things in. Most of them can be created via the makefile:

```
make create_directories
```

You will need to set permissions appropriately so that the web user (`nginx` or `www` or `www-data` depending on your system) will be able to access them and in some cases write and execute them. If you are truly desperate, you can always just `chmod 777` but we advise choosing permissions less liberally.

Here's a quick rundown of the folders:

* `static/uploads/` - This is where we used to put user uploaded files - this may get used again in the future if the Postgres filesystem approach doesn't pan out.
* `static/uploads/submission_blocks/` - Images of students' block get uploaded here.
* `static/gen/` - The asset manager for Flask bundles JS and CSS, placing it here.
* `static/.webassets-cache/` - This is also involved in the asset bundling.
* `logs/` - This is where we store student code files (every edit creates a new file). We also store several server logs.
* `database/` - This is where we store the SQLITE database for the local development version.
* `certs/` - This is where I store any local https certificates for local dev.
* `backups/` - If you run the backup commands, data will be dumped here by default.

## Configuration

You're going to need to specify some settings for your server's installation.

You will need to create the file+folder `settings/secrets.json` with the following structure (some fields explained below):

```json
{
    "FLASK_SECRET_KEY": "MAKE UP A SECRET KEY",
    "EMAIL": {
        "USERNAME": "GIVE THE USERNAME FOR YOUR EMAIL HOST",
        "SENDER": "GIVE THE SENDER NAME FOR YOUR EMAIL HOST",
        "PASSWORD": "GIVE THE PASSWORD FOR YOUR EMAIL HOST",
        "SERVER": "GIVE THE SERVER NAME FOR YOUR EMAIL HOST (e.g., think.cs.vt.edu)",
        "PORT": 465,
        "USE_SSL": true
    },

    "CONSUMER_KEY_CERT": "/PATH TO .KEY FILE",
    "CONSUMER_KEY_PEM_FILE": "/PATH TO .PEM FILE",
    "CONSUMER_KEY": "MAKE UP A CONSUMER KEY",
    "CONSUMER_KEY_SECRET": "MAKE UP A CONSUMER SECRET",

    "SECURITY_PASSWORD_SALT": "MAKE UP A GOOD SALT FOR YOUR PASSWORDS",
    "BLOCKPY_SOURCE_DIR": "Only needed for local dev",
    "DATASETS_SOURCE_DIR": "Only needed for local dev",

    "PRODUCTION": true,

    "SYS_ADMINS": ["ADD IN EMAIL ADDRESSES OF ANY SERVER ADMINS"],
    "SITE_ADMIN": "GIVE A NAME TO YOUR SITE ADMIN ('BlockPy @ VT').",
    "DATABASE": {
        "USER": "USERNAME FOR THE DATABASE, IF NOT SQLITE",
        "PASS": "PASSWORD FOR THE DATABASE, IF NOT SQLITE",
        "ACCESS_URL": "postgresql://{username}:{password}@localhost/DB_NAME"
    },

    "CORGIS_URL": "https://corgis-edu.github.io/corgis/datasets/",

    "ADMIN": {
        "first_name": "YOUR FIRST NAME",
        "last_name": "YOUR LAST NAME",
        "password": "YOUR PASSWORD",
        "email": "YOUR EMAIL ADDRESS"
    }
}
```

The `DATABASE.ACCESS_URL` will be interpolated with the `DATABASE.USER` and `DATABASE.PASS`. However, you will still need to replace the `DB_NAME` (we use `blockpydb`).

Technically speaking, you could run your own version of CORGIS by changing the `CORGIS_URL`. However, you will probably just want to use the general CORGIS github instance. No further work is required on your end.

Your `CONSUMER_KEY` uniquely identifies you to Canvas, `CONSUMER_SECRET` is to be shared with instructors using your BlockPy instance. The goal is to keep it relatively secretive. You can choose anything you want for your Key and Secret.

## Database setup

You're going to need to create a new Postgres database and prepopulate some schemas. Our database is named `blockpydb`. You might want to adjust your authentication for Postgres too - we modified our `pg_hba.conf` file to require `md5` instead of `ident`, for instance. Your exact database requirements may vary depending on whether you want to have other tools on the server.

In addition to the database, you'll need to create a user (that you specified in the `settings/secrets.json` file) with appropriate privileges. Basically, we ran the following commands through `psql`:

```postgresql
> CREATE DATABASE thinkdb;
> CREATE USER thinker WITH PASSWORD 'XXXX';
> ALTER ROLE thinker SET client_encoding TO 'utf8';
> ALTER ROLE thinker SET default_transaction_isolation TO 'read committed';
> ALTER ROLE thinker SET timezone TO 'UTC';
> GRANT ALL PRIVILEGES ON DATABASE thinkdb TO thinker;
> GRANT ALL ON ALL TABLES IN SCHEMA public TO thinker;
> \q
```

 Assuming things have gone well so far, you should be able to run the following command line script to create the relevant tables:

```
> env/bin/python manage.py create_db
```

You'll want to run any migrations to keep the schema in sync with our own:

```
> env/bin/python manage.py db upgrade
```

And the most basic default data can be added with:

```
> env/bin/python manage.py populate_db
```

You might want to add the maze course too, though we're hoping to make it its own separate curriculum.

```
> env/bin/python manage.py add_maze_course_db
```

In theory, you could now upload one of our curricula's programming problems (e.g., PythonSneks or CT@VT). More information on that coming soon! For now, you can create some rudimentary database items if you want:

```
> env/bin/python manage.py add_test_users_db
```

## Nginx Setup

You'll need to create two sites files for Nginx. We start with a setup like this:

```bash
> cd /etc/nginx/
> mkdir sites-available
> mkdir sites-enabled
```

Then edit the `nginx.conf` file to remove the default server blocks and add:

```
include /etc/nginx/sites-enabled/*.conf;
server_names_hash_bucket_size 64;
```

Then create a new file `sites-enabled/https_redirect.conf` to redirect HTTP traffic to HTTPS:

```
server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;
        return 301 https://$host$request_uri;

}
```

And now you can set up the actual Nginx BlockPy Server site. Many of your settings will vary, but here's most of what we used for our local institution's `sites-enabled/blockpy.conf` file:

```
server {
    listen       443 ssl http2 default_server;
    listen       [::]:443 ssl http2 default_server;
    server_name  XXXX.YYY.ZZZ.edu;

    ssl_certificate /full/path/to/your/pem/file;
    ssl_certificate_key /full/path/to/your/key/file;
    ssl_dhparam /full/path/to/your/dhparam.pem/file;

    location /favicon.ico {
        alias /var/www/blockpy-server/static/images/favicon.ico;
    }

    location /nginx_status {
        stub_status on;
        access_log off;
    }

    # We wanted our toplevel URL to be a separate site. You might want
    # to host here directly, instead. But the point is that BlockPy Server
    # can be configured to run alongside other applications!
    location / {
        root /var/www/html;
        index index.html;
    }

    location /blockpy {
        include            uwsgi_params;
        uwsgi_pass         unix:/run/uwsgi/blockpy.sock;
    }

    ########################################################################
    # from https://cipherli.st/                                            #
    # and https://raymii.org/s/tutorials/Strong_SSL_Security_On_nginx.html #
    ########################################################################
    ssl_session_cache shared:SSL:20m;
    ssl_session_timeout 180m;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_prefer_server_ciphers on;
    ssl_ecdh_curve secp384r1;
    ssl_ciphers ECDH+AESGCM:ECDH+AES256:ECDH+AES128:DHE+AES128:!ADH:!AECDH:!MD5;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    add_header Strict-Transport-Security "max-age=63072000; includeSubdomains";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    ##################################
    # END https://cipherli.st/ BLOCK #
    ##################################
}
```

I don't have good notes on this, but this was part of what I did apparently. I'm not sure if it's redundant to your external SSL certificate, but it might be used to set up outbound SSL communication?

```
> openssl dhparam 2048 -out /etc/nginx/cert/dhparam.pem
```

We also had a lot of headaches with permissions for `/run/uwsgi/blockpy.sock` particularly on server reloads. Keep an eye on it and choose appropriate permissions for the users you choose.

You can test your Nginx sites with:

```bash
> nginx -t
```

And reload them when they're ready:

```bash
> nginx -s reload
```

## INI File Setup

You should edit your `blockpy.ini` file in the BlockPy Server directory, if you have a different directory than `/var/www/blockpy-server/`

## UWSGI Setup

You'll need to register your UWSGI script with your server's `systemd` or equivalent. Here's our `/etc/systemd/system/uwsgi.service` file:

```ini
[Unit]
Description=uWSGI instance to serve blockpy-server

[Service]
ExecStartPre=-/usr/bin/bash -c 'mkdir -p /run/uwsgi; chown nginx /run/uwsgi'
ExecStart=/usr/bin/bash -c 'cd /var/www/blockpy-server; source env/bin/activate; uwsgi --ini blockpy.ini'
Restart=always
KillSignal=SIGQUIT
Type=notify
NotifyAccess=all

[Install]
WantedBy=multi-user.target
```

Alternatively, we set up Emperor for our institution, so there's an additional file and a slightly different `ExecStart`. That's only necessary if you are running multiple apps on the server.

Don't forget to start/restart UWSGI (you'll do this when pulling new versions of the github repo too):

```bash
> sudo systemctl restart uwsgi
```

# Using BlockPy

At this point, in theory, your instance is now publicly accessible from the browser. If not, google and our Issue tracker are your friends :)

Let's talk about how to actually use this thing.

## Adding Instructors

Students are automatically registered in Canvas, but instructors should register separately. In theory, this can all be done with BlockPy's Register and Login buttons. However, I broke the email server and haven't been able to test them recently. Please raise an Issue if you have trouble!

Once you're in the system and confirmed, you can create courses. Roles are taken from Canvas. Note that this means a student with appropriate Canvas permissions could create their own course and become an instructor. Keep an eye on ownership of assignments and roles within courses.

## Configuring Canvas

You connect to your BlockPy instance from Canvas via the LTI protocol. This requires you to register your BlockPy instance in your course. The recommended approach is to use the XML configuration file generated for your instance automatically. You can get your XML file and other settings by visiting the Courses page. For us, the URL is: `https://think.cs.vt.edu/blockpy/courses/add_canvas`

With your settings and XML file, you can follow [this guide](https://community.canvaslms.com/docs/DOC-12863-415274552) to add BlockPy to your Canvas installation. There are also some brief instructions on the BlockPy Add Canvas page that you can link instructors to.

## Curriculum Setup

TODO: We need instructions for how to upload all our assignments. And possibly some better toolings. I'll have this finished in the next day or two when I need to upload my own course :)

## Adding assignments

The Courses page has a link to another page with instructions for building new assignments and selecting resources. For us, the url is: `https://think.cs.vt.edu/blockpy/courses/making_problems/`

Unfortunately, this guide is slightly out of date. We'll update it soon once we finish the revised assignment editing interface.

If you're using our curriculum, you might never use these menus. But please do know that BlockPy has a very rich system for building assignments. In particular, we use [Pedal](https://github.com/pedal-edu/pedal/) to provide feedback.

## Trying Assignments

When you open an assignment as an instructor, you are editing its settings. You can try out the problem, but grades aren't passed anywhere. You probably want to use the Student View to more accurately model what students will experience. You should verify that you can successfully submit a grade with this, to check that you have your LTI permissions enabled correctly.

Using the BlockPy Editor is outside the scope of this document. If you have issues with the Editor, please feel free to report them in our Issue tracker, either for the [server](https://github.com/blockpy-edu/blockpy-server/issues) or for the [client](https://github.com/blockpy-edu/blockpy/issues/).

## Dashboard

This feature isn't ready, but will eventually provide an interface for instructors and students to view submissions (and eventually to provide comments and feedback).

# Getting Help

Filing a GitHub Issue is the best way for us to help track and resolve trouble you're having. Please understand that we are a small team (mostly just Dr. Bart) with other responsibilities. We will try to fix show-stopper issues as quickly as possible.