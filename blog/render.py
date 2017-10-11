#!/usr/bin/env python3

"""
Small blog renderer from MD.
"""

import markdown
import sys, os
import json
import datetime
import hashlib

ROOT = os.path.abspath(os.path.dirname(sys.argv[0]))

def _digest(s):
    if isinstance(s, str):
        s = s.encode('utf-8')
    return hashlib.sha224(s).hexdigest()[:16]

class PostBase:
    def get_title(self):
        " Get title of this post "
        return "Untitled"

    def get_id(self):
        " Get unique post id "
        assert(False)

    def get_html(self):
        " Get post content as HTML "
        assert(False)

    def get_hash(self):
        " Get the content hash. "
        return _digest(self.get_html()) # Better to use hash of the source


class PostMD(PostBase):
    def __init__(self, filename):
        with open(filename, "rt") as f:
            self.data = f.read()

        html = markdown.markdown(self.data, output_format = 'html5', extensions = [ 'markdown.extensions.codehilite' ])
        for level in range(5, 0, -1):
            html = html.replace("<h%d>" % level, "<h%d>" % (level + 1)).replace("</h%d>" % level, "</h%d>" % (level + 1))
        # Try to find title:
        hh = html.split("<h2>", 1)
        if len(hh) == 2:
            title = hh[1].split("</h2>", 1)[0]
            if len(title) > 100:
                title = title[:97] + "..."
        else:
            title = "Untitled"

        self.title = title
        self.html = html
        self.page_id = os.path.basename(filename[:-3])

    def get_title(self):
        return self.title

    def get_id(self):
        return self.page_id

    def get_html(self):
        return self.html

    def get_hash(self):
        " Get the content hash. "
        return _digest(self.data)

def load_post(filename):
    if filename.endswith(".md"):
        return PostMD(filename)
    print("WARNING: %s format is unknown" % filename)
    return None

class Blog:
    def __init__(self, top):
        self.top = os.path.abspath(top)

        fnm = os.path.join(self.top, "db.json")

        with open(fnm, "rt") as f:
            self.data = json.load(f)

        tdir = os.path.join(self.top, "template")

        with open(os.path.join(tdir, "header.html")) as f:
            self._header = f.read()
        with open(os.path.join(tdir, "footer.html")) as f:
            self._footer = f.read()

        self._load()

    def _load(self):
        d = os.path.join(self.top, "posts")
        posts = []
        for fnm in os.listdir(d):
            post = load_post(os.path.join(d, fnm))
            if isinstance(post, PostBase):
                posts.append(post)

        blog = self.data["blog"]

        # Process new posts:
        for post in posts:
            id = post.get_id()
            if id not in blog:
                meta = { "id": id }
                now = datetime.datetime.now()
                meta["created"] = now.ctime()
                meta["updated"] = now.ctime()
                meta["ts_created"] = now.timestamp()
                meta["ts_updated"] = now.timestamp()
                meta["digest"] = post.get_hash()
                meta["title"] = post.get_title()
                blog[id] = meta
            elif blog[id]["digest"] != post.get_hash():
                blog[id]["digest"] = post.get_hash()
                now = datetime.datetime.now()
                blog[id]["updated"] = now.ctime()
                blog[id]["ts_updated"] = now.timestamp()
                blog[id]["title"] = post.get_title()

        # TODO: remove posts
        # Sort them all:
        def post_key(a):
            return self.data["blog"][a.get_id()]["ts_updated"]
        posts.sort(key = post_key, reverse = True)
        self.posts = posts

        # TODO: tags, ...

    def _write_page(self, page):
        name = "p_%s.html" % page.get_id()
        with open(name, "wt") as f:
            f.write(page.get_html())
        return name

    def render(self):
        with open(os.path.join(self.top, "index.html"), "wt") as f:
            f.write(self._header)
            for i, p in enumerate(self.posts):
                self._write_page(p)
                if i < 10:
                    f.write("""<div class="blog-post">\n%s\n</div>""" % p.get_html())
            f.write(self._footer)

        fnm = os.path.join(self.top, "db.json")
        with open(fnm, "wt") as f:
            json.dump(self.data, f)

def main():
    blog = Blog(ROOT)
    blog.render()

if __name__ == '__main__':
    main()
