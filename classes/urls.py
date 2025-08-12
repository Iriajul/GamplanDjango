from django.urls import path
from .views import (
    set_title,
    SaveClassView,
    SavedClassListView,
    CreateManualClassView,
    PinnedCalendarView,
    PinToCalendarView,
)

urlpatterns = [
    path('set-title/', set_title),
    path('save/', SaveClassView.as_view()),
    path('saved/', SavedClassListView.as_view()),
    path('create/', CreateManualClassView.as_view()),
    path('calendar/', PinnedCalendarView.as_view()),
    path('pin/', PinToCalendarView.as_view()),
]
