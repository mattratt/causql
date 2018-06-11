import sys
import logging
import csv
import getpass
from HTMLParser import HTMLParser
from urllib2 import URLError
from httplib import BadStatusLine
from joblib import Parallel, delayed
from scraper import Scraper


# reference:
# https://meta.stackexchange.com/questions/288059/how-to-download-dataexplorer-queries


QUERY_LIST_URL = 'http://data.stackexchange.com/stackoverflow/queries?order_by=everything' + \
                 '&page={}&pagesize={}'


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
csv.field_size_limit(sys.maxsize)
html_parser = HTMLParser()  # we should prob use this for everything instead of low-budget scraper


def get_query_list_url(page, rpp):
    return QUERY_LIST_URL.format(page, rpp)


# <li>
#     <div class="favorites">
#     </div>
#     <div class="views">
#         <span class="totalViews"><span class="pretty-short" title="">0</span></span>
#         <span class="viewDesc">views</span>
#     </div>
#     <div class="title">
#         <h3>
#             <a title="" href="/stackoverflow/revision/860531/1062620/all-questions-with-python-and-r-tag">All questions with python and R tag</a>
#         </h3>
#     </div>
#     <div class="user">
#         <span title="2018-06-08 16:35:32Z" class="relativetime">jun 8</span>
#     </div>
#     <div class="clear"></div>
# </li>
def get_query_links(page, rpp):
    url = get_query_list_url(page, rpp)
    print url

    query_urls = []
    scrape = Scraper(url)
    i = 0
    while scrape.move_to('<div class="title">') != -1:
        url = 'http://data.stackexchange.com/' + scrape.pull_from_to(' href="', '"')
        title = scrape.pull_from_to('>', '</a>')
        query_urls.append(url)
        # print i, title, url
        # print ""
        i += 1
    return query_urls


def clean_sql(sql):
    sql_space = ' '.join(sql.split())
    try:
        sql_unesc = html_parser.unescape(sql_space)
    except UnicodeDecodeError:
        return sql_space
    return sql_unesc


# <pre id="queryBodyText" class="cm-s-default"><code>select * from comments where text like &#39;%lamp%&#39;</code></pre>
# ...
# </div>
#     </td>
#     <td class="post-signature">
#          <div class="user-info owner">
#     <div class="user-action-time">created <span title="2018-05-19 11:08:45Z" class="relativetime">may 19</span></div>
#         <div class="user-gravatar32">
#                 <a href="/users/26658"><img src="//www.gravatar.com/avatar/217dcfb97fdbd00aa573257dffa226b9?s=64&amp;d=identicon&amp;r=PG" height="32px" width="32px" class="logo"></a>
#                 <a href="/users/26658">JonathanDavidArndt</a>
#         </div>
# </div>
def get_query_info(url):
    try:
        scrape = Scraper(url)
    except (URLError, BadStatusLine) as err:
        print "url error: ", url, err
        return None

    scrape.move_to('<pre id="queryBodyText" class="cm-s-default">')
    sql_raw = scrape.pull_from_to('<code>', '</code>')
    sql = clean_sql(sql_raw)
    scrape.move_to('> created <span')
    ts = scrape.pull_from_to('title="', '" class="relativetime"')
    scrape.move_to('<div class="user-gravatar32">')
    if scrape.comes_before('<a href="/users', '</div>'):
        user_id = scrape.pull_from_to('<a href="/users/', '"><img ')
        scrape.move_to('<a href="/users/')
        user_name = scrape.pull_from_to('>', '</a>')
    else:
        user_id = None
        user_name = None
    return (ts, url, sql, user_id, user_name)


def get_query_infos(outfile_name, cache_prev=False, rpp=100):

    prev_urls = {}
    if cache_prev:
        prev_urls = read_query_urls_from_file(outfile_name)

    query_tups = []
    for page in range(1, 3000000):
        query_urls = get_query_links(page, rpp)

        if len(query_urls) == 0:
            break

        # for i, url in enumerate(query_urls):
        #     tup = get_query_info(url)
        #     print i, tup
        #     query_tups.append(tup)

        query_urls = [ u for u in query_urls if u not in prev_urls ]
        print "page {}, got {} query urls".format(page, len(query_urls))

        # Parallel(n_jobs=2)(delayed(sqrt)(i ** 2) for i in range(10))
        tups = Parallel(n_jobs=4)(delayed(get_query_info)(url) for url in query_urls)

        with open(outfile_name, 'a') as outfile:
            writer = csv.writer(outfile, delimiter="\t")
            for tup in tups:
                if tup is not None:
                    try:
                        writer.writerow(tup)
                    except UnicodeEncodeError as err:
                        print "can't write tup:", tup

        query_tups.extend(tups)

    return query_tups


def read_query_urls_from_file(file_path):
    query_urls = set()
    with open(file_path, 'r') as infile:
        reader = csv.reader(infile, delimiter="\t")
        for i, row in enumerate(reader):
            if i % 100000 == 0:
                print "\t", i, "\t", len(query_urls)
            ts, url, sql, user_id, user_name = row
            query_urls.add(url)
    return query_urls


#####################################################
if __name__ == '__main__':

    outfile_path = sys.argv[1]

    get_query_infos(outfile_path, cache_prev=True)








