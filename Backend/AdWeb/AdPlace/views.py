from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import AdForm
from .services import AdService

# Create your views here.

@login_required
def create_ad(request):
    if request.method == 'POST':
        form = AdForm(request.POST, request.FILES)
        if form.is_valid():
            ad = AdService.create_ad(request.user, form.cleaned_data)
            return redirect('ad_list')
    else:
        form = AdForm()
    return render(request, 'ads/create.html', {'form': form})

@login_required
def ad_list(request):
    ads = AdService.get_ad_list(user=request.user)
    return render(request, 'ads/list.html', {'ads': ads})