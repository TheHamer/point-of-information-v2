from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetView, PasswordResetDoneView, PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, StdDev, Max, Min

from .forms import CreateUserForm, changeUserDetails, EnterSpeaks, EnterTabURL, PasswordReset, SetPassword, PasswordChange
from .decorators import unauthenticated_user, allowed_users
from .models import Speaks
from .analysis import speaks_analysis
from .best_fit_line import linefit
from .scraper import PersonDataScraper

# Create your views here.

@login_required(login_url='loginpage')
def trakerhome(request):
    speaks_data = Speaks.objects.filter(user=request.user, include=True)
    full_data_list = list(speaks_data.values())

    if speaks_data:
        avg = speaks_data.aggregate(Avg('speaker_score'))
        std = speaks_data.aggregate(StdDev('speaker_score'))
        max = speaks_data.aggregate(Max('speaker_score'))
        min = speaks_data.aggregate(Min('speaker_score'))
        no_entries = speaks_data.count()

        avg_round = round(avg["speaker_score__avg"], 2)
        std_round = round(std["speaker_score__stddev"], 2)
        max_value = max["speaker_score__max"]
        min_value = min["speaker_score__min"]

    else:
        avg_round = None
        std_round = None
        max_value = None
        min_value = None
        no_entries = None

    context = {
        "avg": avg_round,
        "std": std_round,
        "max": max_value,
        "min": min_value,
        "no_entries": no_entries,
        "full_data_list": full_data_list
    }

    return render(request, 'speakstracker/trakerhome.html', context)

@unauthenticated_user
def loginpage(request):

    context = {}

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('trakerhome')
        else:
            messages.info(request, 'Username or Password incorrect')
            return render(request, 'speakstracker/login.html', context)

    return render(request, 'speakstracker/login.html', context)

def logoutpage(request):
    logout(request)
    return redirect('loginpage')

@unauthenticated_user
def register(request):

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('username')
            messages.success(request, f'Account was created for {user}')
            return redirect('loginpage')

    else:
        form = CreateUserForm()

    context = {"form": form}
    return render(request, 'speakstracker/register.html', context)

