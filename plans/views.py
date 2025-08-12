# --- IMPORTS ---
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from .models import Plan
from payments.utils import has_active_subscription_or_trial

from .serializers import (
    PlanSerializer, 
    PlanSummarySerializer, 
    ChatMessageSerializer,
)
from ai.agent import generate_ai_response


# --- /api/chats/new ---
class CreateNewPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan = Plan.objects.create(user=request.user)
        serializer = PlanSerializer(plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# --- /api/chats/ ---
class ChatListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = Plan.objects.filter(user=request.user).order_by('-created_at')[:10]
        serializer = PlanSummarySerializer(plans, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ChatMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message = serializer.validated_data['message']
        try:
            plan = Plan.objects.filter(user=request.user).latest('created_at')
        except Plan.DoesNotExist:
            return Response({"error": "No plan found. Please create a new plan first."}, status=status.HTTP_404_NOT_FOUND)

        plan.conversation.append({"role": "user", "content": message})
        ai_response = generate_ai_response(message)
        plan.conversation.append({"role": "assistant", "content": ai_response})
        plan.save()

        return Response({
            "message": message,
            "response": ai_response,
            "plan_id": plan.id
        }, status=status.HTTP_200_OK)


# --- GET /api/chats/last ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_last_plan(request):
    user = request.user
    last_plan = Plan.objects.filter(user=user).order_by('-created_at').first()

    if not last_plan:
        return Response({"detail": "No plan found."}, status=404)

    return Response({
        "id": last_plan.id,
        "title": last_plan.title,
        "conversation": last_plan.conversation,
        "is_saved": last_plan.is_saved,
        "pinned_date": last_plan.pinned_date,
        "created_at": last_plan.created_at,
        "updated_at": last_plan.updated_at,
    })


# --- GET /api/chats/{chat_id} ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_plan_by_id(request, chat_id):
    try:
        plan = Plan.objects.get(id=chat_id, user=request.user)
    except Plan.DoesNotExist:
        return Response({"detail": "Plan not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "id": plan.id,
        "title": plan.title,
        "conversation": plan.conversation,
        "is_saved": plan.is_saved,
        "pinned_date": plan.pinned_date,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
    })


# --- GET /api/chats/all-plans (paginated) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_plans(request):
    user = request.user
    plans = Plan.objects.filter(user=user).order_by('-created_at')

    paginator = PageNumberPagination()
    paginator.page_size = 5
    result_page = paginator.paginate_queryset(plans, request)
    serializer = PlanSummarySerializer(result_page, many=True)

    return paginator.get_paginated_response(serializer.data)


# --- GET /api/chats/recent-messages ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recent_chat_preview(request):
    user = request.user
    plan = Plan.objects.filter(user=user).order_by('-updated_at').first()

    if not plan or not plan.conversation:
        return Response({"detail": "No recent conversation found."}, status=404)

    user_msg = None
    ai_msg = None
    for message in reversed(plan.conversation):
        if message['role'] == 'assistant' and not ai_msg:
            ai_msg = message['content']
        elif message['role'] == 'user' and not user_msg:
            user_msg = message['content']
        if user_msg and ai_msg:
            break

    return Response({
        "plan_id": plan.id,
        "title": plan.title,
        "last_user_message": user_msg,
        "last_ai_response": ai_msg,
        "updated_at": plan.updated_at,
    })

# --- POST /api/chats/set-title ---
@api_view(['POST'])
def set_class_title(request):
    plan_id = request.data.get('plan_id')
    title = request.data.get('title')

    if not plan_id or not title:
        return Response({'error': 'plan_id and title are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        plan = Plan.objects.get(id=plan_id)
        plan.title = title
        plan.save()
        return Response({'message': 'Title updated successfully.'})
    except Plan.DoesNotExist:
        return Response({'error': 'Plan not found.'}, status=status.HTTP_404_NOT_FOUND)

# --- POST /api/chats/{chat_id}/ ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message_to_chat(request, chat_id):
    user = request.user

    # Check subscription or trial before allowing chat
    if not has_active_subscription_or_trial(user):
        return Response(
            {"error": "Your free trial has ended. Please upgrade to Pro."},
            status=403
        )

    try:
        plan = Plan.objects.get(id=chat_id, user=user)
    except Plan.DoesNotExist:
        return Response({"detail": "Plan not found."}, status=status.HTTP_404_NOT_FOUND)

    message = request.data.get("message")
    if not message:
        return Response({"error": "Message is required."}, status=400)

    # Append user message
    plan.conversation.append({"role": "user", "content": message})

    # Generate AI response
    ai_response = generate_ai_response(message)

    # Append assistant response
    plan.conversation.append({"role": "assistant", "content": ai_response})
    plan.save()

    return Response({
        "message": message,
        "response": ai_response,
        "plan_id": plan.id
    }, status=200)