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


# crear producto falta verificar que sea admin
@app.route("/productos", methods=["POST"])
def crear_producto():
    try:
        datos = request.get_json()

        # Validar datos requeridos
        if not datos or "nombre" not in datos or "precio" not in datos:
            return jsonify(
                {"exito": False, "error": "Faltan campos requeridos: nombre y precio"}
            ), 400

        response = supabase.table("productos").insert(datos).execute()

        return jsonify(
            {
                "exito": True,
                "mensaje": "Producto creado exitosamente",
                "datos": response.data,
            }
        ), 201
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500


@app.route("/productos/<int:id>", methods=["PUT"])
def actualizar_producto(id):
    try:
        datos = request.get_json()

        if not datos:
            return jsonify(
                {"exito": False, "error": "No se enviaron datos para actualizar"}
            ), 400

        response = supabase.table("productos").update(datos).eq("id", id).execute()

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


@app.route("/productos/<int:id>", methods=["DELETE"])
def eliminar_producto(id):
    try:
        response = supabase.table("productos").delete().eq("id", id).execute()

        return jsonify(
            {"exito": True, "mensaje": "Producto eliminado exitosamente"}
        ), 200
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
