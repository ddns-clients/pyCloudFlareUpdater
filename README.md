# GoDaddy 'A' Record Updater

*DDNS Service for updating dynamically your CloudFlare 'A' Records when your public IP changes*

[![PyPi](https://img.shields.io/badge/v1.0%20-PyPi-green.svg)](https://pypi.org/project/pyGoDaddyUpdater/)
[![ZIP](https://img.shields.io/badge/Package%20-Zip-green.svg)](https://gitlab.javinator9889.com/ddns-clients/pyCloudFlareUpdater/repository/master/archive.zip)
[![GIT](https://img.shields.io/badge/Package%20-Git-green.svg)](https://gitlab.javinator9889.com/ddns-clients/pyCloudFlareUpdater.git)
[![Downloads](https://pepy.tech/badge/pygodaddyupdater)](https://pepy.tech/project/pygodaddyupdater)

## Index

 1. [Purpose](#purpose)
 2. [Installation](#installation)
 3. [Usage](#usage)
 4. [License](#license)
 
------------

### Purpose

As a continuation of the [recently created pyGoDaddyUpdater](https://gitlab.javinator9889.com/ddns-clients/pyGoDaddyAUpdater),
here you have *CloudFlare Updater*. This group aims to create *DDNS* OpenSource clients that are available for every 
user/sysadmin with the most common DNS providers.

If you are a *CloudFlare* user (you have your own domain, CNAMES, etc.) maybe you have noticed that there is no **Dynamic 
DNS** (*DDNS*) update service, so you have to manually put your **public IP** at your domain 'A' Record whenever it 
changes.

Therefore, other possibilities exists such as *having a No-IP domain* and make all your CNAMEs point to that DNS, 
enabling redirection from the source domain (e.g.: example.com) to an *www* domain (e.g.: www.example.com).

With this script/service, you can configure a **daemon** which will be running in the background, periodically checking
for your public IP for seeing if it has changed. If you want also, you can configure it to run only once.

### Installation

**NOTICE: THIS SCRIPT IS ONLY RUNNING ON SYSTEMS WITH PYTHON 3 AND ABOVE**

There are two possibilities for installing this script:

#### 1. Using *setup.py*
   
   Start by *cloning* this repository. For that, you will need to have 
   [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed. Then, run on Git Bash:
   ```text
   git clone https://gitlab.javinator9889.com/ddns-clients/pyCloudFlareUpdater.git
   ```
   
   There is another possibility so you can *directly download* a compressed file with all the necessary data. Just unzip
   it and continue with the steps below.
   
   For installing, you will need **administrator** permissions, as the script is creating a new command so you can run
   it from everywhere:
   ```text
   cd pyCloudFlareUpdater
   sudo python3 setup.py install
   ```
   
#### 2. Using *pip* (easier and faster)
   
   I assume you have [**pip** installed](https://www.makeuseof.com/tag/install-pip-for-python/), so for using this package:
   ```text
   sudo pip install pyCloudFlareUpdater
   # If you have any error saying that at least Python 3 is needed
   # try with the following one:
   sudo pip3 install pyCloudFlareUpdater
   ```
   
### Usage

First of all, go to your *Cloudflare user account* options, and find the section (usually at the bottom of the page) 
that says **API Keys**. 

Obtain the *Global API Key* and save it on a safe location, we will use it later.

![API Keys](api_keys.png)

---------

Once you have installed the script, the execution is simple (from your command line):
```text
$ cloudflare_ddns [OPTIONS]
```

The available options are:

 + `--domain DOMAIN`: specifies **which domain** will be updated. That is, if your site is hosted at www.example.com, then your
 domain is *example.com*.
 
 + `--name NAME`: here the 'A' Record name must be included. In most cases, this name usually is `@` (the name pointing to 
 the host).
 
 + `--time TIME`: change the *update check interval* time (in minutes). By default, it is 5 minutes.
 
 + `--key KEY`: the *Cloudflare key* you obtained as explained before.
 
 + `--mail MAIL`: the *Cloudflare mail* you use to login into your account.
 
 + `--proxied`: use this option for making all the requests to your website **access first** Cloudflare servers (the 
 same as enabling this option ![Cloudflare proxy](cloud.png)).
 
 + `--no_daemonize`: include this option for running this script **only once**.
 
 + `--pid PID FILE`: define your own PID file, in which the running daemon PID will be saved. By default, it is: 
 `/var/run/cloudflare.pid`.
 
 + `--log LOG FILE`: define your own LOG file, in which the running daemon logs will be saved. By default, it is:
 `/var/log/cloudflare.log`.
 
 + `--preferences PREFERENCES FILE`: if you are planning to dynamically update **more than one** domain at the same 
 time, you can define a custom preferences file (if not, each time you run the daemon it will be overwritten).
 
 + `--user USERNAME`: if for any reason you need to run this script as another user (for example, because of the 
 permissions for saving logs and the PID file), include here your username (you must run the script as admin).
 
 + `--group GROUP NAME`: if for any reason you need to run this script as another group (for example, because of the 
 permissions for saving logs and the PID file), include here your username (you must run the script as admin).
 
The first time you execute this script (or for defining a new preferences file), you must include (only the first time):
 + Domain.
 + Name.
 + Key.
 + Mail.
 + Proxied.

Then, each time you execute the script with no *extra arguments* or *providing the preferences file* you will not need
to include the options mentioned above.

### License

```text
                             pyCloudFlareUpdater
                  Copyright (C) 2019 - Javinator9889

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
      the Free Software Foundation, either version 3 of the License, or
                   (at your option) any later version.

       This program is distributed in the hope that it will be useful,
       but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
               GNU General Public License for more details.

     You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
```
 