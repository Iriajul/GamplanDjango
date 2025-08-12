from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView
from django.utils.timezone import now

from plans.models import Plan
from .models import SavedClass
from .serializers import SetTitleSerializer, SavedClassSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_title(request):
    serializer = SetTitleSerializer(data=request.data)
    if serializer.is_valid():
        plan_id = serializer.validated_data['plan_id']
        title = serializer.validated_data['title']

        try:
            plan = Plan.objects.get(id=plan_id, user=request.user)
            plan.title = title
            plan.save()
            return Response({'message': 'Title updated successfully'})
        except Plan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SaveClassView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        title = request.data.get('title', 'Untitled Class')
        notes = request.data.get('notes', '')

        try:
            plan = Plan.objects.get(id=plan_id, user=request.user)
            if plan.is_saved:
                return Response({'detail': 'Already saved.'}, status=400)

            saved_class = SavedClass.objects.create(
                user=request.user,
                plan=plan,
                title=title,
                notes=notes
            )
            plan.is_saved = True
            plan.save()

            serializer = SavedClassSerializer(saved_class)
            return Response(serializer.data, status=201)

        except Plan.DoesNotExist:
            return Response({'detail': 'Plan not found.'}, status=404)


class SavedClassListView(generics.ListAPIView):
    serializer_class = SavedClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedClass.objects.filter(user=self.request.user).order_by('-created_at')


class CreateManualClassView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        title = request.data.get("title", "Untitled Class")
        notes = request.data.get("notes", "")

        # ✅ Step 1: Create a new saved Plan
        plan = Plan.objects.create(
            user=request.user,
            title=title,
            is_saved=True,
            conversation=[],  # empty chat history for now
        )

        # ✅ Step 2: Link it to SavedClass
        saved_class = SavedClass.objects.create(
            user=request.user,
            plan=plan,
            title=title,
            notes=notes,
        )

        return Response({
            "id": saved_class.id,
            "plan_id": plan.id,
            "title": saved_class.title,
            "notes": saved_class.notes,
            "created_at": saved_class.created_at,
        }, status=status.HTTP_201_CREATED)


class PinnedCalendarView(generics.ListAPIView):
    serializer_class = SavedClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedClass.objects.filter(user=self.request.user, pinned_date__isnull=False)


class PinToCalendarView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        class_id = request.data.get('class_id')
        date_str = request.data.get('pinned_date')

        try:
            saved_class = SavedClass.objects.get(id=class_id, user=request.user)
            saved_class.pinned_date = date_str
            saved_class.save()
            return Response({'detail': 'Pinned to calendar.'})
        except SavedClass.DoesNotExist:
            return Response({'detail': 'Class not found.'}, status=404)
