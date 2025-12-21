import json

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
from .services import TabbycatService
from .services.tabbycat_service import extract_tournament_slug_from_url, extract_base_url

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

def _fetch_data_from_api(url: str, name: str) -> dict:
    """Fetch tournament data using the Tabbycat API (public tabs only)."""
    base_url = extract_base_url(url)
    tournament_slug = extract_tournament_slug_from_url(url)
    
    if not tournament_slug:
        raise ValueError("Could not extract tournament slug from URL")
    
    service = TabbycatService(base_url)
    return service.get_person_data(tournament_slug, name)


def _fetch_data_from_scraper(url: str, name: str) -> dict:
    """Fetch tournament data using the legacy web scraper."""
    scraper = PersonDataScraper(url)
    return scraper.get_person(name)


def _save_tournament_data(request, tab_data: dict, comp_date, tournament_name: str) -> int:
    """
    Save tournament data to the database.
    
    Returns:
        Number of rounds successfully saved.
    """
    total_points = 0
    rounds_saved = 0
    
    for round_no in range(1, len(tab_data["speaks"]) + 1):
        round_key = f"R{round_no}"
        
        try:
            speaks = Speaks()
            speaks.date = comp_date
            speaks.tournament = tournament_name
            speaks.round = round_no
            speaks.partner = tab_data.get("partner")
            speaks.room_points = total_points
            
            # Position data
            if round_key in tab_data.get("positions", {}):
                speaks.team_position = tab_data["positions"][round_key].get("team_position")
                speaks.speaker_position = tab_data["positions"][round_key].get("speaker_position")
            
            # Team points
            if round_key in tab_data.get("team_points", {}):
                speaks.team_points = tab_data["team_points"][round_key]
            
            # Speaker score
            if round_key in tab_data.get("speaks", {}):
                speaks.speaker_score = tab_data["speaks"][round_key]
            
            # Motion data
            if round_key in tab_data.get("motions", {}):
                speaks.motion = tab_data["motions"][round_key].get("motion")
                speaks.info_slide = tab_data["motions"][round_key].get("info_slide")
            
            # Opponent positions (if available) - serialize to JSON
            if round_key in tab_data.get("opponent_positions", {}):
                opponent_pos = tab_data["opponent_positions"][round_key]
                if opponent_pos:
                    speaks.opponent_positions = json.dumps(opponent_pos)
            
            speaks.save()
            request.user.speaks.add(speaks)
            
            # Update cumulative points
            if speaks.team_points:
                total_points += speaks.team_points
            
            rounds_saved += 1
            
        except Exception as e:
            # Log the error but continue with other rounds
            print(f"Error saving round {round_no}: {e}")
            continue
    
    return rounds_saved


@login_required(login_url='loginpage')
def enterspeaks(request):

    if request.method == 'POST' and "tab_url" in request.POST:

        URL_form = EnterTabURL(request.POST)
        form = EnterSpeaks()

        if URL_form.is_valid():
            tab_url = URL_form.cleaned_data["tab_url"]
            speaker_name = URL_form.cleaned_data["name"]
            comp_date = URL_form.cleaned_data["date"]
            tournament_name = URL_form.cleaned_data["tournament"]
            data_source = URL_form.cleaned_data.get("data_source", "api")
            
            try:
                # Fetch data using selected method
                if data_source == "api":
                    try:
                        tab_data = _fetch_data_from_api(tab_url, speaker_name)
                    except Exception as api_error:
                        # Fall back to scraper if API fails
                        messages.warning(
                            request, 
                            f"API failed ({api_error}), falling back to web scraping...", 
                            extra_tags='url'
                        )
                        tab_data = _fetch_data_from_scraper(tab_url, speaker_name)
                else:
                    tab_data = _fetch_data_from_scraper(tab_url, speaker_name)
                
                # Save the data
                rounds_saved = _save_tournament_data(request, tab_data, comp_date, tournament_name)
                
                if rounds_saved > 0:
                    messages.success(
                        request, 
                        f"{tournament_name} added to tracker ({rounds_saved} rounds)", 
                        extra_tags='url'
                    )
                else:
                    messages.warning(
                        request, 
                        f"No rounds could be saved for {tournament_name}", 
                        extra_tags='url'
                    )

            except ValueError as ve:
                messages.error(request, f"Invalid data: {ve}", extra_tags='url')
            except Exception as e:
                messages.error(request, f"Failed to retrieve data: {e}", extra_tags='url')
                   
    elif request.method == 'POST' and "partner" in request.POST:
        form = EnterSpeaks(request.POST)
        URL_form = EnterTabURL()

        if form.is_valid():
            form_instance = form.save()
            request.user.speaks.add(form_instance)
            messages.success(request, "Round added to tracker", extra_tags='round')

        else:
            messages.error(request, "Failed to add round to tracker", extra_tags='round')

    else:
        form = EnterSpeaks()
        URL_form = EnterTabURL()

    
    context = {"form": form, "URL_form": URL_form}
    return render(request, 'speakstracker/enterspeaks.html', context)

