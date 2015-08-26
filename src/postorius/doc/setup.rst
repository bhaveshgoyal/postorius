============
Installation
============

.. note::
    This installation guide covers Postorius, the web user interface for
    GNU Mailman 3. To install GNU Mailman follow the instructions in the `documentation`_.

    If you are looking for an easy way to set up the whole GNU Mailman 3
    suite (GNU Mailman 3, Postorius, Hyperkitty and mailman.client), check
    out the `mailman-bundler`_ project on GitLab.

.. _mailman-bundler: https://gitlab.com/mailman/mailman-bundler
.. _documentation: http://mailman.readthedocs.org

Install Postorius
=================


Latest release
--------------

If you just want to install the latest release of Postorius, install it from
PyPi:

::

    $ sudo pip install postorius

or:

::

    $ sudo easy_install postorius


Latest dev version
------------------

If you want to always be up to date with the latest development version, you
should install Postorius using git:

::

    $ git clone https://gitlab.com/mailman/postorius.git
    $ cd postorius
    $ sudo python setup.py develop


Setup your django project
=========================

Since you have now installed the necessary packages to run Postorius, it's
time to setup your Django site.

First, get the project directory from gitlab:

::

    $ git clone https://gitlab.com/mailman/postorius_standalone.git

Change the database setting in ``postorius_standalone/settings.py`` to
your preferred database, if you want something other than SQlite.

.. note::
    Detailed information on how to use different database engines can be found
    in the `Django documentation`_.

.. _Django documentation: https://docs.djangoproject.com/en/1.8/ref/settings/#databases

Third, prepare the database:

::

    $ cd postorius_standalone
    $ python manage.py syncdb
    $ cd ..

This will create the ``.db file`` (if you ar using SQLite) and will setup all the
necessary db tables. You will also be prompted to create a superuser which
will act as an admin account for Postorius.


Running the development server
==============================

The quickest way to run Postorius is to just start the development server:

::

    $ cd postorius_standalone
    $ python manage.py runserver


.. warning::
    You should use the development server only locally. While it's possible to
    make your site publicly available using the dev server, you should never
    do that in a production environment.


Running Postorius on Apache with mod_wsgi
=========================================

.. note::
    This guide assumes that you know how to setup a VirtualHost with Apache.
    If you are using SQLite, the ``.db`` file as well as its folder need to be
    writable by the web server.

These settings need to be added to your Apache VirtualHost:

:: 

    Alias /static /path/to/postorius_standalone/static
    <Directory "/path/to/postorius_standalone/static">
        Order deny,allow
        Allow from all
    </Directory>    

    WSGIScriptAlias / /path/to/postorius_standalone/srv/postorius.wsgi
    <Directory "/path/to/postorius_standalone/srv">
        Order deny,allow
        Allow from all
    </Directory>    

The first Alias serves the static files (CSS, JS, Images, etc.). The
WSGIScriptAlias serves the Django application. The paths need to be changed
depending on which location you downloaded ``postorius_standalone`` to. 

We're almost ready. But you need to collect the static files from Postorius
(which resides somewhere on your pythonpath) to be able to serve them from the
site directory. All you have to do is to change into the
``postorius_standalone`` directory and run:

::

    $ python manage.py collectstatic

After reloading the webserver Postorius should be running! 
