from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.health_app.models import MyHealth
from apps.health_app.serializers import MyHealthSerializer
from utils.response_format import success_response, error_response


def get_health_score(data):
    """
    Basic scoring stub until Dev3 ML is ready.
    Dev3 will replace this with their scoring logic.
    """
    score = 0

    if data.get('q1') == 'Persistent/recurrent':  score += 20
    elif data.get('q1') == 'Occasionally missed':  score += 10

    if data.get('q2') == 'Heavy':    score += 15
    elif data.get('q2') == 'Moderate': score += 8

    if data.get('q3') == 'Significant': score += 15
    elif data.get('q3') == 'Noticeable': score += 8

    if data.get('q4') == 'Severe (9+ kg)':    score += 15
    elif data.get('q4') == 'Moderate (5-8 kg)': score += 8

    if data.get('q5') == 'Moderate': score += 10
    elif data.get('q5') == 'Mild':   score += 5

    if data.get('q6') == 'Yes': score += 5

    if data.get('q7') == 'Significant': score += 10
    elif data.get('q7') == 'Mild':      score += 5

    if data.get('q8') == 'Strong fatigue/crashes': score += 10
    elif data.get('q8') == 'Mild fatigue':          score += 5

    # Determine risk level
    if score >= 60:
        risk_level = 'High'
    elif score >= 30:
        risk_level = 'Moderate'
    else:
        risk_level = 'Low'

    return score, risk_level


def get_health_insights(score, risk_level, data):
    """
    Basic insights stub until Dev3 ML is ready.
    """
    insights = []

    if data.get('q1') == 'Persistent/recurrent':
        insights.append("Your symptoms suggest possible hormonal imbalance")

    if data.get('q3') in ['Noticeable', 'Significant'] and data.get('q8') == 'Strong fatigue/crashes':
        insights.append("Weight and fatigue patterns indicate metabolic risk")

    if data.get('q9') in ['Never', '1 time/week']:
        insights.append("Improving physical activity may help regulate cycles")

    if not insights:
        insights.append("Keep tracking your health for better insights")

    return insights


class MyHealthView(APIView):
    """
    POST /api/my-health — save health questionnaire
    GET  /api/my-health — get responses + score + risk + insights
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Request:
        {
            "q1": "Persistent/recurrent",
            ...
            "q10": "Mixed"
        }
        Response:
        {
            "message": "Health data saved"
        }
        """
        # Check if already submitted
        existing = MyHealth.objects.filter(user=request.user).first()

        serializer = MyHealthSerializer(
            existing,
            data=request.data,
            partial=False
        ) if existing else MyHealthSerializer(data=request.data)

        if serializer.is_valid():
            # -------------------------------------------------------
            # DEV3 INTEGRATION POINT
            # When Dev3 scoring is ready, uncomment below
            # -------------------------------------------------------
            # import sys
            # sys.path.append('../ml_service')
            # from health.scorer import get_score
            # score, risk_level = get_score(serializer.validated_data)
            # -------------------------------------------------------

            # STUB scoring
            score, risk_level = get_health_score(serializer.validated_data)

            if existing:
                # Update existing
                for field, value in serializer.validated_data.items():
                    setattr(existing, field, value)
                existing.score      = score
                existing.risk_level = risk_level
                existing.save()
            else:
                # Create new
                serializer.save(
                    user       = request.user,
                    score      = score,
                    risk_level = risk_level
                )

            return success_response(message="Health data saved", status=201)

        first_error = list(serializer.errors.values())[0][0]
        return error_response(str(first_error), status=400)

    def get(self, request):
        """
        Response:
        {
            "responses": { "q1": "...", ... "q10": "..." },
            "score": 65,
            "risk_level": "Moderate",
            "insights": ["...", "..."]
        }
        """
        try:
            health = MyHealth.objects.get(user=request.user)
        except MyHealth.DoesNotExist:
            return error_response("No health data found. Please complete the questionnaire.", status=404)

        responses = {
            'q1':  health.q1,
            'q2':  health.q2,
            'q3':  health.q3,
            'q4':  health.q4,
            'q5':  health.q5,
            'q6':  health.q6,
            'q7':  health.q7,
            'q8':  health.q8,
            'q9':  health.q9,
            'q10': health.q10,
        }

        insights = get_health_insights(health.score, health.risk_level, responses)

        return success_response(data={
            "responses":  responses,
            "score":      health.score,
            "risk_level": health.risk_level,
            "insights":   insights
        })