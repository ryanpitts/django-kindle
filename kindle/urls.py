from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url(
        regex   = '^kindle-xml/section-manifest/$',
        view    = 'kindle.views.kindle_section_manifest',
        kwargs  = {},
        name    = 'kindle_section_manifest_today',
    ),

    url(
        regex   = '^kindle-xml/section-manifest/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/$',
        view    = 'kindle.views.kindle_section_manifest',
        kwargs  = {},
        name    = 'kindle_section_manifest',
    ),

    url(
        regex   = '^kindle-xml/article-manifest/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<section>[-\w]+)/$',
        view    = 'kindle.views.kindle_article_manifest',
        kwargs  = {},
        name    = 'kindle_article_manifest',
    ),

    url(
        regex   = '^kindle-xml/article-file/(?P<object_id>[-\w]+)/$',
        view    = 'kindle.views.kindle_article_detail',
        kwargs  = {},
        name    = 'kindle_article_file',
    ),
)
