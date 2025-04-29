from django import forms
from .models import Ad
from .services import AdService

class AdForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = ['placement', 'budget', 'daily_limit', 'image', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def clean(self):
        # 自定义验证逻辑
        cleaned_data = super().clean()
        AdService.validate_ad_time_range(
            cleaned_data.get('start_date'), 
            cleaned_data.get('end_date')
        )
        return cleaned_data
        