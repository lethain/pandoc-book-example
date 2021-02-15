import os
import os.path
import yaml
import re
import subprocess
import sys
import urllib.parse
import collections
import png
import pyqrcode
import hashlib


RELATIVE_URL = re.compile('\!?\[(.*?)\]\((.*?)\)')
PULL_DIV = re.compile('<div class="pull">[\S\s]*?</div>')
QUOTES = re.compile('> (.*)')

MISSING_MD_TEMPLATE = """
## %s

[Read draft in google docs](%s)

\\newpage

"""

SLUG_OVERRIDES = {
    'deciding-to-switch': 'deciding-to-switch-companies',
}

FRONT_FILES = [
    {
        'path': "acknowledgments.md",
        "title": "Acknowledgments"
    },
    {
        'path': "foreward.md",
        "title": "Foreword"
    },
    {
        "path": "preface.md",
        "title": "Preface",
    }
]

SOURCE_PATH = "../staff-eng/src/markdown/"
IMAGE_PATH = "../staff-eng/static/"


def build_headers(title, subtitle, author):

    return fmt % (title, subtitle, author)



class Section:
    def __init__(self, book, chapter, data):
        self.book = book
        self.chapter = chapter
        self.data = data
        self.path = None
        self.txt = ""

    def metadata(self):
        md = {}
        if self.txt:
            metalines = []
            first = True
            has_md = False
            for line in self.txt.split('\n'):
                line = line.strip()
                if first and line == '---':
                    has_md = True
                    first = False
                elif not first and not has_md:
                    break
                elif has_md and line in ('---', '...'):
                    break
                elif has_md:
                    key, val = line.split(':')
                    md[key.strip()] = val.strip(" \"")
        return md

    def slug(self):
        return self.data['slug'] if 'slug' in self.data else None

    def draft(self):
        return self.data['draft'] if 'draft' in self.data else None

    def load(self, path):
        self.path = path
        self.txt = open(path, 'r').read()
        # remove pull divs for external links
        self.txt = PULL_DIV.sub('', self.txt)

    def title(self):
        return self.data['title']

    def links(self):
        return [(x,y) for _, x, y in self.links_with_txt()]

    def links_with_txt(self):
        matches = RELATIVE_URL.finditer(self.txt)
        clean = []
        for match in matches:
            txt, path = match.groups()
            clean.append((match.group(0), txt, path))
        return clean


    def relative_urls(self):
        return [x for x in self.links() if x[1].strip().startswith('/')]

    def fix_relative_urls(self, domain):
        done = {}
        for txt, url in self.relative_urls():
            if url in done:
                continue
            done[url] = True
            new_url = urllib.parse.urljoin(domain, url)
            self.txt = self.txt.replace(url, new_url) 

    def squash_refs(self):
        for full, txt, url in self.links_with_txt():
            self.txt = self.txt.replace(full, txt)

    def extract_refs(self, refs):
        done = {}
        for full, txt, url in self.links_with_txt():
            if full in done:
                continue
            done[full] = True
            
            if not url.startswith('#') and not full.startswith('!') and url not in refs:
                refs[url] = txt
                tag = "^" + str(len(refs)) + "^"
                self.txt = self.txt.replace(full, txt+tag)
            elif not full.startswith('!'):
                # remove link
                self.txt = self.txt.replace(full, txt)


    def make_italic_quotes(self):
        new_txt = ""
        for line in self.txt.split('\n'):
            match = QUOTES.search(line)
            if match:
                new_line = "> _" + match.group(1).strip() + '_'
                new_txt += new_line + '\n'
            else:
                new_txt += line + '\n'
        self.txt = new_txt

    def map_urls_to_headers(self, domain, slugs):
        missing = []
        for _txt, link in self.links():
            if link.strip().startswith(domain):
                link_slug = link.split('/')[-1].strip()
                exists = link_slug in slugs
                if link_slug in SLUG_OVERRIDES:
                    override = SLUG_OVERRIDES[link_slug]
                    self.txt = self.txt.replace(link, '#'+override)
                elif link.endswith('png') or link.endswith('jpg'):
                    new_link = link.replace("https://staffeng.com/", IMAGE_PATH)
                    self.txt = self.txt.replace(link, new_link)
                elif not exists:
                    missing.append((link, link_slug, exists))
                else:
                    self.txt = self.txt.replace(link, '#'+link_slug)

        return missing

    def markdown(self):
        txt = ""
        if not 'surpress_title' in self.data:
            slug = self.slug()
            if slug:
                txt += "## %s {#%s}" % (self.title(), self.slug())
            else:
                txt += "## %s" % (self.title(),)
        if self.txt:
            if self.txt.startswith('---'):
                raw = self.txt[3:]
                end = raw.find('---')+3
                raw = raw[end:]
            else:
                raw = self.txt

            txt += "\n\n" + raw.replace("## ", "### ")
            txt += "\n\\newpage\n\n"
        return txt

    def __repr__(self):
        return self.data['title']


