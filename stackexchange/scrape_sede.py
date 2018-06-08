from scraper import Scraper
from HTMLParser import HTMLParser

# reference:
# https://meta.stackexchange.com/questions/288059/how-to-download-dataexplorer-queries


QUERY_LIST_URL = 'http://data.stackexchange.com/stackoverflow/queries?order_by=everything' + \
                 '&page={}&pagesize={}'


html_parser = HTMLParser()  # we should prob use this for everything instead of low budget scaper


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

        print i, title, url
        print ""
        i += 1
    return query_urls


def clean_sql(sql):
    return html_parser.unescape(' '.join(sql.split()))


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
    scrape = Scraper(url)
    scrape.move_to('<pre id="queryBodyText" class="cm-s-default">')
    sql_raw = scrape.pull_from_to('<code>', '</code>')
    sql = clean_sql(sql_raw)
    scrape.move_to('<div class="user-gravatar32">')
    if scrape.comes_before('<a href="/users', '</div>'):
        user_id = scrape.pull_from_to('<a href="/users/', '"><img ')
        scrape.move_to('<a href="/users/')
        user_name = scrape.pull_from_to('>', '</a>')
    else:
        user_id = None
        user_name = None
    return (sql, user_id, user_name)


def get_query_infos(rpp=100):
    query_tups = []
    for page in range(1, 1000000):
        query_urls = get_query_links(page, rpp)
        print "page {}, got {} query urls".format(page, len(query_urls))

        if (page > 3) or len(query_urls) == 0:
            break

        for i, url in enumerate(query_urls):
            tup = get_query_info(url)
            print i, tup
            query_tups.append(tup)

    return query_tups


#####################################################
if __name__ == '__main__':

    get_query_infos()








