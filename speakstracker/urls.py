from django.urls import path
from . import views
from .decorators import unauthenticated_user

urlpatterns = [
    path('', views.trakerhome, name='trakerhome'),
    path('login/', views.loginpage, name='loginpage'),
    path('logout/', views.logoutpage, name='logoutpage'),
    path('register/', views.register, name='register'),
    path('updatedetails/', views.update_details, name='updatedetails'),
    path('enterspeaks/', views.enterspeaks, name='enterspeaks'),
    path('speakstable/', views.speakstable, name='speakstable'),
    path('speakstable/<id>/', views.updatespeaks, name='updatespeaks'),
    path('speakstable/deletespeaks/<id>/', views.deletespeaks, name='deletespeaks'),
    path('speaksanalysis/', views.speaksanalysis, name='speaksanalysis'),
    path('speaksanalysis/static/', views.speaksanalysis_static, name='speaksanalysis_static'),
    path('speaksanalysis/dynamic/', views.speaksanalysis_dynamic, name='speaksanalysis_dynamic'),
    path('speaksanalysis/position_data', views.position_data, name='position_data'),
    path('speaksanalysis/filtered/', views.filtered_analysis_data, name='filtered_analysis_data'),
    path('speaksanalysis/heatmap/', views.heatmap_data, name='heatmap_data'),
    path('speakstable/includespeaks/<id>/', views.change_include, name='includespeaks'),
    path('password_change/', views.PasswordChange.as_view(), name='password_change'),
    path('password_change_done/', views.PasswordChangeDone.as_view(), name='password_change_done'),
    path('password_reset/', unauthenticated_user(views.PasswordReset.as_view()), name='password_reset'),
    path('password_reset_done/', unauthenticated_user(views.PasswordResetDone.as_view()), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', unauthenticated_user(views.PasswordResetConfirm.as_view()), name='password_reset_confirm'),
    path('password_reset_complete/', unauthenticated_user(views.PasswordResetComplete.as_view()), name='password_reset_complete'),
    path('delete_user/', views.deleteuser, name='delete_user'),
]