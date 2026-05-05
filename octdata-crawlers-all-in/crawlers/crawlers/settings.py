# Configurações personalizadas do framework, em caso de dúvida, conferir a documentação do Scrapy.

# BOT_NAME = "crawlers"

YEARS = [y for y in range (2009, 2027)]
SPIDER_MODULES = ["crawlers.spiders"]
NEWSPIDER_MODULE = "crawlers.spiders"

#USER_AGENT = "crawlers (+http://www.yourdomain.com)"

ROBOTSTXT_OBEY = False

#DOWNLOAD_DELAY = 3
CONCURRENT_REQUESTS = 6
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

ITEM_PIPELINES = {
    "crawlers.pipelines.CrawlersPipeline": 300,
}

LOG_LEVEL = 'INFO'

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://www.google.com/'
}