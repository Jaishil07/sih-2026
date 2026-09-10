from django.views import View
from apps.cases.views import GlobalSearchView, sanitize_search_snippet

global_search_view = GlobalSearchView.as_view()