class Story(Section):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def slug(self):
        return self.data

    def title(self):
        return self.metadata().get('title', self.data)

    def __repr__(self):
        return self.title()



class Chapter:
    def __init__(self, book, data):
        self.book = book
        self.data = data

    def sections(self):
        if 'sections' in self.data:
            return [Section(self.book, self, x) for x in self.data['sections']]
        return []

    def markdown(self):
        return "\n# %s\n" % self.data['title']

    def stories(self):
        if 'stories' in self.data:
            return [Story(self.book, self, x) for x in self.data['stories']]
        return []

    def __repr__(self):
        return self.data['title']


class Book:
    def __init__(self, index_path):
        self.index = self.load(index_path)

    def markdown_metadata(self):
        with open('./metadata.txt', 'r') as fin:
            return fin.read()

    def title(self):
        return self.index['title']

    def load(self, index_path):
        with open(index_path, 'r') as index_fh:
            parsed = yaml.load(index_fh, Loader=yaml.FullLoader)
            return parsed

    def chapters(self):
        return [Chapter(self, x) for x in self.index['chapters']]

    def slugs(self):
        slugs = []
        for chapter in self.index['chapters']:
            for section in chapter.get('sections', []):
                if 'slug' in section:
                    slugs.append(section['slug'])
            if 'stories' in chapter:
                for story in chapter['stories']:
                    slugs.append(story)

        return slugs

    def __repr__(self):
        title = "%s: %s" % (self.index['title'], self.index['subtitle'])
        return title


def slug_map():
    sm = {}

    directories = ['guides', 'stories']
    base_path = os.path.abspath(SOURCE_PATH)
    for directory in directories:
        dir_path = os.path.join(base_path, directory)
        filenames = os.listdir(dir_path)
        for filename in filenames:
            if not filename.endswith('.md'):
                continue
            filepath = os.path.join(dir_path, filename)
            if not os.path.isfile(filepath):
                continue
            slug = filename.split('.')[0]
            sm[slug] = filepath

    return sm

def flush_references(refs, chunk_size=50, qr=True, qr_scale=2):
    txt = ""

    for i, (ref_url, ref_info) in enumerate(refs.items(), 1):
        hid = None        
        if qr:
            encoded_ref_url = ref_url.encode('utf-8')
            h = hashlib.sha256()
            h.update(encoded_ref_url)
            hid = h.hexdigest()
            qr_path = './qrs/%s.png' % hid
            code = pyqrcode.create(encoded_ref_url)
            code.png(qr_path, scale=qr_scale)

            txt += "\n\\begin{wrapfigure}{r}{1cm}\n"
            txt += "\n\\centering\n"
            txt += "\n\\includegraphics[width=2cm, height=2cm]{%s}\n" % qr_path
            txt += "\n\\end{wrapfigure}\n"
            txt += "\n^%s^" % i

            #full_ref_info = "...%s..." % ref_info
            full_ref_info = "%s" % ref_info
            lines = 0
            txt += "\t"
            
            chunks = []
            for chunk in range(0, len(full_ref_info), chunk_size):
                chunks.append(full_ref_info[chunk:chunk+chunk_size])

            if len(chunks[-1]) < 3:
                chunks[-2] = chunks[-2] + chunks[-1]
                chunks.pop()

            for section in chunks:
                txt += "_%s_  \n" % section.strip()
                lines += 1
            txt += "\n"

            chunks = []
            for chunk in range(0, len(ref_url), chunk_size):
                chunks.append(ref_url[chunk:chunk+chunk_size])

            if len(chunks[-1]) < 3:                
                chunks[-2] = chunks[-2] + chunks[-1]
                chunks.pop()

            for section in chunks:
                txt += "\\underline{\\detokenize{%s}}  \n" % section
                lines += 1

            min_lines  = 8
            if lines < min_lines:
                extra_space = (min_lines - lines) * 4
                txt += "\n\\vspace{%spt}\n" % extra_space


        else:
            txt += "\n^%s^" % i
            txt += "\t_...%s..._  \n" % ref_info
            for chunk in range(0, len(ref_url), chunk_size):
                section = ref_url[chunk:chunk+chunk_size].strip()
                txt += "\\underline{\\detokenize{%s}}  \n" % section

    txt += "\n\\newpage"
    refs.clear()
    return txt