@login_required(login_url='loginpage')
def update_details(request):

    if request.method == 'POST':
        form = changeUserDetails(data=request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account details have been updated')
    else:
        form = changeUserDetails(instance=request.user)
        
    context = {"form": form}

    return render(request, 'speakstracker/updateuserdetails.html', context)

class PasswordChange(PasswordChangeView):
    template_name = 'speakstracker/password_change_form.html'
    form_class = PasswordChange

class PasswordChangeDone(PasswordChangeDoneView):
    template_name = 'speakstracker/password_change_done.html'

class PasswordReset(PasswordResetView):
    template_name = 'speakstracker/password_reset_form.html'
    form_class = PasswordReset

class PasswordResetDone(PasswordResetDoneView):
    template_name = 'speakstracker/password_reset_done.html'

class PasswordResetConfirm(PasswordResetConfirmView):
    template_name = 'speakstracker/password_reset_confirm.html'
    form_class = SetPassword

class PasswordResetComplete(PasswordResetCompleteView):
    template_name = 'speakstracker/password_reset_complete.html'

@login_required(login_url='loginpage')
def deleteuser(request):

    if request.method == 'POST':
        user = request.user
        user.delete()
        return redirect('loginpage')

@login_required(login_url='loginpage')
def enterspeaks(request):

    if request.method == 'POST' and "tab_url" in request.POST:

        URL_form = EnterTabURL(request.POST)
        form = EnterSpeaks()

        if URL_form.is_valid():
        
            try:
                tab = PersonDataScraper(URL_form.cleaned_data["tab_url"])
                tab_data = tab.get_person(URL_form.cleaned_data["name"])
                comp_date = URL_form.cleaned_data["date"]
                tournament_name = URL_form.cleaned_data["tournament"]                

                total_points = 0
                for round_no in range(1, len(tab_data["speaks"])+1):
                    try:
                        speaks = Speaks()

                        speaks.date = comp_date
                        speaks.tournament = tournament_name
                        speaks.round = round_no
                        speaks.partner = tab_data["partner"]
                        speaks.room_points = total_points
                        speaks.team_position = tab_data["positions"][f"R{round_no}"]["team_position"]
                        speaks.speaker_position = tab_data["positions"][f"R{round_no}"]["speaker_position"]
                        speaks.team_points = tab_data["team_points"][f"R{round_no}"]
                        speaks.speaker_score = tab_data["speaks"][f"R{round_no}"]
                        speaks.motion = tab_data["motions"][f"R{round_no}"]["motion"]
                        speaks.info_slide = tab_data["motions"][f"R{round_no}"]["info_slide"]
                        speaks.save()
                        request.user.speaks.add(speaks)
                                        
                        total_points += tab_data["team_points"][f"R{round_no}"]
                    except:
                        messages.info(request, "Faild to retrieve all rounds", extra_tags='url')

                messages.info(request, f"{tournament_name} added to tracker", extra_tags='url')

            except:
                messages.info(request, "Faild to retrieve data", extra_tags='url')
                   
    elif request.method == 'POST' and "partner" in request.POST:
        form = EnterSpeaks(request.POST)
        URL_form = EnterTabURL()

        if form.is_valid():
            form_instance = form.save()
            request.user.speaks.add(form_instance)
            messages.info(request, "Round added to tracker", extra_tags='round')

        else:
            messages.info(request, "Faild to add round to tracker", extra_tags='round')

    else:
        form = EnterSpeaks()
        URL_form = EnterTabURL()


    
    context = {"form": form, "URL_form": URL_form}
    return render(request, 'speakstracker/enterspeaks.html', context)

@login_required(login_url='loginpage')
def speakstable(request):

    speaks_data = Speaks.objects.filter(user=request.user).values()

    context = {"speaks_data": speaks_data}
    return render(request, 'speakstracker/speakstable.html', context)

@login_required(login_url='loginpage')
def updatespeaks(request, id):

    entry = get_object_or_404(Speaks, id = id)

    if request.user == entry.user:

        if request.method == "POST":
            form = EnterSpeaks(request.POST, instance = entry)

            if form.is_valid():
                form.save()
                return redirect("speakstable")

        else:
            form = EnterSpeaks(instance = entry)

        context = {"form": form}
        
        return render(request, 'speakstracker/updatespeaks.html', context)
    
    else:
        return HttpResponse("<h1>Access denied!</h1>")

@login_required(login_url='loginpage')
def deletespeaks(request, id):

    entry = get_object_or_404(Speaks, id = id)
    if request.user == entry.user:
        if request.method == "POST":
            entry.delete()
            return redirect("speakstable")
        
    else:
        return HttpResponse("<h1>Access denied!</h1>")

    context = {}
    return redirect("speakstable")

@login_required(login_url='loginpage')
def change_include(request, id):

    entry = get_object_or_404(Speaks, id = id)
    if request.user == entry.user:
        if request.method == "POST":
            if entry.include == True:
                entry.include = False
                include_value = False
            else:
                entry.include = True
                include_value = True
        entry.save()

    return JsonResponse({"include": include_value})


@login_required(login_url='loginpage')
def speaksanalysis(request):

    speaks_data = Speaks.objects.filter(user=request.user, include=True)
    full_data_list = list(speaks_data.values())

    if not speaks_data:
        context = {
            "position_speak_avg": None,
            "position_type_avg": None,
            "position_team_avg": None,
            "room_points_avg": None,
            "partner_avg": None,
            "motion_avg": None,
            "speaks_vs_time": None,
            "best_fit": None,
        }

        return render(request, 'speakstracker/speaksanalysis.html', context)

    speaks_calculate = speaks_analysis(speaks_data)

    position_avg, grouped_position_avg = speaks_calculate.speaks_per_position()
    room_points_avg = speaks_calculate.speaks_per_room_points()
    partner_avg = speaks_calculate.speaks_per_partner()
    motion_avg = speaks_calculate.speaks_per_motion_type()

    date_not_null = speaks_data.exclude(date__isnull=True)
    dates = list(date_not_null.values_list('date', flat=True))
    speaks = list(date_not_null.values_list('speaker_score', flat=True))

    if dates:
        speaks_vs_time = []

        for date, speaks in zip(dates, speaks):
            speaks_vs_time.append({"x": date, "y": speaks})
    else:
        speaks_vs_time = None

    context = {
        "position_speak_avg": position_avg,
        "grouped_position_avg": grouped_position_avg,
        "room_points_avg": room_points_avg,
        "partner_avg": partner_avg,
        "motion_avg": motion_avg,
        "speaks_vs_time": speaks_vs_time,
        "full_data_list": full_data_list,
    }

    return render(request, 'speakstracker/speaksanalysis.html', context)

@login_required(login_url='loginpage')
def position_data(request):

        speaks_data = Speaks.objects.filter(user=request.user)
        speaks_calculate = speaks_analysis(speaks_data)
        position_avg = speaks_calculate.speaks_per_position()[0]

        return JsonResponse(position_avg)





