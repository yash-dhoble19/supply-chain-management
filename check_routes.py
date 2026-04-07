from api.routes import products
from main import app

print("Products router imported successfully")
print("Products router prefix:", products.router.prefix)
print()
print("All app routes with 'products':")
for r in app.routes:
    if 'products' in r.path:
        print(f"  {r.path} - Methods: {r.methods}")
