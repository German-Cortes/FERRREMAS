def grupo_usuario(request):
    grupos = []
    if request.user.is_authenticated:
        grupos = list(request.user.groups.values_list('name', flat=True))
    return {'grupos_usuario': grupos}
