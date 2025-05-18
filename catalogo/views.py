from django.urls import path
from . import views
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Producto
from .forms import ProductoForm


urlpatterns = [
    path('', views.vista_catalogo, name='vista_catalogo'),
]

@require_POST
def agregar_al_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})
    carrito[producto_id] = carrito.get(producto_id, 0) + 1
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