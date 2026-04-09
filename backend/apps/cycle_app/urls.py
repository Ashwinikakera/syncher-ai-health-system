from django.urls import path
from apps.cycle_app.views import (
    CycleStartView,
    CycleEndView,
    CycleListView,
    PredictionFeedbackView
)

urlpatterns = [
<<<<<<< HEAD
    path('cycle', CycleView.as_view(), name='cycle'),
=======
    path('cycle/start/',           CycleStartView.as_view(),          name='cycle-start'),
    path('cycle/end/',             CycleEndView.as_view(),            name='cycle-end'),
    path('cycle/',                 CycleListView.as_view(),           name='cycle-list'),
    path('prediction-feedback/',   PredictionFeedbackView.as_view(),  name='prediction-feedback'),
>>>>>>> d98ae17 (dev 1 editing done)
]