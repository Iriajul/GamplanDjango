from django.urls import path
from .views import CreateNewPlanView, ChatListCreateView, get_last_plan, get_plan_by_id, list_all_plans, get_recent_chat_preview, set_class_title, send_message_to_chat

urlpatterns = [
    path('new/', CreateNewPlanView.as_view(), name='create-new-plan'),
    path('', ChatListCreateView.as_view(), name='chat_list_create'),
    path('last/', get_last_plan, name='get_last_plan'),
    path('<int:chat_id>/', get_plan_by_id, name='get_plan_by_id'),
    path('all/', list_all_plans, name='list_all_plans'),
    path('recent-messages/', get_recent_chat_preview, name='recent_chat_preview'),
    path('set-title/', set_class_title, name='set_class_title'),
    path('<int:chat_id>/send/', send_message_to_chat, name='send_message_to_chat'),
]