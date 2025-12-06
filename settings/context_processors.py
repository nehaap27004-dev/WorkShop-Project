from .models import GlobalSettings

def global_settings_context(request):
    return {
        "global_settings": GlobalSettings.objects.first()
    }
