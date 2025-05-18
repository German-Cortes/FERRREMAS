from django.urls import path
from . import views

urlpatterns = [
    path('', views.vista_catalogo, name='vista_catalogo'),
    path('agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
path('carrito/', views.ver_carrito, name='ver_carrito'),
path('crear/', views.crear_producto, name='crear_producto'),
path('editar/<int:pk>/', views.editar_producto, name='editar_producto'),
path('eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),

]
