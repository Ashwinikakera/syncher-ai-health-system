from rest_framework import serializers
from apps.cycle_app.models import CycleHistory


class CycleSerializer(serializers.ModelSerializer):
    """
    Handles both POST and GET /api/cycle

    POST validates:
    {
        "start_date": "2024-03-01",
        "end_date": "2024-03-05"
    }

    GET returns:
    {
        "cycles": [
            {
                "start_date": "2024-03-01",
                "end_date": "2024-03-05",
                "cycle_length": 28
            }
        ]
    }
    """

    class Meta:
        model  = CycleHistory
        fields = ['start_date', 'end_date', 'cycle_length']
        extra_kwargs = {
            'cycle_length': {'read_only': True}  # auto calculated, not user input
        }

    def validate(self, data):
        # end_date must be after start_date
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError("end_date must be after start_date")
        return data