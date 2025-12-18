import math

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from config import supabase

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

CORS(app)  # Enable CORS for all routes


@app.route("/health")
def health_check():
    return jsonify({"status": "ok"})
# devolver todos los productos
@app.route("/allproducts", methods=["GET"])
def get_all_products():
    try:
        response = supabase.table("products").select("*").execute()
        return jsonify({"products": response.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#crear un producto
@app.route("/add", methods=["POST"])
def add_product():
    print("datos recibidos:", request.get_json())

    try:
        datos = request.get_json()
        # Validar datos requeridos
        if not datos or "name" not in datos or "price" not in datos:
            return jsonify(
                {"exito": False, "error": "Faltan campos requeridos: name y price"}
            ), 400

        datos.pop("id", None)
        print("datos a insertar:", datos)
        response = supabase.table("products").insert(datos).execute()

        return jsonify(
            {
                "exito": True,
                "mensaje": "Producto creado exitosamente",
                "datos": response.data,
            }
        ), 200
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500



# busqueda de productos por categoria
@app.route("/products/search", methods=["GET"])
def search_products():
    print("search_products")
    try:
        # Obtener parámetros de consulta
        category = request.args.get("category")
        if category == "Ninguna":
            category = None

        keyword = request.args.get("keyword")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 8))
        min_price = request.args.get("min_price")
        max_price = request.args.get("max_price")

        # Construir consulta base
        print("consultando a supabase con ", category, keyword, page, page_size, min_price, max_price)
        query = supabase.table("products").select("*", count="exact")

        # Filtro por categoría
        if category:
            query = query.ilike("category", f"%{category}%")

        # Filtro por palabra clave (busca en nombre y descripción)
        if keyword:
            # Supabase no tiene OR directo en el query builder, usamos filter
            query = query.or_(f"name.ilike.%{keyword}%,description.ilike.%{keyword}%")

        # Filtro por rango de precios
        if min_price:
            query = query.gte("price", float(min_price))
        if max_price:
            query = query.lte("price", float(max_price))

        # Calcular offset para paginación
        offset = (page - 1) * page_size

        # Ejecutar consulta con paginación
        response = query.range(offset, offset + page_size - 1).execute()

        # Calcular total de páginas
        total_products = (
            response.count if hasattr(response, "count") else len(response.data)
        )
        total_pages = math.ceil(total_products / page_size)

        return jsonify(
            {
                "products": response.data,
                "total_pages": total_pages,
                "current_page": page,
                "total_products": total_products,
            }
        ), 200

    except ValueError:
        return jsonify({"error": "Número de página o tamaño de página inválido"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# obtener detalles de un producto
@app.route("/products/<int:id>", methods=["GET"])
def obtener_producto(id):
    try:
        response = supabase.table("products").select("*").eq("id", id).execute()

        if len(response.data) == 0:
            return jsonify({"exito": False, "error": "Producto no encontrado"}), 404

        return jsonify({"exito": True, "datos": response.data[0]}), 200
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500


@app.route("/products", methods=["POST"])
def crear_producto():
    try:
        datos = request.get_json()

        # Validar datos requeridos
        if not datos or "nombre" not in datos or "precio" not in datos:
            return jsonify(
                {"exito": False, "error": "Faltan campos requeridos: nombre y precio"}
            ), 400

        response = supabase.table("products").insert(datos).execute()

        return jsonify(
            {
                "exito": True,
                "mensaje": "Producto creado exitosamente",
                "datos": response.data,
            }
        ), 201
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500


@app.route("/edit/<int:id>", methods=["PUT"])
def actualizar_producto(id):
    try:
        datos = request.get_json()
        datos.pop("id", None)
        if not datos:
            return jsonify(
                {"exito": False, "error": "No se enviaron datos para actualizar"}
            ), 400

        response = supabase.table("products").update(datos).eq("id", id).execute()

        if len(response.data) == 0:
            return jsonify({"exito": False, "error": "Producto no encontrado"}), 404

        return jsonify(
            {
                "exito": True,
                "mensaje": "Producto actualizado exitosamente",
                "datos": response.data,
            }
        ), 200
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500


@app.route("/delete/<int:id>", methods=["DELETE"])
def eliminar_producto(id):
    print("eliminar_producto:", id)
    try:
        response = supabase.table("products").delete().eq("id", id).execute()

        return jsonify(
            {"exito": True, "mensaje": "Producto eliminado exitosamente"}
        ), 200
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500


@app.route("/reduce-stock", methods=["POST"])
def reduce_stock():
    """
    Payload:
    {
      "items": [
        { "product_id": int, "quantity": int }
      ]
    }
    """
    data = request.get_json()
    items = data.get("items") if data else None

    if not items:
        return jsonify({"error": "Items are required"}), 400

    try:
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity")

            if not product_id or not quantity or quantity <= 0:
                return jsonify({"error": "Invalid item format"}), 400

            # Obtener producto
            response = (
                supabase
                .table("products")
                .select("id, stock")
                .eq("id", product_id)
                .execute()
            )

            if not response.data:
                return jsonify({"error": f"Product {product_id} not found"}), 404

            current_stock = response.data[0]["stock"]

            if current_stock < quantity:
                return jsonify({
                    "error": f"Insufficient stock for product {product_id}"
                }), 409

            # Reducir stock
            supabase.table("products").update({
                "stock": current_stock - quantity
            }).eq("id", product_id).execute()

        return jsonify({
            "message": "Stock reduced successfully"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/restore-stock", methods=["POST"])
def restore_stock():
    """
    Payload:
    {
      "items": [
        { "product_id": int, "quantity": int }
      ]
    }
    """
    data = request.get_json()
    items = data.get("items") if data else None

    if not items:
        return jsonify({"error": "Items are required"}), 400

    try:
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity")

            if not product_id or not quantity or quantity <= 0:
                return jsonify({"error": "Invalid item format"}), 400

            # Obtener stock actual
            response = (
                supabase
                .table("products")
                .select("stock")
                .eq("id", product_id)
                .execute()
            )

            if not response.data:
                continue  # No rompemos compensación por un producto inexistente

            current_stock = response.data[0]["stock"]

            # Restaurar stock
            supabase.table("products").update({
                "stock": current_stock + quantity
            }).eq("id", product_id).execute()

        return jsonify({
            "message": "Stock restored successfully"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
