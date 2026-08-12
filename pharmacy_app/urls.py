from rest_framework.routers import DefaultRouter

from pharmacy_app.views import MedicineViewSet, PrescribedItemViewSet

app_name = "pharmacy_app"

router = DefaultRouter()
router.register("medicines", MedicineViewSet, basename="medicine")
router.register("prescribed-items", PrescribedItemViewSet, basename="prescribed-item")

urlpatterns = router.urls
