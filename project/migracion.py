# migracion_final.py
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.apps import apps
from django.core.management import call_command
from django.db import connections
from django.contrib.contenttypes.models import ContentType

print("="*60)
print("INICIANDO MIGRACIÓN DE SQLITE A MYSQL")
print("="*60)

# 1. Verificar conexiones
print("\n🔍 Verificando conexiones...")
try:
    # Probar SQLite
    with connections['sqlite'].cursor() as cursor:
        cursor.execute("SELECT sqlite_version();")
        version_sqlite = cursor.fetchone()[0]
        print(f"✅ SQLite conectado (versión {version_sqlite})")
except Exception as e:
    print(f"❌ Error con SQLite: {e}")
    print("Verifica que la ruta de tu BD SQLite sea correcta en settings.py")
    sys.exit(1)

try:
    # Probar MySQL
    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT VERSION();")
        version_mysql = cursor.fetchone()[0]
        print(f"✅ MySQL conectado (versión {version_mysql})")
except Exception as e:
    print(f"❌ Error con MySQL: {e}")
    print("Verifica usuario, contraseña y nombre de BD")
    sys.exit(1)

# 2. Limpiar MySQL
print("\n🗑️  Limpiando MySQL...")
try:
    call_command('flush', interactive=False, database='default', verbosity=0)
    print("✅ MySQL limpiado")
except Exception as e:
    print(f"ℹ️  MySQL ya estaba limpio o error: {e}")

# 3. Definir el orden correcto de migración
# Las tablas deben crearse en este orden para respetar las claves foráneas
orden_modelos = [
    # Primero: Modelos base (sin dependencias)
    'users.CustomUser',  # Modelo de usuario personalizado
    'auth.Group',
    'auth.Permission',
    
    # Segundo: Modelos que dependen de usuarios
    'users.UserSession',
    'authtoken.Token',
    'sessions.Session',
    
    # Tercero: Tus modelos de aplicación (ajusta según tu proyecto)
    # Agrega aquí tus modelos en orden de dependencia
    # Ejemplo:
    # 'mi_app.Perfil',
    # 'mi_app.Producto',
    # 'mi_app.Pedido',
]

# Obtener todos los modelos de Django
todos_los_modelos = list(apps.get_models())

# Separar modelos por app
modelos_por_app = {}
for model in todos_los_modelos:
    clave = f"{model._meta.app_label}.{model.__name__}"
    if clave not in orden_modelos:
        modelos_por_app[model._meta.app_label] = modelos_por_app.get(model._meta.app_label, []) + [model]

print("\n📦 Iniciando migración de datos...")

# Contadores
total_registros = 0
errores = []

# Primero migrar en el orden definido
for nombre_modelo in orden_modelos:
    try:
        app_label, model_name = nombre_modelo.split('.')
        model = apps.get_model(app_label, model_name)
        
        datos = list(model.objects.using('sqlite').all())
        cantidad = len(datos)
        
        if cantidad > 0:
            print(f"📋 Migrando {nombre_modelo} ({cantidad} registros)...")
            for obj in datos:
                try:
                    obj.save(using='default')
                except Exception as e:
                    errores.append(f"{nombre_modelo} - ID {obj.pk}: {str(e)[:100]}")
            total_registros += cantidad
            print(f"   ✅ Completado")
        else:
            print(f"📋 {nombre_modelo}: sin datos")
            
    except Exception as e:
        errores.append(f"Error en {nombre_modelo}: {str(e)[:100]}")
        print(f"   ⚠️  {e}")

# Luego migrar el resto por app
print("\n📦 Migrando resto de aplicaciones...")
for app_name, modelos in modelos_por_app.items():
    print(f"\n📁 Aplicación: {app_name}")
    for model in modelos:
        clave = f"{app_name}.{model.__name__}"
        if clave in orden_modelos:
            continue
            
        try:
            datos = list(model.objects.using('sqlite').all())
            cantidad = len(datos)
            
            if cantidad > 0:
                print(f"   📋 {model.__name__}: {cantidad} registros...", end=" ")
                for obj in datos:
                    try:
                        obj.save(using='default')
                    except Exception as e:
                        errores.append(f"{clave} - ID {obj.pk}: {str(e)[:50]}")
                        break
                else:
                    print("✅")
                    total_registros += cantidad
            else:
                print(f"   📋 {model.__name__}: sin datos")
                
        except Exception as e:
            errores.append(f"Error en {clave}: {str(e)[:100]}")
            print(f"   ❌ Error: {str(e)[:100]}")

# 4. Resumen final
print("\n" + "="*60)
print("RESUMEN DE MIGRACIÓN")
print("="*60)
print(f"✅ Total registros migrados: {total_registros}")
print(f"⚠️  Total errores: {len(errores)}")

if errores:
    print("\n🔧 Errores detectados (primeros 10):")
    for error in errores[:10]:
        print(f"   - {error}")

print("\n🎉 ¡Proceso completado!")