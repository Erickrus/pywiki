# -*- coding: utf-8 -*-

import base64
import datetime
import glob
import json
import os
import re
import sys
import tornado
import traceback

from html.parser import HTMLParser
import markdown as md
import mdx_math

import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, os.path, random, string
from tornado.options import define, options
from tornado.web import StaticFileHandler

# wget https://github.com/mathjax/MathJax/archive/2.7.5.zip
# unzip 2.7.5.zip -d static/js
# rm 2.7.5.zip

portNum = 8080
define("port", default=portNum, help="run on the given port", type=int)

class CustomizedHTMLParser(HTMLParser):
    def set_tag(self, tag, attr):
        self.tag = tag
        self.attr = attr

    def handle_starttag(self, tag, attrs):
        if 'value' not in dir(self):
            self.value = ''
        attrDict = {}
        for attr in attrs:
            attrDict[attr[0].lower()] = attr[1]
        if tag.lower() == self.tag and self.attr in attrDict:
            self.value = attrDict[self.attr]

class Wiki:
    def __init__(self, baseDir):
        self.baseDir = baseDir
        self.imgPattern = r'<[Ii][Mm][Gg][\w\W]+?/?>'
        self.urlPattern = r'<[aA][\w\W]+?/?>'

    def find(self, keywords):
        foundFilenames = []
        for filename in glob.glob(os.path.join(self.baseDir, "**/*.md"), recursive=True):
            found = 0
            with open(filename, 'r') as f:
                mdText = f.read().lower()
            for keyword in keywords:
                if mdText.find(keyword.lower()) >= 0:
                    found += 1
            if found>0:
                foundFilenames.append({"filename": filename, "found":found})

        filenames = []
        foundFilenames = sorted(foundFilenames, key=lambda x: -x['found'])
        for filename in foundFilenames:
            filename = filename['filename']
            title= os.path.basename(filename)[:-3].replace('_',' ').title()
            filenames.append(
                "<a class='innerLink' href='#' onclick='api.goto(\"%s\")'>%s</a><br/>" % (
                    filename[len(self.baseDir):],
                    title
                )
            )
        return "\n".join(filenames), ''

    def display_dir(self, url):
        originUrl = ""+url
        if url.startswith('/'):
            url = url[1:]
        filenames , entries = [], []
        
        for dirpath, dirnames, files in os.walk(os.path.join(self.baseDir, url)):
            if dirpath == os.path.join(self.baseDir, url):
                for dirname in dirnames:
                    title= "[%s]"%os.path.basename(dirname)
                    entries.append(
                        "<a class='innerLink' href='#' onclick='api.goto(\"%s\")'>%s</a><br/>" % (
                            os.path.join(originUrl, dirname),
                            title
                        )
                    )
                for filename in files:
                    if filename.lower().endswith('.md'):
                        title= os.path.basename(filename)[:-3].replace('_',' ').title()
                        filenames.append(
                            "<a class='innerLink' href='#' onclick='api.goto(\"%s\")'>%s</a><br/>" % (
                                os.path.join(originUrl, filename), 
                                title
                            )
                        )
        entries = sorted(entries)

        if originUrl != '/':
            entries.insert(0,
                "<a class='innerLink' href='#' onclick='api.goto(\"%s\")'>%s</a><br/>" % (
                os.path.join(os.path.dirname(originUrl)),
                '[..]')
            )


        filenames = sorted(filenames)
        entries.extend(filenames)

        mdHtml, mdText = '\n'.join(entries), ''
        return mdHtml, mdText

    def display(self, url):
        #url = url.replace(".md", ".txt")
        if url.startswith('/'):
            url = url[1:]
        with open(os.path.join(self.baseDir, url)) as f:
            mdText = f.read()
        originMdText = mdText+""

        matches = re.findall(self.imgPattern, mdText)
        for match in matches:
            ihp = CustomizedHTMLParser()
            ihp.set_tag('img', 'src')
            ihp.feed(match)
            imUrl = ihp.value
            if imUrl.startswith('/'):
                imFilename = os.path.join(self.baseDir, imUrl[1:])
                with open(imFilename, 'rb') as f:
                    imB64 = base64.encodebytes(f.read()).decode('utf-8').replace('\n','')
                imExt = os.path.splitext(imFilename)[1][1:].lower()
                if imExt == 'jpg':
                    imExt = 'jpeg'
                imStr = '<img src="data:image/%s;base64, %s" />' % (imExt.upper(), imB64)
                mdText = mdText.replace(match, imStr)

        mdHtml = md.markdown(mdText, extensions=[
            mdx_math.MathExtension(enable_dollar_delimiter=True), 
            'fenced_code'
        ])
        matches = re.findall(self.urlPattern, mdHtml)
        for match in matches:
            ahp = CustomizedHTMLParser()
            ahp.set_tag('a', 'href')
            ahp.feed(match)
            if ahp.value.startswith("/"):
                last = 1
                if match.endswith("/>"):
                    last = 2
                repl = '<a class="innerLink" href="#"' + " onclick='api.goto(\"%s\")'" % ahp.value+ match[-last:]
                mdHtml = mdHtml.replace(match, repl)
            

        #return IPython.display.display(Markdown(mdText))
        return mdHtml, originMdText


