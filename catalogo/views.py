from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Producto
from .forms import ProductoForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
import mercadopago
from django.conf import settings
from .forms import RegistroUsuarioForm
from .decorators import solo_crud_user
from django.http import HttpResponseForbidden

@solo_crud_user
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_productos')
    else:
        form = ProductoForm()
    return render(request, 'catalogo/producto_form.html', {'form': form})

@solo_crud_user
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, request.FILES or None, instance=producto)
    if form.is_valid():
        form.save()
        return redirect('admin_productos')
    return render(request, 'catalogo/producto_form.html', {'form': form})


def solo_cliente(view_func):
    def _wrapped_view(request, *args, **kwargs):
        # Aquí podrías usar un flag o grupo para filtrar compradores
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@solo_crud_user
def admin_productos(request):
    productos = Producto.objects.all()
    return render(request, 'catalogo/admin_productos.html', {'productos': productos})


def vista_catalogo(request):
    productos = Producto.objects.all()
    return render(request, 'catalogo/catalogo.html', {'productos': productos})


@require_POST
def agregar_al_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})
    carrito[str(producto_id)] = carrito.get(str(producto_id), 0) + 1
    request.session['carrito'] = carrito
    return redirect('vista_catalogo')


def ver_carrito(request):
    carrito = request.session.get('carrito', {})
    productos = Producto.objects.filter(id__in=carrito.keys())
    carrito_items = [
        {
            'producto': producto,
            'cantidad': carrito[str(producto.id)],
            'subtotal': producto.precio * carrito[str(producto.id)]
        }
        for producto in productos
    ]
    total = sum(item['subtotal'] for item in carrito_items)
    return render(request, 'catalogo/carrito.html', {'carrito_items': carrito_items, 'total': total})


@login_required
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('vista_catalogo')
    else:
        form = ProductoForm()
    return render(request, 'catalogo/producto_form.html', {'form': form})


@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, request.FILES or None, instance=producto)
    if form.is_valid():
        form.save()
        return redirect('vista_catalogo')
    return render(request, 'catalogo/producto_form.html', {'form': form})


@login_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        return redirect('vista_catalogo')
    return render(request, 'catalogo/confirmar_eliminar.html', {'producto': producto})

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('vista_catalogo')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registro.html', {'form': form})


from .forms import DatosContactoForm

def checkout(request):
    carrito = request.session.get('carrito', {})
    productos = Producto.objects.filter(id__in=carrito.keys())

    carrito_items = [
        {
            'producto': producto,
            'cantidad': carrito[str(producto.id)],
            'subtotal': producto.precio * carrito[str(producto.id)]
        }
        for producto in productos
    ]
    total = sum(item['subtotal'] for item in carrito_items)

    if request.method == 'POST':
        form = DatosContactoForm(request.POST)
        if form.is_valid():
            # Guardar los datos en sesión para pasarlos a MercadoPago
            request.session['datos_contacto'] = form.cleaned_data
            return redirect('procesar_pago')
    else:
        form = DatosContactoForm()

    return render(request, 'catalogo/checkout.html', {
        'carrito_items': carrito_items,
        'total': total,
        'form': form
    })



def procesar_pago(request):
    carrito = request.session.get('carrito', {})
    datos_contacto = request.session.get('datos_contacto', {})
    productos = Producto.objects.filter(id__in=carrito.keys())

    preference_items = []
    for producto in productos:
        cantidad = carrito[str(producto.id)]
        preference_items.append({
            "title": producto.nombre,
            "quantity": cantidad,
            "unit_price": float(producto.precio),
            "currency_id": "CLP"
        })
    
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    preference_data = {
        "items": preference_items,
        "payer": {
            "name": datos_contacto.get("nombre", ""),
            "email": datos_contacto.get("correo", "")
        },
        "back_urls": {
            "success": request.build_absolute_uri('/pago-exitoso/'),
            "failure": request.build_absolute_uri('/pago-error/'),
            "pending": request.build_absolute_uri('/pago-pendiente/')
        }
    }

    request.session['carrito_para_descuento'] = carrito

    preference = sdk.preference().create(preference_data)
    print("📦 PREFERENCE RESPONSE >>>", preference)

    if preference.get("status") != 201 or "init_point" not in preference.get("response", {}):
        return HttpResponse(
            f"<h2>Error al crear preferencia</h2><pre>{preference}</pre>",
            status=500
        )

    return redirect(preference["response"]["init_point"])

def pago_exitoso(request):
    carrito = request.session.get('carrito_para_descuento', {})

    for producto_id, cantidad in carrito.items():
        try:
            producto = Producto.objects.get(id=producto_id)
            producto.stock = max(producto.stock - cantidad, 0)
            producto.save()
        except Producto.DoesNotExist:
            continue

    request.session['carrito'] = {}  # Vaciar carrito visual
    request.session['carrito_para_descuento'] = {}  # Vaciar temporal

    return render(request, 'catalogo/pago_exitoso.html')

def pago_error(request):
    return render(request, 'catalogo/pago_error.html')

def pago_pendiente(request):
    return render(request, 'catalogo/pago_pendiente.html')


def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data['password'])
            usuario.save()
            login(request, usuario)
            return redirect('vista_catalogo')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'registration/registro_usuario.html', {'form': form})
