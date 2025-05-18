from django.shortcuts import redirect
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test

def es_crud_user(user):
    return user.is_authenticated and user.groups.filter(name='crud_productos').exists()

solo_crud_user = user_passes_test(es_crud_user, login_url='login')

def solo_crud_user(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        # Aquí puedes personalizar si en el futuro usas grupos o campos de perfil
        return view_func(request, *args, **kwargs)
    return _wrapped_view
