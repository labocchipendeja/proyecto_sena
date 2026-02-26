from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from .models import producto
from .forms import productoForm




def home(request):
    print('test')
    pecheras = producto.objects.filter(categoria="pechera")
    
    return render(request, "catalog/home.html", {"pecheras" :pecheras, ""  : "correas"})

def product_list(request):
    productos = producto.objects.all()

    if request.method == "POST":
        form = productoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('catalog:product_list')
    else:
        form = productoForm()

    return render(request, "catalog/product_list.html", {"form": form,"productos": productos})

def eliminate_product(request, product_id):
    product = producto.objects.get(id=product_id)
    product.delete()
    return redirect('catalog:product_list')