#!/usr/bin/env python3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from flask import Flask, request, redirect, session, render_template, url_for, flash
import os
from os import urandom
from subprocess import Popen, PIPE, CalledProcessError, TimeoutExpired
import re
from datetime import datetime
import socket

application = Flask(__name__)

### Configuration ###
logDir = "log"
resultDirJSON = "result/json"
resultDirHTML = "result/html"
checkCmd = "testssl.sh/testssl.sh"
checkArgs = ["--quiet", "--color", "3", "--logfile=" + logDir, "--jsonfile=" + resultDirJSON, "--fast"]
checkTimeout = 300
rendererCmd = "aha"
rendererArgs = ["--stylesheet", "--word-wrap", "--no-header", "--black"]
rendererTimeout = 30
protocols = ["ftp", "smtp", "lmtp", "pop3", "imap", "xmpp", "xmpp-server", "ldap", "nntp", "postgres", "mysql"]
reHost = re.compile(r"^[a-zA-Z0-9_][a-zA-Z0-9_\-]+(\.[a-zA-Z0-9_\-]+)*$")
preflightRequest = True
preflightTimeout = 10
application.debug = False
application.secret_key = urandom(32)


#####################

def escape_ansi(line):
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', line)


@application.route("/", methods=['GET', 'POST'])
def main():
    if request.method == 'GET':  # Main Page
        return render_template("main.html")
    elif request.method == 'POST':  # Perform Test
        # Sanity checks of request values
        ok = True
        host = request.form['host']
        if not reHost.match(host):
            flash("Invalid host name ::: '" + str(host) + "'")
            ok = False
        if host == "localhost" or host.find("127.") == 0:
            flash("I was already pentested ;)")
            ok = False

        try:
            port = int(request.form['port'])
            if not (1 <= port <= 65535):
                flash("Invalid port number!")
                ok = False
        except:
            flash("Port number must be numeric")
            ok = False

        if 'starttls' in request.form and request.form['starttls'] == "yes":
            starttls = True
            protocol = request.form['protocol']
            if starttls and protocol not in protocols:
                flash("Invalid protocol ::: '" + str(protocol) + "' ")
                ok = False
        else:
            starttls = False

        # if not ('confirm' in request.form and request.form['confirm'] == "yes"):
        #    flash("You must confirm that you are authorized to scan the given system!")
        #    ok = False

        if not os.path.isdir(resultDirJSON):
            flash("JSON log directory not present")
            ok = False

        if not os.path.isdir(resultDirHTML):
            flash("HTML log directory not present")
            ok = False

        # Perform preflight request to prevent that testssl.sh runs into long timeout
        if ok and preflightRequest:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(preflightTimeout)
                s.connect((host, port))
                s.close()
            except:
                flash("Connection test failed of host:port ::: '" + str(host) + ":" + str(port) + "'")
                ok = False

        if not ok:
            return redirect(url_for('main'))

        # Build command line
        args = [checkCmd]
        args += checkArgs
        if starttls:
            args.append("-t")
            args.append(protocol)
        args.append(host + ":" + str(port))

        # Perform test
        output = b""
        try:
            check = Popen(args, stdout=PIPE, stderr=PIPE)
            output, err = check.communicate(timeout=checkTimeout)
            if check.returncode > 10:
                output = err
                flash("SSL Scan failed with error code " + str(check.returncode) + " - " + escape_ansi(str(err, 'utf-8')))
        except TimeoutExpired:
            flash("SSL Scan timed out after " + str(checkTimeout) + " seconds of host name '" + str(host) + "'")
            check.terminate()

        html = "<pre>" + str(output, 'utf-8') + "</pre>"
        try:
            rArgs = [rendererCmd]
            rArgs += rendererArgs
            renderer = Popen(rArgs, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            html, err = renderer.communicate(input=output, timeout=rendererTimeout)
            if renderer.returncode != 0:
                html = str(err, 'utf-8')
                flash("HTML formatting failed with error code " + str(renderer.returncode) + " - see raw output below")
        except TimeoutExpired as e:
            flash("HTML formatting failed - see raw output below")
            renderer.terminate()

        ts = datetime.now()
        try:
            resultfile = open(
                resultDirHTML + "/" + ts.strftime("%Y%m%d-%H%M%S.%f") + "-" + host + "_" + str(port) + ".html",
                mode='w')
            resultfile.write(str(html, 'utf-8'))
            resultfile.close()
        except:
            pass
        return render_template("result.html", result=str(html, 'utf-8'))


if __name__ == "__main__":
    application.run()