@login_required(login_url='loginpage')
def speakstable(request):

    speaks_queryset = Speaks.objects.filter(user=request.user)
    speaks_data = []
    
    for speaks in speaks_queryset:
        speaks_dict = {
            'id': speaks.id,
            'user_id': speaks.user_id,
            'date': speaks.date,
            'tournament': speaks.tournament,
            'partner': speaks.partner,
            'round': speaks.round,
            'room_points': speaks.room_points,
            'team_position': speaks.team_position,
            'speaker_position': speaks.speaker_position,
            'motion_type': speaks.motion_type,
            'team_points': speaks.team_points,
            'speaker_score': speaks.speaker_score,
            'motion': speaks.motion,
            'info_slide': speaks.info_slide,
            'include': speaks.include,
            'opponent_positions': speaks.opponent_positions,
            'call': speaks.get_call(),
        }
        speaks_data.append(speaks_dict)

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
    """Legacy analysis page - redirects to static for backwards compatibility."""
    return redirect('speaksanalysis_static')

@login_required(login_url='loginpage')
def speaksanalysis_static(request):
    """Static analysis page with Speaker Position and below sections."""
    speaks_data = Speaks.objects.filter(user=request.user, include=True)
    full_data_list = list(speaks_data.values())

    if not speaks_data:
        context = {
            "position_speak_avg": None,
            "position_type_avg": None,
            "position_team_avg": None,
            "room_points_avg": None,
        "avg_points_data": None,
        "avg_points_team_data": None,
        "avg_points_best_fit": None,
            "partner_avg": None,
            "motion_avg": None,
            "speaks_vs_time": None,
            "best_fit": None,
            "filter_options": None,
            "heatmap_data": None,
        }

        return render(request, 'speakstracker/speaksanalysis.html', context)

    speaks_calculate = speaks_analysis(speaks_data)

    position_avg, grouped_position_avg = speaks_calculate.speaks_per_position()
    room_points_avg = speaks_calculate.speaks_per_room_points()
    partner_avg = speaks_calculate.speaks_per_partner()
    motion_avg = speaks_calculate.speaks_per_motion_type()
    
    # New: Average points data
    avg_points_speaker, avg_points_team, avg_points_best_fit = speaks_calculate.get_average_points_chart_data()
    
    # New: Filter options
    filter_options = speaks_calculate.get_filter_options()
    
    # New: Heatmap data
    heatmap_data = speaks_calculate.positional_win_rate_heatmap()

    date_not_null = speaks_data.exclude(date__isnull=True)
    dates = list(date_not_null.values_list('date', flat=True))
    speaks_scores = list(date_not_null.values_list('speaker_score', flat=True))

    if dates:
        speaks_vs_time = []

        for date, score in zip(dates, speaks_scores):
            speaks_vs_time.append({"x": date, "y": score})
    else:
        speaks_vs_time = None

    context = {
        "position_speak_avg": position_avg,
        "grouped_position_avg": grouped_position_avg,
        "room_points_avg": room_points_avg,
        "avg_points_data": avg_points_speaker,
        "avg_points_team_data": avg_points_team,
        "avg_points_best_fit": avg_points_best_fit,
        "partner_avg": partner_avg,
        "motion_avg": motion_avg,
        "speaks_vs_time": speaks_vs_time,
        "full_data_list": full_data_list,
        "filter_options": filter_options,
        "heatmap_data": heatmap_data,
    }
    return render(request, 'speakstracker/speaksanalysis_static.html', context)