class WikiModifyHandler(tornado.web.RequestHandler):

    def initialize(self, wiki):
        tornado.web.RequestHandler.initialize(self)
        self.wiki = wiki

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS')

    def options(self):
        # no body
        self.set_header("Access-Control-Allow-Headers","*")
        self.set_status(204)
        self.finish()

    def error_out(self, message):
        self.set_status(400)
        return self.finish(json.dumps({"error": message}))

    def post(self):
        data = json.loads(self.get_argument("json"))
        res = {}

        requiredFields = ["mdUrl", "mdText"]
        requiredFields = []
        for requiredField in requiredFields:
            if requiredField not in data:
                self.set_status(400)
                return self.finish(json.dumps({"error":"Missing data. Required JSON fields: %s" % ", ".join(requiredFields)}))

        mdUrl = data["mdUrl"]
        mdText = data["mdText"]
        with open(os.path.join(os.getcwd(), mdUrl[1:]), "w") as f:
            f.write(mdText)
        html, mdText = "Page not found", ""
        try:
            html, mdText = self.wiki.display(mdUrl)
        except:
            traceback.print_exc()
            pass

        res = {
            "mdUrl": mdUrl, 
            "content":html,
            "md": mdText
        }
        self.write({"message":"ok", "data": res})

class WikiPageHandler(tornado.web.RequestHandler):

    def initialize(self, wiki):
        tornado.web.RequestHandler.initialize(self)
        self.wiki = wiki

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS')

    def options(self):
        # no body
        self.set_header("Access-Control-Allow-Headers","*")
        self.set_status(204)
        self.finish()

    def error_out(self, message):
        self.set_status(400)
        return self.finish(json.dumps({"error": message}))

    def post(self):
        data = json.loads(self.get_argument("json"))
        res = {}

        requiredFields = ["mdUrl"]
        requiredFields = []
        for requiredField in requiredFields:
            if requiredField not in data:
                self.set_status(400)
                return self.finish(json.dumps({"error":"Missing data. Required JSON fields: %s" % ", ".join(requiredFields)}))

        mdUrl = data["mdUrl"]
        html, mdText = "Page not found", ""

        if mdUrl.startswith('find:'):
            keywords = mdUrl[5:].strip().split(' ')
            html, mdText = self.wiki.find(keywords)
        else:
            try:
                html, mdText = self.wiki.display(mdUrl)
            except IsADirectoryError:
                html, mdText = self.wiki.display_dir(mdUrl)
            except:
                traceback.print_exc()
                pass

        res = {
            "mdUrl": mdUrl, 
            "content":html,
            "md": mdText
        }
        self.write({"message":"ok", "data": res})

wiki = Wiki(os.path.join(os.getcwd(), "repo"))

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"^/wiki/api/page", WikiPageHandler,  {"wiki": wiki}),
            (r"^/wiki/api/modify",  WikiModifyHandler, {"wiki": wiki}),
            (r'^/static/(.*?)$',
             StaticFileHandler,
             {"path":os.path.join(os.getcwd(), "static"), "default_filename":"index.html"}),
            (r'/(favicon.ico)', StaticFileHandler, {"path": os.path.join(os.getcwd(), "static")}),
        ]
        tornado.web.Application.__init__(self, handlers)

def main(argv):
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(portNum)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main(sys.argv)

