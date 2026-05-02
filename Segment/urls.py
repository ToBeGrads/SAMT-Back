from django.urls import path
from . import views

urlpatterns = [
    path('', views.SAM),
    path('structures', views.Get_Structures,name='structures'),
    path('MRI_List_For_Segment', views.MRI_List_For_Segment), 
    path("save_mask", views.save_mask), 
    path("Update_mask", views.Update_mask),
    path("mystructures", views.myStructures),
    path("Addstructure", views.AddStructure),
    path("UpdateCoordinates", views.Update_Coordinates),
    path('AddCoordinates', views.Add_Coordinates), 
    path("Load_mask", views.Load_mask), 
    path("UploadMris", views.UploadMRIs)
]
