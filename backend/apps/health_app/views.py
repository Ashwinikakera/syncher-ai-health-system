from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.health_app.models import MyHealth
from apps.health_app.serializers import MyHealthSerializer
from utils.response_format import success_response, error_response
from apps.chatbot_app.llm import analyze_health_questionnaire


def get_health_score(data):
    """
    Calculate health score from questionnaire answers.
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


class MyHealthView(APIView):
    """
    Health questionnaire endpoint with AI analysis
    POST /api/my-health - save questionnaire
    GET  /api/my-health - get analysis + insights
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Save health questionnaire and analyze with AI"""
        if request.user.is_onboarded == False:
            return error_response("Please complete onboarding first", status=400)

        existing = MyHealth.objects.filter(user=request.user).first()
        serializer = MyHealthSerializer(
            existing,
            data=request.data,
            partial=False
        ) if existing else MyHealthSerializer(data=request.data)

        if serializer.is_valid():
            # Calculate score
            score, risk_level = get_health_score(serializer.validated_data)

            # Get AI analysis
            analysis_result = analyze_health_questionnaire(
                health_data=serializer.validated_data,
                score=score,
                risk_level=risk_level
            )

            # Save to database
            if existing:
                for field, value in serializer.validated_data.items():
                    setattr(existing, field, value)
                existing.score = score
                existing.risk_level = risk_level
                existing.save()
            else:
                serializer.save(
                    user=request.user,
                    score=score,
                    risk_level=risk_level
                )

            return success_response(
                data={
                    "message": "Health data saved",
                    "score": score,
                    "risk_level": risk_level,
                    "ai_analysis": analysis_result.get("analysis")
                },
                status=201
            )

        first_error = list(serializer.errors.values())[0][0]
        return error_response(str(first_error), status=400)

    def get(self, request):
        """Get health data with AI analysis"""
        try:
            health = MyHealth.objects.get(user=request.user)
        except MyHealth.DoesNotExist:
            return error_response("No health data found. Please complete the questionnaire.", status=404)

        responses = {
            'q1': health.q1, 'q2': health.q2, 'q3': health.q3, 'q4': health.q4,
            'q5': health.q5, 'q6': health.q6, 'q7': health.q7, 'q8': health.q8,
            'q9': health.q9, 'q10': health.q10,
        }

        # Get fresh AI analysis
        analysis_result = analyze_health_questionnaire(
            health_data=responses,
            score=health.score,
            risk_level=health.risk_level
        )

        return success_response(data={
            "responses": responses,
            "score": health.score,
            "risk_level": health.risk_level,
            "ai_analysis": analysis_result.get("analysis")
        })