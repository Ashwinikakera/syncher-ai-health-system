from rest_framework import serializers
from apps.cycle_app.models import CycleHistory, PredictionFeedback


class CycleStartSerializer(serializers.ModelSerializer):
    """
    Validates POST /api/cycle/start
    {
        "start_date": "2024-03-01"
    }
    """
    class Meta:
        model  = CycleHistory
        fields = ['start_date']


class CycleEndSerializer(serializers.ModelSerializer):
    """
    Validates POST /api/cycle/end
    {
        "end_date": "2024-03-05"
    }
    """
    class Meta:
        model  = CycleHistory
        fields = ['end_date']


class CycleListSerializer(serializers.ModelSerializer):
    """
    Used for GET /api/cycle
    Returns:
    {
        "start_date": "2024-03-01",
        "end_date": "2024-03-05",
        "cycle_length": 28
    }
    """
    class Meta:
        model  = CycleHistory
        fields = ['start_date', 'end_date', 'cycle_length']


class PredictionFeedbackSerializer(serializers.ModelSerializer):
    """
    Validates POST /api/prediction-feedback
    {
        "prediction_correct": false,
        "actual_date": "2024-03-30"
    }
    """
    class Meta:
        model  = PredictionFeedback
        fields = ['prediction_correct', 'actual_date']