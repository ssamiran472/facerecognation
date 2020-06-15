from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index_page'),
    path('login/', views.logins, name="login"),
    path('logout/', views.loging_out, name="logout"),
    path('api/register/', views.registering, name="register"),
    path('recognize/', views.recognize, name="recognize"),
    path('secoend-time/login/', views.secoend_time, name="extra_checking"),
    path('api/recognizing/image/', views.recognizing_image, name="recognizing_image"),
    path('export/xls/', views.get_attendance_data, name='export_attendance_xls'),

]