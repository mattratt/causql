from scraper import Scraper


# reference:
# https://meta.stackexchange.com/questions/288059/how-to-download-dataexplorer-queries


QUERY_LIST_URL = 'http://data.stackexchange.com/stackoverflow/queries?order_by=everything' + \
                 '&page={}&pagesize={}'


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
def get_query_links(page, rpp=100):
    url = get_query_list_url(page, rpp)
    print url

    scrape = Scraper(url)
    i = 0
    while scrape.move_to('<div class="title">') != -1:
        url = scrape.pull_from_to(' href="', '"')
        title = scrape.pull_from_to('>', '</a>')

        print i, title, url
        print ""
        i += 1

#####################################################
if __name__ == '__main__':

    page = 1
    get_query_links(page)