@login_required(login_url='loginpage')
def speaksanalysis_dynamic(request):
    """Dynamic analysis page with filters, heatmap, average points, and speaks vs time."""
    speaks_data = Speaks.objects.filter(user=request.user, include=True)
    full_data_list = list(speaks_data.values())

    if not speaks_data:
        context = {
            "avg_points_data": None,
            "avg_points_team_data": None,
            "avg_points_best_fit": None,
            "speaks_vs_time": None,
            "filter_options": None,
            "heatmap_data": None,
            "full_data_list": full_data_list,
        }
        return render(request, 'speakstracker/speaksanalysis_dynamic.html', context)

    speaks_calculate = speaks_analysis(speaks_data)
    
    # Average points data
    avg_points_speaker, avg_points_team, avg_points_best_fit = speaks_calculate.get_average_points_chart_data()
    
    # Filter options
    filter_options = speaks_calculate.get_filter_options()
    
    # Heatmap data
    heatmap_data = speaks_calculate.positional_win_rate_heatmap()

    # Speaks vs time
    date_not_null = speaks_data.exclude(date__isnull=True)
    dates = list(date_not_null.values_list('date', flat=True))
    speaks_scores = list(date_not_null.values_list('speaker_score', flat=True))

    if dates:
        speaks_vs_time = []
        for date, score in zip(dates, speaks_scores):
            speaks_vs_time.append({"x": date, "y": score})
    else:
        speaks_vs_time = None

    context = {
        "avg_points_data": avg_points_speaker,
        "avg_points_team_data": avg_points_team,
        "avg_points_best_fit": avg_points_best_fit,
        "speaks_vs_time": speaks_vs_time,
        "full_data_list": full_data_list,
        "filter_options": filter_options,
        "heatmap_data": heatmap_data,
    }

    return render(request, 'speakstracker/speaksanalysis_dynamic.html', context)

@login_required(login_url='loginpage')
def position_data(request):

        speaks_data = Speaks.objects.filter(user=request.user)
        speaks_calculate = speaks_analysis(speaks_data)
        position_avg = speaks_calculate.speaks_per_position()[0]

        return JsonResponse(position_avg)


