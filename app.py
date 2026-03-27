from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timezone
import json

app = Flask(__name__)

# --- Connexion MongoDB ---
client = MongoClient("mongodb://localhost:27017/")
db = client["restaurantDB"]
collection = db["restaurants"]

# -------------------------
# ROUTES PRINCIPALES
# -------------------------

@app.route("/")
def index():
    """Dashboard : stats globales"""
    total = collection.count_documents({})

    # Restaurants par borough
    by_borough = list(collection.aggregate([
        {"$group": {"_id": "$borough", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}
    ]))

    # Top 8 cuisines
    top_cuisines = list(collection.aggregate([
        {"$group": {"_id": "$cuisine", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 8}
    ]))

    # Score moyen par borough
    score_by_borough = list(collection.aggregate([
        {"$unwind": "$grades"},
        {"$group": {
            "_id": "$borough",
            "avg_score": {"$avg": "$grades.score"}
        }},
        {"$sort": {"avg_score": 1}}
    ]))

    return render_template("index.html",
        total=total,
        by_borough=by_borough,
        top_cuisines=top_cuisines,
        score_by_borough=score_by_borough
    )


@app.route("/restaurants")
def restaurants():
    """Liste avec recherche et filtres"""
    search = request.args.get("search", "").strip()
    borough = request.args.get("borough", "")
    cuisine = request.args.get("cuisine", "")
    page = int(request.args.get("page", 1))
    per_page = 20

    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    if borough:
        query["borough"] = borough
    if cuisine:
        query["cuisine"] = cuisine

    total = collection.count_documents(query)
    results = list(collection.find(query)
                   .skip((page - 1) * per_page)
                   .limit(per_page))

    # Convertir ObjectId en string
    for r in results:
        r["_id"] = str(r["_id"])

    boroughs = collection.distinct("borough")
    cuisines = sorted(collection.distinct("cuisine"))
    total_pages = (total + per_page - 1) // per_page

    return render_template("restaurants.html",
        restaurants=results,
        search=search,
        borough=borough,
        cuisine=cuisine,
        boroughs=boroughs,
        cuisines=cuisines,
        page=page,
        total_pages=total_pages,
        total=total
    )


@app.route("/restaurant/<id>")
def detail(id):
    """Détail d'un restaurant"""
    resto = collection.find_one({"_id": ObjectId(id)})
    if not resto:
        return "Restaurant introuvable", 404
    resto["_id"] = str(resto["_id"])
    return render_template("detail.html", resto=resto)


# -------------------------
# CRUD
# -------------------------

@app.route("/add", methods=["GET", "POST"])
def add():
    """Ajouter un restaurant"""
    if request.method == "POST":
        name = request.form.get("name")
        borough = request.form.get("borough")
        cuisine = request.form.get("cuisine")
        street = request.form.get("street")
        building = request.form.get("building")
        zipcode = request.form.get("zipcode")

        doc = {
            "name": name,
            "borough": borough,
            "cuisine": cuisine,
            "address": {
                "street": street,
                "building": building,
                "zipcode": zipcode,
                "coord": []
            },
            "grades": [],
            "restaurant_id": str(collection.count_documents({}) + 90000)
        }
        collection.insert_one(doc)
        return redirect(url_for("restaurants"))

    boroughs = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
    cuisines = sorted(collection.distinct("cuisine"))
    return render_template("add.html", boroughs=boroughs, cuisines=cuisines)


@app.route("/edit/<id>", methods=["GET", "POST"])
def edit(id):
    """Modifier un restaurant"""
    resto = collection.find_one({"_id": ObjectId(id)})
    if not resto:
        return "Restaurant introuvable", 404

    if request.method == "POST":
        collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "name": request.form.get("name"),
                "borough": request.form.get("borough"),
                "cuisine": request.form.get("cuisine"),
                "address.street": request.form.get("street"),
                "address.building": request.form.get("building"),
                "address.zipcode": request.form.get("zipcode"),
            }}
        )
        return redirect(url_for("detail", id=id))

    resto["_id"] = str(resto["_id"])
    boroughs = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
    cuisines = sorted(collection.distinct("cuisine"))
    return render_template("edit.html", resto=resto, boroughs=boroughs, cuisines=cuisines)


@app.route("/delete/<id>", methods=["POST"])
def delete(id):
    """Supprimer un restaurant"""
    collection.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("restaurants"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