def bind(index_path, domain, print_mode=False, chapter_refs=False):
    if print_mode:
        print("Running in PRINT MODE", file=sys.stderr)

    sm = slug_map()
    bk = Book(index_path)
    book_slugs = bk.slugs()

    incomplete = []
    missing_file = []
    relative_urls = []
    refs = collections.OrderedDict()

    txt = ""
    txt += bk.markdown_metadata() + "\n\n"
    txt += "\n\n\\newpage\n\n"

    frontmatter = [Section(bk, None, x) for x in FRONT_FILES]
    for section in frontmatter:
        section.load(section.data['path'])
        if print_mode:
            section.squash_refs()
        txt += "\n\n" + section.markdown()

    slugs_only_on_staffeng = []
    for chapter in bk.chapters():
        txt += "\n\n"
        txt += chapter.markdown()
        txt += '\n![](./StaffEng-ChapterBreak.png)\n\n'

        content = chapter.sections() + chapter.stories()
        for section in content:
            slug = section.slug()
            if not slug:
                incomplete.append(section)
                missing_md =  MISSING_MD_TEMPLATE % (section.title(), section.draft())
                txt += missing_md
            elif slug not in sm:
                missing_file.append(section)
            else:
                path = sm[slug]
                section.load(path)
                section.fix_relative_urls(domain)
                section.make_italic_quotes()
                missing_from_map = section.map_urls_to_headers(domain, book_slugs)
                slugs_only_on_staffeng += missing_from_map

                bad_urls = section.relative_urls()
                if bad_urls:
                    relative_urls.append((slug, bad_urls))

                if print_mode:
                    section.extract_refs(refs)

                txt += "\n\n" + section.markdown()
                if print_mode and chapter_refs and len(refs) > 0:
                    txt += "\n\\newpage"
                    txt += "\n### References"
                    txt += "\n\n" + flush_references(refs)

    if print_mode and not chapter_refs:
        txt += "\n\\newpage"
        txt += "\n\n# References\n\n"
        txt += "\n\n" + flush_references(refs)

    print(txt)

    if incomplete:
        print("\n## Sections missing a slug", file=sys.stderr)
        for section in incomplete:
            print('\t', section, file=sys.stderr)
    if missing_file:
        print("\n## Sections without file matching slug", file=sys.stderr)
        for section in missing_file:
            print('\t', section, section.slug(), file=sys.stderr)
    if relative_urls:
        print("\n## Relative urls", file=sys.stderr)
        for slug, slug_relative_urls in relative_urls:
            print('\t', slug, file=sys.stderr)
            for url in slug_relative_urls:
                print('\t\t', url, file=sys.stderr)
    if slugs_only_on_staffeng:
        print("\n## Book domain slugs that are not in book index", file=sys.stderr)
        for slug, _, _ in slugs_only_on_staffeng:
            print('\t', slug, file=sys.stderr)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("index", help="path to index yaml")
    parser.add_argument("--domain", help="protocol plus domain to rewrite relative URLs", default="https://staffeng.com")
    parser.add_argument("--print-mode", help="print mode", action='store_true')
    parser.add_argument("--chapter-refs", help="use chapter references", action='store_true')    
    args = parser.parse_args()
    index_path = args.index
    bind(index_path, args.domain, print_mode=args.print_mode, chapter_refs=args.chapter_refs)
