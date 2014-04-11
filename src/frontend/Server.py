'''

'''

import string
import cgi
import time
import argparse
import pyccn
from ftplib import *
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class GatewayHTTPServerHandler(BaseHTTPRequestHandler):
    ''' TODO
    '''
    def buildInterest(self, path):

        # Strip out the components and build the interest
        components = self.path.split("/")

        excl = pyccn.ExclusionFilter()
        excl.add_any()
        excl.add_name(pyccn.Name([self.latest_version]))
        # expected result should be between those two names
        excl.add_name(pyccn.Name([self.last_version_marker]))
        excl.add_any()

        interest = pyccn.Interest(name=self.base_name, exclude=excl, \
            minSuffixComponents=3, maxSuffixComponents=3)
        interest.childSelector = 1 if latest else 0

    ''' Handle HTTP GET requests by converting the target URL to an equivalent interest.
    '''
    def do_GET(self):
        try:
            if self.path.endswith(".html"):
                f = open(curdir + sep + self.path) #self.path has /test.html
                #note that this potentially makes every file on your computer readable by the internet

                self.send_response(200)
                self.send_header('Content-type',	'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            if self.path.endswith(".esp"):   #our dynamic content
                self.send_response(200)
                self.send_header('Content-type',	'text/html')
                self.end_headers()
                self.wfile.write("hey, today is the" + str(time.localtime()[7]))
                self.wfile.write(" day in the year " + str(time.localtime()[0]))
                return
            return
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)

    def do_POST(self):
        global rootnode
        try:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query=cgi.parse_multipart(self.rfile, pdict)
                self.send_response(301)

                self.end_headers()
                upfilecontent = query.get('upfile')
                print "filecontent", upfilecontent[0]
                self.wfile.write("<HTML>POST OK.<BR><BR>");
                self.wfile.write(upfilecontent[0]);

        except:
            pass

def main():
    try:
        parser = argparse.ArgumentParser(prog='ftpredator - preying on stupidly insecure FTP services')
    parser.add_argument("-t", "--target", help="IP address of the target/host to attack", type=str, default="localhost")
    parser.add_argument("-tf", "--target_file", help="File containing a list of targets/hosts on each line", type=str, default="")
    parser.add_argument("-uf", "--username_file", help="File containing a list of usernames to try", type=str, default="USERNAMES")
    parser.add_argument("-pf", "--password_file", help="File containing a list of passwords to try", type=str, default="PASSWORDS")
    parser.add_argument("-sf", "--string_file", help="File containing a list of substrings to match against", type=str, default="STRINGS")

    argmap = parser.parse_args()
    args = vars(argmap)
    host = args["target"]
    host_file = args["target_file"]
    username_file = args["username_file"]
    password_file = args["password_file"]
    string_file = args["string_file"]


        server = HTTPServer(('', 80), GatewayHTTPServerHandler)
        print('Started gateway HTTP server')
        server.serve_forever()

    except KeyboardInterrupt:
        print('^C received, shutting down server')
        server.socket.close()

if __name__ == '__main__':
    main()