@login_required(login_url='loginpage')
def filtered_analysis_data(request):
    """
    AJAX endpoint for filtered analysis data.
    
    Accepts filter parameters via GET/POST and returns filtered chart data.
    
    Filter Parameters:
        - team_positions: comma-separated list (e.g., "OG,OO")
        - speaker_positions: comma-separated list (e.g., "PM,DPM")
        - partners: comma-separated list
        - avg_points_min: float (0-3)
        - avg_points_max: float (0-3)
        - date_start: YYYY-MM-DD
        - date_end: YYYY-MM-DD
        - primary_position: for heatmap (OG, OO, CG, CO)
    """
    from datetime import datetime
    
    # Get base queryset
    speaks_data = Speaks.objects.filter(user=request.user, include=True)
    
    if not speaks_data.exists():
        return JsonResponse({
            "error": "No data available",
            "filtered_data": [],
            "analysis": None
        })
    
    # Parse filter parameters
    params = request.GET if request.method == 'GET' else request.POST
    
    # Team position filter
    team_positions = params.get('team_positions', '')
    if team_positions:
        positions = [p.strip() for p in team_positions.split(',') if p.strip()]
        if positions:
            speaks_data = speaks_data.filter(team_position__in=positions)
    
    # Speaker position filter
    speaker_positions = params.get('speaker_positions', '')
    if speaker_positions:
        positions = [p.strip() for p in speaker_positions.split(',') if p.strip()]
        if positions:
            speaks_data = speaks_data.filter(speaker_position__in=positions)
    
    # Partner filter
    partners = params.get('partners', '')
    if partners:
        partner_list = [p.strip() for p in partners.split(',') if p.strip()]
        if partner_list:
            speaks_data = speaks_data.filter(partner__in=partner_list)
    
    # Date range filter
    date_start = params.get('date_start', '')
    date_end = params.get('date_end', '')
    
    if date_start:
        try:
            start_date = datetime.strptime(date_start, '%Y-%m-%d').date()
            speaks_data = speaks_data.filter(date__gte=start_date)
        except ValueError:
            pass
    
    if date_end:
        try:
            end_date = datetime.strptime(date_end, '%Y-%m-%d').date()
            speaks_data = speaks_data.filter(date__lte=end_date)
        except ValueError:
            pass
    
    # Average points filter (applied in Python since it's a computed field)
    avg_points_min = params.get('avg_points_min', '')
    avg_points_max = params.get('avg_points_max', '')
    
    filtered_data = list(speaks_data.values())
    
    # Apply average points filter
    if avg_points_min or avg_points_max:
        min_val = float(avg_points_min) if avg_points_min else 0
        max_val = float(avg_points_max) if avg_points_max else 3
        
        def calc_avg_points(entry):
            round_num = entry.get('round') or 0
            room_points = entry.get('room_points') or 0
            team_points = entry.get('team_points') or 0
            if round_num == 0:
                return 1.5
            # room_points is cumulative BEFORE current round, so add current round's points
            cumulative_points = room_points + team_points
            return cumulative_points / round_num
        
        filtered_data = [
            entry for entry in filtered_data 
            if min_val <= calc_avg_points(entry) <= max_val
        ]
    
    # Run analysis on filtered data
    if not filtered_data:
        return JsonResponse({
            "filtered_data": [],
            "count": 0,
            "analysis": None
        })
    
    # Convert filtered data back to queryset for analysis
    filtered_ids = [entry['id'] for entry in filtered_data]
    filtered_qs = Speaks.objects.filter(id__in=filtered_ids)
    
    speaks_calculate = speaks_analysis(filtered_qs)
    
    # Get analysis results
    position_avg, grouped_position_avg = speaks_calculate.speaks_per_position()
    room_points_avg = speaks_calculate.speaks_per_room_points()
    partner_avg = speaks_calculate.speaks_per_partner()
    motion_avg = speaks_calculate.speaks_per_motion_type()
    avg_points_speaker, avg_points_team, avg_points_best_fit = speaks_calculate.get_average_points_chart_data()
    
    # Heatmap for specific position
    primary_position = params.get('primary_position', '')
    heatmap_data = None
    if primary_position in ['OG', 'OO', 'CG', 'CO']:
        heatmap_data = speaks_calculate.get_heatmap_data_for_position(primary_position)
    else:
        heatmap_data = speaks_calculate.positional_win_rate_heatmap()
    
    # Speaks vs time
    speaks_vs_time = []
    for entry in filtered_data:
        if entry.get('date') and entry.get('speaker_score'):
            speaks_vs_time.append({
                "x": entry['date'].isoformat() if hasattr(entry['date'], 'isoformat') else str(entry['date']),
                "y": entry['speaker_score']
            })
    
    return JsonResponse({
        "filtered_data": filtered_data,
        "count": len(filtered_data),
        "analysis": {
            "position_avg": position_avg,
            "grouped_position_avg": grouped_position_avg,
            "room_points_avg": room_points_avg,
            "avg_points_speaker": avg_points_speaker,
            "avg_points_team": avg_points_team,
            "avg_points_best_fit": avg_points_best_fit,
            "partner_avg": partner_avg,
            "motion_avg": motion_avg,
            "heatmap": heatmap_data,
            "speaks_vs_time": speaks_vs_time,
        }
    })


@login_required(login_url='loginpage')
def heatmap_data(request):
    """
    AJAX endpoint for positional win-rate heatmap data.
    
    Parameters:
        - primary_position: The selected position (OG, OO, CG, CO)
    """
    speaks_data = Speaks.objects.filter(user=request.user, include=True)
    
    if not speaks_data.exists():
        return JsonResponse({"error": "No data available"})
    
    speaks_calculate = speaks_analysis(speaks_data)
    
    params = request.GET if request.method == 'GET' else request.POST
    primary_position = params.get('primary_position', '')
    
    if primary_position in ['OG', 'OO', 'CG', 'CO']:
        data = speaks_calculate.get_heatmap_data_for_position(primary_position)
    else:
        data = speaks_calculate.positional_win_rate_heatmap()
    
    return JsonResponse({
        "primary_position": primary_position or None,
        "heatmap": data
    })

